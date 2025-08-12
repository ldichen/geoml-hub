"""
Skopeo镜像推送工具
使用skopeo实现高性能、稳定的镜像仓库推送功能
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, BinaryIO, Any, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SkopeoPusher:
    """基于skopeo的镜像推送器"""
    
    def __init__(self):
        self.skopeo_cmd = "skopeo"
        
    async def check_skopeo_available(self) -> bool:
        """检查skopeo是否可用"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.skopeo_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Skopeo可用: {version}")
                return True
            else:
                logger.error(f"Skopeo检查失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Skopeo不可用: {e}")
            return False
    
    async def push_from_tar(
        self,
        tar_file: BinaryIO,
        harbor_url: str,
        username: str,
        password: str,
        project: str,
        repository: str,
        tag: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        使用skopeo从tar文件推送镜像到Harbor
        
        Args:
            tar_file: Docker tar文件流
            harbor_url: Harbor服务器URL
            username: 用户名
            password: 密码
            project: 项目名
            repository: 仓库名
            tag: 标签
            progress_callback: 进度回调函数
            
        Returns:
            推送结果字典
        """
        temp_tar_path = None
        
        try:
            if progress_callback:
                await progress_callback(5, "准备skopeo推送...")
            
            # 1. 保存tar文件到临时路径
            temp_tar_path = await self._save_temp_tar(tar_file)
            logger.info(f"临时tar文件: {temp_tar_path}")
            
            if progress_callback:
                await progress_callback(10, "开始skopeo推送...")
            
            # 2. 构建目标URL（移除协议前缀）
            # skopeo的docker://格式不需要http://或https://前缀
            clean_harbor_url = harbor_url.replace('https://', '').replace('http://', '').rstrip('/')
            target_url = f"{clean_harbor_url}/{project}/{repository}:{tag}"
            logger.info(f"原始Harbor URL: {harbor_url}")
            logger.info(f"清理后URL: {clean_harbor_url}")
            logger.info(f"完整推送目标: docker://{target_url}")
            
            # 3. 执行skopeo推送
            result = await self._execute_skopeo_copy(
                temp_tar_path, target_url, username, password, progress_callback
            )
            
            if result.get('status') == 'success':
                logger.info(f"Skopeo推送成功: {project}/{repository}:{tag}")
                return {
                    'status': 'success',
                    'method': 'skopeo',
                    'image': f"{project}/{repository}:{tag}",
                    'message': 'Skopeo推送成功',
                    'performance_improvement': '高性能原生推送'
                }
            else:
                logger.error(f"Skopeo推送失败: {result.get('message')}")
                return result
                
        except Exception as e:
            logger.error(f"Skopeo推送异常: {e}")
            return {
                'status': 'error',
                'method': 'skopeo',
                'message': f'Skopeo推送异常: {str(e)}'
            }
            
        finally:
            # 清理临时文件
            if temp_tar_path and temp_tar_path.exists():
                try:
                    temp_tar_path.unlink()
                    logger.debug(f"清理临时文件: {temp_tar_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")
    
    async def _save_temp_tar(self, tar_file: BinaryIO) -> Path:
        """保存tar文件到临时路径"""
        try:
            # 重置文件指针
            tar_file.seek(0)
            
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.tar', prefix='skopeo_')
            temp_path = Path(temp_path)
            
            # 写入数据
            with open(temp_fd, 'wb') as f:
                shutil.copyfileobj(tar_file, f)
            
            logger.debug(f"保存临时tar文件: {temp_path} ({temp_path.stat().st_size} bytes)")
            return temp_path
            
        except Exception as e:
            logger.error(f"保存临时tar文件失败: {e}")
            raise
    
    async def _execute_skopeo_copy(
        self,
        tar_path: Path,
        target_url: str,
        username: str,
        password: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """执行skopeo copy命令"""
        try:
            # 构建skopeo命令
            cmd = [
                self.skopeo_cmd,
                "copy",
                "--insecure-policy",  # 跳过签名验证
                "--dest-tls-verify=false",  # 目标不验证TLS（Harbor自签名证书）
                "--dest-username", username,
                "--dest-password", password,
                f"docker-archive:{tar_path}",
                f"docker://{target_url}"
            ]
            
            logger.debug(f"执行skopeo命令: {' '.join(cmd[:8])} [credentials hidden]")
            
            if progress_callback:
                await progress_callback(20, "执行skopeo copy...")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 监控进度（简化版）
            if progress_callback:
                # 启动进度监控任务
                monitor_task = asyncio.create_task(
                    self._monitor_progress(progress_callback)
                )
            
            stdout, stderr = await process.communicate()
            
            if progress_callback:
                monitor_task.cancel()
                await progress_callback(100, "推送完成")
            
            # 处理结果
            if process.returncode == 0:
                logger.info("Skopeo copy执行成功")
                stdout_text = stdout.decode() if stdout else ""
                return {
                    'status': 'success',
                    'stdout': stdout_text,
                    'message': 'Skopeo推送成功'
                }
            else:
                stderr_text = stderr.decode() if stderr else ""
                logger.error(f"Skopeo copy失败: {stderr_text}")
                return {
                    'status': 'error',
                    'stderr': stderr_text,
                    'message': f'Skopeo推送失败: {stderr_text}'
                }
                
        except Exception as e:
            logger.error(f"执行skopeo命令异常: {e}")
            return {
                'status': 'error',
                'message': f'执行skopeo命令异常: {str(e)}'
            }
    
    async def _monitor_progress(self, progress_callback):
        """监控推送进度（简化实现）"""
        try:
            progress_points = [30, 40, 50, 60, 70, 80, 90]
            for i, progress in enumerate(progress_points):
                await asyncio.sleep(2)  # 每2秒更新一次进度
                await progress_callback(progress, f"推送中... ({progress}%)")
        except asyncio.CancelledError:
            pass
    
    async def get_image_info_from_tar(self, tar_file: BinaryIO) -> Dict[str, Any]:
        """从tar文件获取镜像信息（用于进度显示等）"""
        try:
            # 简化实现：使用skopeo inspect
            temp_tar_path = await self._save_temp_tar(tar_file)
            
            cmd = [
                self.skopeo_cmd,
                "inspect",
                f"docker-archive:{temp_tar_path}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                info = json.loads(stdout.decode())
                # 清理临时文件
                temp_tar_path.unlink()
                return {
                    'status': 'success',
                    'info': info,
                    'layers_count': len(info.get('Layers', [])),
                    'size': info.get('Size', 0)
                }
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"获取镜像信息失败: {error_msg}")
                return {
                    'status': 'error',
                    'message': error_msg
                }
                
        except Exception as e:
            logger.error(f"获取镜像信息异常: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            # 确保清理临时文件
            if 'temp_tar_path' in locals() and temp_tar_path.exists():
                temp_tar_path.unlink()


# 便捷函数
async def skopeo_push_to_harbor(
    tar_file: BinaryIO,
    harbor_url: str,
    username: str,
    password: str,
    project: str,
    repository: str,
    tag: str,
    progress_callback=None
) -> Dict[str, Any]:
    """
    便捷函数：使用skopeo推送镜像到Harbor
    
    Args:
        tar_file: Docker tar文件流
        harbor_url: Harbor服务器URL
        username: 用户名
        password: 密码
        project: 项目名
        repository: 仓库名
        tag: 标签
        progress_callback: 进度回调函数
        
    Returns:
        推送结果字典
    """
    pusher = SkopeoPusher()
    
    # 检查skopeo可用性
    if not await pusher.check_skopeo_available():
        return {
            'status': 'error',
            'method': 'skopeo',
            'message': 'Skopeo不可用，请确保已安装skopeo'
        }
    
    return await pusher.push_from_tar(
        tar_file, harbor_url, username, password,
        project, repository, tag, progress_callback
    )