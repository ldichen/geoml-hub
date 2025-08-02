"""
Harbor镜像仓库客户端
负责与Harbor API交互，管理镜像的推送、拉取、删除等操作
"""
import aiohttp
import json
import base64
import hashlib
import tempfile
import asyncio
from typing import Dict, List, Optional, BinaryIO
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.utils.logger import logger


class HarborClient:
    """Harbor客户端，用于管理Docker镜像仓库"""
    
    def __init__(self):
        self.base_url = settings.harbor_url
        self.username = settings.harbor_username
        self.password = settings.harbor_password
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        auth = aiohttp.BasicAuth(self.username, self.password)
        self.session = aiohttp.ClientSession(
            auth=auth,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=300)  # 5分钟超时
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送HTTP请求的通用方法"""
        url = f"{self.base_url}/api/v2.0/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 404:
                    return None
                    
                response.raise_for_status()
                
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return {"content": await response.text()}
                    
        except aiohttp.ClientError as e:
            logger.error(f"Harbor API请求失败: {method} {url} - {e}")
            raise Exception(f"Harbor API请求失败: {e}")
    
    # ================== 项目管理 ==================
    
    async def create_project(self, project_name: str, public: bool = False) -> Dict:
        """创建Harbor项目"""
        project_data = {
            "project_name": project_name,
            "public": public,
            "metadata": {
                "auto_scan": "true",
                "severity": "high"
            }
        }
        
        result = await self._request("POST", "/projects", json=project_data)
        if result is None:
            # 项目可能已存在，尝试获取项目信息
            return await self.get_project(project_name)
        return result
    
    async def get_project(self, project_name: str) -> Optional[Dict]:
        """获取项目信息"""
        return await self._request("GET", f"/projects/{project_name}")
    
    async def list_projects(self, user_id: Optional[str] = None) -> List[Dict]:
        """列出项目"""
        params = {}
        if user_id:
            params["owner"] = user_id
            
        result = await self._request("GET", "/projects", params=params)
        return result if result else []
    
    # ================== 镜像仓库管理 ==================
    
    async def list_repositories(self, project_name: str) -> List[Dict]:
        """列出项目下的仓库"""
        result = await self._request("GET", f"/projects/{project_name}/repositories")
        return result if result else []
    
    async def get_repository(self, project_name: str, repository_name: str) -> Optional[Dict]:
        """获取仓库信息"""
        repo_path = f"{project_name}/{repository_name}"
        return await self._request("GET", f"/projects/{project_name}/repositories/{repository_name}")
    
    async def delete_repository(self, project_name: str, repository_name: str) -> bool:
        """删除仓库"""
        try:
            await self._request("DELETE", f"/projects/{project_name}/repositories/{repository_name}")
            return True
        except Exception:
            return False
    
    # ================== 镜像标签管理 ==================
    
    async def list_artifacts(self, project_name: str, repository_name: str) -> List[Dict]:
        """列出仓库的所有artifacts（镜像）"""
        result = await self._request("GET", f"/projects/{project_name}/repositories/{repository_name}/artifacts")
        return result if result else []
    
    async def get_artifact(self, project_name: str, repository_name: str, tag: str) -> Optional[Dict]:
        """获取特定标签的artifact信息"""
        result = await self._request("GET", f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}")
        return result
    
    async def delete_artifact(self, project_name: str, repository_name: str, tag: str) -> bool:
        """删除特定标签的artifact"""
        try:
            await self._request("DELETE", f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}")
            return True
        except Exception:
            return False
    
    # ================== 镜像推送 ==================
    
    async def push_image_from_tar(self, project_name: str, repository_name: str, tag: str, 
                                  tar_file: BinaryIO, progress_callback=None) -> Dict:
        """从tar文件推送镜像到Harbor"""
        
        # 1. 确保项目存在
        try:
            await self.create_project(project_name)
        except Exception as e:
            logger.warning(f"创建Harbor项目失败，可能已存在: {e}")
        
        # 2. 保存tar到临时文件
        temp_dir = Path(tempfile.mkdtemp())
        tar_path = temp_dir / f"{repository_name.replace('/', '_')}_{tag}.tar"
        
        try:
            # 写入tar文件
            with open(tar_path, 'wb') as f:
                chunk_size = 8192
                total_size = 0
                while chunk := tar_file.read(chunk_size):
                    f.write(chunk)
                    total_size += len(chunk)
                    if progress_callback:
                        progress_percent = min(int(total_size / (1024*1024) * 2), 50)  # 上传阶段占50%
                        await progress_callback(progress_percent, "uploading")
            
            if progress_callback:
                await progress_callback(50, "processing")
            
            # 3. 解析Harbor registry URL
            harbor_host = self.base_url.split('://')[-1]
            full_image_name = f"{harbor_host}/{project_name}/{repository_name}:{tag}"
            
            # 4. Docker登录Harbor
            login_cmd = f"echo '{self.password}' | docker login {harbor_host} -u {self.username} --password-stdin"
            process = await asyncio.create_subprocess_shell(
                login_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker登录Harbor失败: {stderr.decode()}")
            
            if progress_callback:
                await progress_callback(60, "loading")
            
            # 5. 加载镜像
            load_cmd = f"docker load -i '{tar_path}'"
            process = await asyncio.create_subprocess_shell(
                load_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker load失败: {stderr.decode()}")
            
            # 获取加载的镜像ID
            loaded_output = stdout.decode()
            logger.info(f"Docker load输出: {loaded_output}")
            
            # 从输出中提取镜像ID或名称
            image_id = None
            for line in loaded_output.split('\n'):
                if 'Loaded image:' in line:
                    image_id = line.split('Loaded image:')[-1].strip()
                    break
                elif 'Loaded image ID:' in line:
                    image_id = line.split('Loaded image ID:')[-1].strip()
                    break
            
            if not image_id:
                # 如果无法解析，使用最新的镜像
                get_latest_cmd = "docker images --format '{{.Repository}}:{{.Tag}}' | head -1"
                process = await asyncio.create_subprocess_shell(
                    get_latest_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    image_id = stdout.decode().strip()
            
            if not image_id:
                raise Exception("无法确定加载的镜像ID")
            
            if progress_callback:
                await progress_callback(75, "tagging")
            
            # 6. 标记镜像
            tag_cmd = f"docker tag '{image_id}' '{full_image_name}'"
            process = await asyncio.create_subprocess_shell(
                tag_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker tag失败: {stderr.decode()}")
            
            if progress_callback:
                await progress_callback(85, "pushing")
            
            # 7. 推送镜像
            push_cmd = f"docker push '{full_image_name}'"
            process = await asyncio.create_subprocess_shell(
                push_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Docker push失败: {stderr.decode()}")
            
            if progress_callback:
                await progress_callback(95, "verifying")
            
            # 8. 获取推送后的镜像信息
            await asyncio.sleep(1)  # 等待Harbor更新
            artifact_info = await self.get_artifact(project_name, repository_name, tag)
            
            if progress_callback:
                await progress_callback(100, "completed")
            
            # 9. 清理本地镜像（可选）
            cleanup_cmd = f"docker rmi '{full_image_name}' '{image_id}' 2>/dev/null || true"
            await asyncio.create_subprocess_shell(cleanup_cmd)
            
            return {
                "project_name": project_name,
                "repository_name": repository_name,
                "tag": tag,
                "full_name": full_image_name,
                "digest": artifact_info.get("digest") if artifact_info else None,
                "size": artifact_info.get("size") if artifact_info else None,
                "push_time": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"推送镜像到Harbor失败: {e}")
            raise Exception(f"推送镜像失败: {str(e)}")
            
        finally:
            # 清理临时文件
            try:
                if tar_path.exists():
                    tar_path.unlink()
                if temp_dir.exists():
                    temp_dir.rmdir()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
    
    # ================== 镜像扫描 ==================
    
    async def scan_artifact(self, project_name: str, repository_name: str, tag: str) -> Dict:
        """扫描镜像安全漏洞"""
        scan_data = {"scan_type": "vulnerability"}
        
        result = await self._request(
            "POST", 
            f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}/scan",
            json=scan_data
        )
        return result if result else {}
    
    async def get_scan_result(self, project_name: str, repository_name: str, tag: str) -> Optional[Dict]:
        """获取镜像扫描结果"""
        return await self._request(
            "GET",
            f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}/scan/vulnerabilities"
        )
    
    # ================== 工具方法 ==================
    
    async def test_connection(self) -> bool:
        """测试Harbor连接"""
        try:
            result = await self._request("GET", "/systeminfo")
            return result is not None
        except Exception as e:
            logger.error(f"Harbor连接测试失败: {e}")
            return False
    
    def generate_image_name(self, username: str, repo_name: str, tag: str = "latest") -> str:
        """生成标准的镜像名称"""
        return f"{username}/{repo_name}:{tag}"
    
    def parse_image_name(self, full_name: str) -> Dict[str, str]:
        """解析镜像名称"""
        # 格式: project/repository:tag
        if ':' in full_name:
            repo_part, tag = full_name.split(':', 1)
        else:
            repo_part, tag = full_name, 'latest'
            
        if '/' in repo_part:
            project, repository = repo_part.split('/', 1)
        else:
            project, repository = repo_part, repo_part
            
        return {
            "project": project,
            "repository": repository,
            "tag": tag
        }