"""
Skopeo镜像推送工具
支持原生skopeo和Docker容器两种方式
使用常驻容器实现高性能、稳定的镜像仓库推送功能
"""

import asyncio
import json
import tempfile
import shutil
import os
import uuid
from pathlib import Path
from typing import Dict, BinaryIO, Any, Optional, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SkopeoPusher:
    """基于skopeo的镜像推送器,支持原生和Docker两种模式"""

    def __init__(self, use_docker: bool = False, container_name: str = "skopeo-service"):
        """
        初始化Skopeo推送器

        Args:
            use_docker: 是否使用Docker容器中的skopeo
            container_name: Docker容器名称(仅use_docker=True时有效)
        """
        self.use_docker = use_docker
        self.container_name = container_name

        if self.use_docker:
            # Docker模式: 使用共享目录
            self.host_shared_dir = Path(os.getenv('SKOPEO_SHARED_DIR', '/tmp/geoml-skopeo'))
            self.container_shared_dir = '/tmp/skopeo'

            # 确保宿主机共享目录存在
            self.host_shared_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Docker模式: 共享目录 {self.host_shared_dir}")
        else:
            # 原生模式
            self.host_shared_dir = None
            self.container_shared_dir = None
            logger.info("原生Skopeo模式")

    async def check_skopeo_available(self) -> bool:
        """检查skopeo是否可用"""
        try:
            if self.use_docker:
                # Docker模式: 检查容器和容器内skopeo
                return await self._check_docker_skopeo()
            else:
                # 原生模式: 检查系统skopeo
                return await self._check_native_skopeo()

        except Exception as e:
            logger.error(f"Skopeo检查失败: {e}")
            return False

    async def _check_docker_skopeo(self) -> bool:
        """检查Docker容器中的skopeo"""
        try:
            # 1. 检查容器是否存在并运行
            inspect_process = await asyncio.create_subprocess_exec(
                "docker", "inspect", "-f", "{{.State.Running}}",
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await inspect_process.communicate()

            if inspect_process.returncode != 0:
                logger.error(f"Skopeo容器 '{self.container_name}' 不存在")
                logger.info("请运行以下命令启动Skopeo容器:")
                logger.info(f"  docker run -d --name {self.container_name} \\")
                logger.info(f"    -v {self.host_shared_dir}:{self.container_shared_dir} \\")
                logger.info(f"    quay.io/skopeo/stable tail -f /dev/null")
                return False

            is_running = stdout.decode().strip() == "true"
            if not is_running:
                logger.error(f"Skopeo容器 '{self.container_name}' 未运行")
                logger.info(f"请运行: docker start {self.container_name}")
                return False

            # 2. 检查容器内skopeo命令
            version_process = await asyncio.create_subprocess_exec(
                "docker", "exec", self.container_name,
                "skopeo", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await version_process.communicate()

            if version_process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Docker容器Skopeo可用: {version}")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"容器内Skopeo不可用: {error_msg}")
                return False

        except FileNotFoundError:
            logger.error("Docker命令不可用,请确保已安装Docker")
            return False
        except Exception as e:
            logger.error(f"检查Docker Skopeo失败: {e}")
            return False

    async def _check_native_skopeo(self) -> bool:
        """检查原生skopeo"""
        try:
            process = await asyncio.create_subprocess_exec(
                "skopeo", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"原生Skopeo可用: {version}")
                return True
            else:
                logger.error(f"Skopeo检查失败: {stderr.decode()}")
                return False

        except FileNotFoundError:
            logger.error("Skopeo命令不可用,请确保已安装skopeo")
            return False
        except Exception as e:
            logger.error(f"检查原生Skopeo失败: {e}")
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
        host_tar_path = None

        try:
            method = "Docker容器" if self.use_docker else "原生Skopeo"
            if progress_callback:
                await progress_callback(5, f"准备{method}推送...")

            # 1. 保存tar文件到临时路径 (返回宿主机路径和容器路径)
            host_tar_path, container_tar_path = await self._save_temp_tar(tar_file)
            logger.info(f"临时tar文件已保存: {host_tar_path}")

            if progress_callback:
                await progress_callback(10, "开始skopeo推送...")

            # 2. 构建目标URL (移除协议前缀)
            clean_harbor_url = harbor_url.replace('https://', '').replace('http://', '').rstrip('/')
            target_url = f"{clean_harbor_url}/{project}/{repository}:{tag}"
            logger.info(f"推送目标: docker://{target_url}")

            # 3. 执行skopeo推送
            result = await self._execute_skopeo_copy(
                host_tar_path, container_tar_path,
                target_url, username, password,
                progress_callback
            )

            if result.get('status') == 'success':
                logger.info(f"{method}推送成功: {project}/{repository}:{tag}")
                return {
                    'status': 'success',
                    'method': 'docker' if self.use_docker else 'native',
                    'image': f"{project}/{repository}:{tag}",
                    'message': f'{method}推送成功',
                    'performance_improvement': '高性能推送'
                }
            else:
                logger.error(f"{method}推送失败: {result.get('message')}")
                return result

        except Exception as e:
            logger.error(f"推送异常: {e}")
            return {
                'status': 'error',
                'method': 'docker' if self.use_docker else 'native',
                'message': f'推送异常: {str(e)}'
            }

        finally:
            # 清理临时文件
            if host_tar_path and host_tar_path.exists():
                try:
                    host_tar_path.unlink()
                    logger.debug(f"清理临时文件: {host_tar_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    async def _save_temp_tar(self, tar_file: BinaryIO) -> Tuple[Path, str]:
        """
        保存tar文件到临时路径

        Returns:
            tuple: (宿主机路径, 容器内路径)
        """
        try:
            # 重置文件指针
            tar_file.seek(0)

            if self.use_docker:
                # Docker模式: 保存到共享目录
                filename = f"skopeo_{uuid.uuid4().hex}.tar"
                host_path = self.host_shared_dir / filename
                container_path = f"{self.container_shared_dir}/{filename}"

                # 保存到宿主机共享目录
                with open(host_path, 'wb') as f:
                    shutil.copyfileobj(tar_file, f)

                logger.debug(f"保存到共享目录 - 宿主机: {host_path}, 容器: {container_path}")
                logger.debug(f"文件大小: {host_path.stat().st_size} bytes")
                return host_path, container_path

            else:
                # 原生模式: 使用系统临时目录
                temp_fd, temp_path_str = tempfile.mkstemp(suffix='.tar', prefix='skopeo_')
                temp_path = Path(temp_path_str)

                # 写入数据
                with open(temp_fd, 'wb') as f:
                    shutil.copyfileobj(tar_file, f)

                logger.debug(f"保存到临时文件: {temp_path} ({temp_path.stat().st_size} bytes)")
                # 原生模式下,宿主机路径和容器路径相同
                return temp_path, str(temp_path)

        except Exception as e:
            logger.error(f"保存临时tar文件失败: {e}")
            raise

    async def _execute_skopeo_copy(
        self,
        host_tar_path: Path,
        container_tar_path: str,
        target_url: str,
        username: str,
        password: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """执行skopeo copy命令"""
        try:
            if self.use_docker:
                # Docker模式: 使用docker exec调用容器内skopeo
                tar_path_for_skopeo = container_tar_path
                cmd = [
                    "docker", "exec", self.container_name,
                    "skopeo", "copy",
                    "--insecure-policy",
                    "--dest-tls-verify=false",
                    "--dest-username", username,
                    "--dest-password", password,
                    f"docker-archive:{tar_path_for_skopeo}",
                    f"docker://{target_url}"
                ]
            else:
                # 原生模式: 直接调用skopeo
                tar_path_for_skopeo = str(host_tar_path)
                cmd = [
                    "skopeo", "copy",
                    "--insecure-policy",
                    "--dest-tls-verify=false",
                    "--dest-username", username,
                    "--dest-password", password,
                    f"docker-archive:{tar_path_for_skopeo}",
                    f"docker://{target_url}"
                ]

            # 安全日志 (隐藏密码)
            safe_cmd = self._build_safe_log(cmd)
            logger.debug(f"执行命令: {safe_cmd}")

            if progress_callback:
                await progress_callback(20, "执行skopeo copy...")

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 启动进度监控
            monitor_task = None
            if progress_callback:
                monitor_task = asyncio.create_task(
                    self._monitor_progress(progress_callback)
                )

            # 等待命令完成
            stdout, stderr = await process.communicate()

            # 取消进度监控
            if monitor_task:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            if progress_callback:
                await progress_callback(100, "推送完成")

            # 处理结果
            if process.returncode == 0:
                method = "Docker容器" if self.use_docker else "原生Skopeo"
                logger.info(f"{method} copy执行成功")
                stdout_text = stdout.decode() if stdout else ""
                return {
                    'status': 'success',
                    'stdout': stdout_text,
                    'message': f'{method}推送成功',
                    'method': 'docker' if self.use_docker else 'native'
                }
            else:
                stderr_text = stderr.decode() if stderr else ""
                logger.error(f"Skopeo copy失败: {stderr_text}")
                return {
                    'status': 'error',
                    'stderr': stderr_text,
                    'message': f'Skopeo推送失败: {stderr_text}',
                    'method': 'docker' if self.use_docker else 'native'
                }

        except Exception as e:
            logger.error(f"执行skopeo命令异常: {e}")
            return {
                'status': 'error',
                'message': f'执行skopeo命令异常: {str(e)}'
            }

    def _build_safe_log(self, cmd: list) -> str:
        """构建隐藏敏感信息的安全日志"""
        safe_cmd = []
        skip_next = False

        for arg in cmd:
            if skip_next:
                safe_cmd.append('[HIDDEN]')
                skip_next = False
            elif arg in ['--dest-password', '--dest-username', '--src-password', '--src-username']:
                safe_cmd.append(arg)
                skip_next = True
            else:
                safe_cmd.append(arg)

        return ' '.join(safe_cmd)

    async def _monitor_progress(self, progress_callback):
        """监控推送进度 (简化实现)"""
        try:
            progress_points = [30, 40, 50, 60, 70, 80, 90]
            for progress in progress_points:
                await asyncio.sleep(2)  # 每2秒更新一次进度
                await progress_callback(progress, f"推送中... ({progress}%)")
        except asyncio.CancelledError:
            pass

    async def get_image_info_from_tar(self, tar_file: BinaryIO) -> Dict[str, Any]:
        """从tar文件获取镜像信息 (用于进度显示等)"""
        temp_tar_path = None

        try:
            # 保存临时文件
            temp_tar_path, container_tar_path = await self._save_temp_tar(tar_file)

            if self.use_docker:
                # Docker模式
                cmd = [
                    "docker", "exec", self.container_name,
                    "skopeo", "inspect",
                    f"docker-archive:{container_tar_path}"
                ]
            else:
                # 原生模式
                cmd = [
                    "skopeo", "inspect",
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
            # 清理临时文件
            if temp_tar_path and temp_tar_path.exists():
                try:
                    temp_tar_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")


# 便捷函数
async def skopeo_push_to_harbor(
    tar_file: BinaryIO,
    harbor_url: str,
    username: str,
    password: str,
    project: str,
    repository: str,
    tag: str,
    progress_callback=None,
    prefer_docker: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：使用skopeo推送镜像到Harbor，支持自动回退

    Args:
        tar_file: Docker tar文件流
        harbor_url: Harbor服务器URL
        username: 用户名
        password: 密码
        project: 项目名
        repository: 仓库名
        tag: 标签
        progress_callback: 进度回调函数
        prefer_docker: 是否优先使用Docker方式 (默认True)

    Returns:
        推送结果字典
    """

    # 优先使用Docker方式
    if prefer_docker:
        pusher = SkopeoPusher(use_docker=True)
        if await pusher.check_skopeo_available():
            logger.info("使用Docker容器方式执行skopeo")
            return await pusher.push_from_tar(
                tar_file, harbor_url, username, password,
                project, repository, tag, progress_callback
            )
        else:
            logger.warning("Docker方式不可用，尝试原生skopeo")

    # 回退到原生skopeo
    pusher = SkopeoPusher(use_docker=False)
    if not await pusher.check_skopeo_available():
        return {
            'status': 'error',
            'method': 'skopeo',
            'message': 'Skopeo不可用，请确保已安装skopeo或配置Docker容器'
        }

    logger.info("使用原生skopeo方式")
    return await pusher.push_from_tar(
        tar_file, harbor_url, username, password,
        project, repository, tag, progress_callback
    )
