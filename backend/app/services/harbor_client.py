"""
Harbor镜像仓库客户端 (优化版)
负责与Harbor API交互，管理镜像的推送、拉取、删除等操作
"""

import aiohttp
import asyncio
import re
import ssl
import shutil
import tempfile
from typing import Dict, List, Optional, BinaryIO, Any
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.utils.logger import logger


class HarborClient:
    """Harbor客户端，用于管理Docker镜像仓库 (优化版)"""

    def __init__(self):
        self.base_url = settings.harbor_url
        self.username = settings.harbor_username
        self.password = settings.harbor_password
        self.session = None
        self._login_cache = {}  # Docker登录状态缓存

    async def __aenter__(self):
        """异步上下文管理器入口"""
        auth = aiohttp.BasicAuth(self.username, self.password)

        # 创建SSL上下文，用于处理自签名证书
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # 创建优化的连接器
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,  # 连接池大小
            limit_per_host=5,  # 每个主机的连接数
            keepalive_timeout=30,  # 保持连接时间
            enable_cleanup_closed=True,
        )

        self.session = aiohttp.ClientSession(
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=600),  # 10分钟超时
            connector=connector,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()

    # ================== 项目管理 ==================

    async def create_project(self, project_name: str) -> Dict:
        """创建Harbor项目"""
        url = f"{self.base_url}/api/v2.0/projects"

        project_data = {
            "project_name": project_name,
            "public": False,  # 私有项目
            "registry_id": None,
        }

        try:
            async with self.session.post(url, json=project_data) as response:
                if response.status == 201:
                    logger.info(f"Harbor项目创建成功: {project_name}")
                    return {"status": "created", "project_name": project_name}
                elif response.status == 409:
                    logger.info(f"Harbor项目已存在: {project_name}")
                    return {"status": "exists", "project_name": project_name}
                else:
                    error_text = await response.text()
                    logger.error(f"创建项目失败: {response.status} - {error_text}")
                    return {"status": "error", "message": error_text}
        except Exception as e:
            logger.error(f"创建Harbor项目异常: {e}")
            return {"status": "error", "message": str(e)}

    # ================== 优化的镜像推送 ==================

    async def push_image_from_tar(
        self,
        project_name: str,
        repository_name: str,
        tag: str,
        tar_file: BinaryIO,
        progress_callback=None,
    ) -> Dict:
        """从tar文件推送镜像到Harbor (优化版)"""

        # 规范化名称为Docker兼容格式
        original_project = project_name
        original_repository = repository_name
        original_tag = tag

        project_name = self.normalize_repository_name(project_name)
        repository_name = self.normalize_repository_name(repository_name)
        tag = self.normalize_tag_name(tag)

        logger.info(
            f"规范化镜像名称: {original_project}/{original_repository}:{original_tag} -> {project_name}/{repository_name}:{tag}"
        )

        # 1. 确保项目存在
        try:
            await self.create_project(project_name)
        except Exception as e:
            logger.warning(f"创建Harbor项目失败，可能已存在: {e}")

        # 2. 使用优化的流式上传处理
        return await self._optimized_push_from_tar(
            project_name, repository_name, tag, tar_file, progress_callback
        )

    async def _optimized_push_from_tar(
        self,
        project_name: str,
        repository_name: str,
        tag: str,
        tar_file: BinaryIO,
        progress_callback=None,
    ) -> Dict:
        """优化的tar包推送实现"""

        temp_dir = None
        tar_path = None

        try:
            # 创建临时目录（优先使用内存文件系统）
            temp_dir = await self._create_optimized_temp_dir()
            tar_path = temp_dir / f"{repository_name.replace('/', '_')}_{tag}.tar"

            # 并行执行：流式写入文件 + Docker登录
            write_task = asyncio.create_task(
                self._streaming_write_tar(tar_file, tar_path, progress_callback)
            )
            login_task = asyncio.create_task(self._ensure_docker_login())

            # 等待写入完成和登录完成
            total_size, docker_login_done = await asyncio.gather(write_task, login_task)

            if progress_callback:
                await progress_callback(50, "processing")

            logger.info(
                f"文件写入完成: {total_size} bytes, Docker登录: {'成功' if docker_login_done else '失败'}"
            )

            if not docker_login_done:
                raise Exception("Docker登录失败")

            # 解析Harbor registry URL
            harbor_host = self.base_url.split("://")[-1]
            full_image_name = f"{harbor_host}/{project_name}/{repository_name}:{tag}"

            # 并行执行Docker操作
            load_task = asyncio.create_task(
                self._docker_load_with_progress(tar_path, progress_callback, 60)
            )

            # 等待Docker load完成并获取镜像信息
            image_info = await load_task

            if progress_callback:
                await progress_callback(75, "tagging")

            # 标记和推送镜像
            tag_push_result = await self._docker_tag_and_push(
                image_info, full_image_name, progress_callback
            )

            if progress_callback:
                await progress_callback(100, "completed")

            return {
                "status": "success",
                "image": full_image_name,
                "digest": tag_push_result.get("digest"),
                "size": total_size,
                "message": "镜像推送成功",
            }

        except Exception as e:
            logger.error(f"推送镜像失败: {e}")
            raise
        finally:
            # 清理临时文件
            await self._cleanup_temp_files(temp_dir, tar_path)

    async def _create_optimized_temp_dir(self) -> Path:
        """创建优化的临时目录（优先使用内存文件系统）"""
        # 尝试使用内存文件系统（Linux/macOS）
        memory_fs_paths = ["/dev/shm", "/tmp"]

        for path in memory_fs_paths:
            if Path(path).exists():
                try:
                    temp_dir = Path(tempfile.mkdtemp(dir=path, prefix="harbor_upload_"))
                    logger.info(f"使用优化临时目录: {temp_dir}")
                    return temp_dir
                except Exception:
                    continue

        # 回退到默认临时目录
        temp_dir = Path(tempfile.mkdtemp(prefix="harbor_upload_"))
        logger.info(f"使用默认临时目录: {temp_dir}")
        return temp_dir

    async def _streaming_write_tar(
        self, tar_file: BinaryIO, tar_path: Path, progress_callback=None
    ) -> int:
        """流式写入tar文件（大块读取，减少IO次数）"""
        import time

        chunk_size = 1024 * 1024  # 64KB chunks (优化后的块大小)
        total_size = 0
        MB = 1024 * 1024
        STEP = 50 * MB  # 每 5MB 回调一次
        SCALE = 1.0 / 50 * MB  # 1MB -> 2%
        CALLBACK_MIN_DELTA = 1  # 至少增长 1% 才回调
        CALLBACK_MIN_INTERVAL = 0.2  # 至少间隔 0.3s 才回调

        last_segment = -1  # 上次已跨过的 5MB 段数（-1 表示尚未开始）
        last_percent = -1  # 上次已回调的百分比
        last_ts = 0.0  # 上次回调时间戳
        try:
            with open(tar_path, "wb", buffering=1024 * 1024) as f:  # 512KB缓冲区
                while True:
                    chunk = tar_file.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    total_size += len(chunk)

                    if progress_callback:
                        # 当前总共跨过的 5MB 段数
                        curr_segment = total_size // STEP
                        if curr_segment > last_segment:
                            # 一次性可能跨过多个 50MB 边界：对每个边界触发一次
                            # 回调使用“边界处的字节数”来算百分比，保证稳定的 5MB 粒度
                            for seg in range(last_segment + 1, curr_segment + 1):
                                thresh_bytes = seg * STEP
                                percent = min(int(thresh_bytes * SCALE), 45)
                                # 双节流：时间 + 百分比增量
                                now = time.time()
                                if (percent >= last_percent + CALLBACK_MIN_DELTA) and (
                                    now - last_ts >= CALLBACK_MIN_INTERVAL
                                ):
                                    await progress_callback(percent, "uploading")
                                    last_percent = percent
                                    last_ts = now
                            last_segment = curr_segment

                # 确保数据写入磁盘
                f.flush()
                # 正常收尾：若未到 45%，补到 45%
            if progress_callback and last_percent < 45:
                await progress_callback(45, "uploading")

        except Exception as e:
            logger.error(f"流式写入失败: {e}")
            raise Exception(f"写入tar文件失败: {e}")

        logger.info(f"流式写入完成: {total_size} bytes")
        return total_size

    async def _ensure_docker_login(self) -> bool:
        """确保Docker登录（带重试和连接复用）"""
        harbor_host = self.base_url.split("://")[-1]

        # 检查缓存的登录状态
        if self._login_cache.get(harbor_host, False):
            logger.debug("使用缓存的Docker登录状态")
            return True

        # 执行登录（带重试）
        max_retries = 2
        for attempt in range(max_retries):
            try:
                login_cmd = f"echo '{self.password}' | docker login {harbor_host} -u {self.username} --password-stdin"
                process = await asyncio.create_subprocess_shell(
                    login_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info("Docker登录Harbor成功")
                    self._login_cache[harbor_host] = True  # 缓存登录状态
                    return True
                else:
                    error_msg = stderr.decode()
                    logger.warning(
                        f"Docker登录失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}"
                    )

                    if attempt == max_retries - 1:
                        raise Exception(f"Docker登录失败: {error_msg}")

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Docker登录异常: {e}")
                    return False
                await asyncio.sleep(1)  # 重试前等待

        return False

    async def _docker_load_with_progress(
        self, tar_path: Path, progress_callback=None, start_progress: int = 60
    ) -> Dict[str, str]:
        """执行Docker load操作并返回镜像信息"""
        try:
            if progress_callback:
                await progress_callback(start_progress, "loading")

            load_cmd = f"docker load -i '{tar_path}'"
            process = await asyncio.create_subprocess_shell(
                load_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Docker load失败: {stderr.decode()}")

            # 解析Docker load输出
            loaded_output = stdout.decode()
            logger.info(f"Docker load输出: {loaded_output}")

            # 提取镜像ID或名称
            image_id = None
            for line in loaded_output.split("\n"):
                if "Loaded image:" in line:
                    image_id = line.split("Loaded image:")[-1].strip()
                    break
                elif "Loaded image ID:" in line:
                    image_id = line.split("Loaded image ID:")[-1].strip()
                    break

            if not image_id:
                # 如果无法解析，使用最新的镜像
                get_latest_cmd = (
                    "docker images --format '{{.Repository}}:{{.Tag}}' | head -1"
                )
                process = await asyncio.create_subprocess_shell(
                    get_latest_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    image_id = stdout.decode().strip()

            if not image_id:
                raise Exception("无法确定加载的镜像ID")

            logger.info(f"成功加载镜像: {image_id}")
            return {"image_id": image_id, "loaded_output": loaded_output}

        except Exception as e:
            logger.error(f"Docker load失败: {e}")
            raise

    async def _docker_tag_and_push(
        self, image_info: Dict[str, str], full_image_name: str, progress_callback=None
    ) -> Dict[str, str]:
        """标记和推送镜像"""
        try:
            image_id = image_info["image_id"]

            # 标记镜像
            tag_cmd = f"docker tag '{image_id}' '{full_image_name}'"
            process = await asyncio.create_subprocess_shell(
                tag_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Docker tag失败: {stderr.decode()}")

            if progress_callback:
                await progress_callback(85, "pushing")

            # 推送镜像
            push_cmd = f"docker push '{full_image_name}'"
            process = await asyncio.create_subprocess_shell(
                push_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Docker push失败: {stderr.decode()}")

            if progress_callback:
                await progress_callback(95, "verifying")

            # 解析推送输出获取digest
            push_output = stdout.decode()
            logger.debug(f"Docker push输出: {push_output}")

            # 从推送输出中提取digest
            digest = None
            for line in push_output.split("\n"):
                if "digest:" in line.lower() and "sha256:" in line:
                    # 格式类似: latest: digest: sha256:abcd1234... size: 1234
                    parts = line.split("digest:")
                    if len(parts) > 1:
                        digest_part = (
                            parts[1].strip().split()[0]
                        )  # 取第一个空格前的部分
                        if digest_part.startswith("sha256:"):
                            digest = digest_part
                            break

            # 如果无法从Docker输出获取digest，尝试从Harbor API获取
            if not digest:
                digest = await self._get_image_digest_from_harbor(full_image_name)

            # 清理本地镜像（可选）
            cleanup_cmd = (
                f"docker rmi '{image_id}' '{full_image_name}' 2>/dev/null || true"
            )
            await asyncio.create_subprocess_shell(
                cleanup_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            logger.info(
                f"成功推送镜像: {full_image_name}, digest: {digest or 'unknown'}"
            )
            return {
                "digest": digest,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Docker tag和推送失败: {e}")
            raise

    async def _get_image_digest_from_harbor(
        self, full_image_name: str
    ) -> Optional[str]:
        """从Harbor API获取镜像digest"""
        try:
            # 解析镜像名称：registry/project/repository:tag
            parts = full_image_name.split("/")
            if len(parts) >= 3:
                project_name = parts[1]
                repository_tag = parts[2]

                if ":" in repository_tag:
                    repository_name, tag = repository_tag.rsplit(":", 1)
                else:
                    repository_name, tag = repository_tag, "latest"

                # 等待一下，让Harbor完成索引
                await asyncio.sleep(2)

                # 从Harbor API获取artifact信息
                artifact_info = await self.get_artifact(
                    project_name, repository_name, tag
                )

                if artifact_info and "digest" in artifact_info:
                    logger.info(f"从Harbor API获取到digest: {artifact_info['digest']}")
                    return artifact_info["digest"]
                else:
                    logger.warning(f"无法从Harbor API获取digest: {full_image_name}")

        except Exception as e:
            logger.error(f"从Harbor API获取digest失败: {e}")

        return None

    async def _cleanup_temp_files(self, temp_dir: Path = None, tar_path: Path = None):
        """清理临时文件"""
        try:
            if tar_path and tar_path.exists():
                tar_path.unlink()
                logger.debug(f"清理临时tar文件: {tar_path}")

            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.debug(f"清理临时目录: {temp_dir}")

        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    # ================== 工具方法 ==================

    def normalize_repository_name(self, name: str) -> str:
        """规范化仓库名称为Harbor兼容格式"""
        if not name:
            return "default"
        # 替换不符合Harbor规范的字符
        normalized = re.sub(r"[^a-z0-9\-_/.]", "-", name.lower())
        # 确保不以连字符开头或结尾
        normalized = normalized.strip("-")
        # 限制长度
        if len(normalized) > 255:
            normalized = normalized[:255]
        return normalized or "default"

    def normalize_tag_name(self, tag: str) -> str:
        """规范化标签名称为Docker兼容格式"""
        if not tag:
            return "latest"
        # Docker标签只能包含小写字母、数字、连字符、下划线和点
        normalized = re.sub(r"[^a-z0-9\-_.]", "-", tag.lower())
        # 确保不以点或连字符开头
        normalized = normalized.lstrip(".-")
        # 限制长度
        if len(normalized) > 128:
            normalized = normalized[:128]
        return normalized or "latest"

    # ================== 镜像一致性检查和清理 ==================

    async def get_all_harbor_images(
        self, project_name: Optional[str] = None
    ) -> List[Dict]:
        """获取Harbor中所有镜像的完整信息"""
        if not project_name:
            project_name = settings.harbor_default_project

        all_images = []

        try:
            repositories = await self.list_repositories(project_name)
            logger.info(f"找到 {len(repositories)} 个仓库")

            for repo in repositories:
                # 提取仓库名（去除项目前缀）
                repo_name = (
                    repo["name"].split("/")[-1] if "/" in repo["name"] else repo["name"]
                )

                try:
                    artifacts = await self.list_artifacts(project_name, repo_name)
                    logger.info(f"仓库 {repo_name} 包含 {len(artifacts)} 个artifacts")

                    for artifact in artifacts:
                        # 获取artifact的标签
                        tags = await self.get_artifact_tags(
                            project_name, repo_name, artifact["digest"]
                        )

                        # 构建镜像信息
                        image_info = {
                            "project_name": project_name,
                            "repository_name": repo_name,
                            "digest": artifact["digest"],
                            "size": artifact.get("size", 0),
                            "push_time": artifact.get("push_time"),
                            "pull_time": artifact.get("pull_time"),
                            "tags": [tag["name"] for tag in tags] if tags else [],
                            "full_repository_name": f"{project_name}/{repo_name}",
                            "harbor_storage_path": repo_name,  # Harbor中的存储路径
                            "artifact_info": artifact,
                        }

                        all_images.append(image_info)

                except Exception as e:
                    logger.error(f"获取仓库 {repo_name} 的artifacts失败: {e}")
                    continue

                # 避免过于频繁的API调用
                await asyncio.sleep(0.1)

            logger.info(f"从Harbor获取到 {len(all_images)} 个镜像")
            return all_images

        except Exception as e:
            logger.error(f"获取Harbor镜像列表失败: {e}")
            return []

    async def get_artifact_tags(
        self, project_name: str, repository_name: str, digest: str
    ) -> List[Dict]:
        """获取artifact的所有标签"""
        try:
            result = await self._request(
                "GET",
                f"/projects/{project_name}/repositories/{repository_name}/artifacts/{digest}/tags",
            )
            return result if result else []
        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return []

    async def compare_with_database_images(
        self, db_images: List[Dict]
    ) -> Dict[str, List]:
        """比较Harbor镜像与数据库记录，找出孤立镜像"""
        try:
            # 获取Harbor中的所有镜像
            harbor_images = await self.get_all_harbor_images()

            # 构建数据库镜像的Harbor存储路径集合
            db_storage_paths = set()
            for db_image in db_images:
                # 构建期望的Harbor存储路径
                storage_path = db_image.get("harbor_storage_name", "")
                if storage_path:
                    db_storage_paths.add(storage_path)

            logger.info(f"数据库中有 {len(db_storage_paths)} 个有效的镜像存储路径")
            logger.info(f"Harbor中有 {len(harbor_images)} 个镜像")

            # 找出孤立镜像（在Harbor中存在但数据库中没有记录）
            orphan_images = []
            valid_images = []

            for harbor_image in harbor_images:
                harbor_storage_path = harbor_image.get("harbor_storage_path", "")

                if harbor_storage_path in db_storage_paths:
                    valid_images.append(harbor_image)
                else:
                    orphan_images.append(harbor_image)

            # 找出缺失镜像（数据库中有记录但Harbor中不存在）
            missing_images = []
            harbor_storage_paths = {
                img.get("harbor_storage_path", "") for img in harbor_images
            }

            for db_image in db_images:
                expected_path = db_image.get("harbor_storage_name", "")
                if expected_path and expected_path not in harbor_storage_paths:
                    missing_images.append(db_image)

            result = {
                "orphan_images": orphan_images,
                "valid_images": valid_images,
                "missing_images": missing_images,
                "summary": {
                    "total_harbor_images": len(harbor_images),
                    "total_db_images": len(db_images),
                    "orphan_count": len(orphan_images),
                    "valid_count": len(valid_images),
                    "missing_count": len(missing_images),
                },
            }

            logger.info(
                f"镜像一致性检查完成: 孤立镜像 {len(orphan_images)} 个, 有效镜像 {len(valid_images)} 个, 缺失镜像 {len(missing_images)} 个"
            )
            return result

        except Exception as e:
            logger.error(f"镜像一致性检查失败: {e}")
            raise Exception(f"镜像一致性检查失败: {str(e)}")

    async def cleanup_orphan_images(
        self, orphan_images: List[Dict], dry_run: bool = True
    ) -> Dict[str, Any]:
        """清理孤立镜像"""
        cleanup_results = {
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "errors": [],
            "cleaned_images": [],
            "dry_run": dry_run,
        }

        if not orphan_images:
            logger.info("没有需要清理的孤立镜像")
            return cleanup_results

        logger.info(
            f"{'模拟' if dry_run else '开始'}清理 {len(orphan_images)} 个孤立镜像"
        )

        for image in orphan_images:
            cleanup_results["attempted"] += 1

            try:
                project_name = image.get("project_name")
                repository_name = image.get("repository_name")
                digest = image.get("digest")

                if not all([project_name, repository_name, digest]):
                    error_msg = f"镜像信息不完整: {image}"
                    cleanup_results["errors"].append(error_msg)
                    cleanup_results["failed"] += 1
                    continue

                if dry_run:
                    logger.info(
                        f"[模拟] 将删除镜像: {project_name}/{repository_name}@{digest}"
                    )
                    cleanup_results["succeeded"] += 1
                    cleanup_results["cleaned_images"].append(
                        {
                            "project_name": project_name,
                            "repository_name": repository_name,
                            "digest": digest,
                            "size": image.get("size", 0),
                            "action": "would_delete",
                        }
                    )
                else:
                    # 实际删除镜像
                    success = await self.delete_artifact(
                        project_name, repository_name, digest
                    )

                    if success:
                        logger.info(
                            f"成功删除孤立镜像: {project_name}/{repository_name}@{digest}"
                        )
                        cleanup_results["succeeded"] += 1
                        cleanup_results["cleaned_images"].append(
                            {
                                "project_name": project_name,
                                "repository_name": repository_name,
                                "digest": digest,
                                "size": image.get("size", 0),
                                "action": "deleted",
                            }
                        )
                    else:
                        error_msg = (
                            f"删除镜像失败: {project_name}/{repository_name}@{digest}"
                        )
                        cleanup_results["errors"].append(error_msg)
                        cleanup_results["failed"] += 1

                # 避免过于频繁的API调用
                await asyncio.sleep(0.2)

            except Exception as e:
                error_msg = f"处理镜像时出错: {image.get('repository_name', 'unknown')} - {str(e)}"
                cleanup_results["errors"].append(error_msg)
                cleanup_results["failed"] += 1
                logger.error(error_msg)

        logger.info(
            f"清理完成: 尝试 {cleanup_results['attempted']} 个, 成功 {cleanup_results['succeeded']} 个, 失败 {cleanup_results['failed']} 个"
        )
        return cleanup_results

    async def get_harbor_storage_usage(self) -> Dict[str, Any]:
        """获取Harbor存储使用情况"""
        try:
            # 获取系统信息
            system_info = await self._request("GET", "/systeminfo")

            # 获取所有项目的镜像
            all_images = await self.get_all_harbor_images()

            # 计算存储使用情况
            total_size = sum(img.get("size", 0) for img in all_images)

            usage_info = {
                "total_images": len(all_images),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
                "harbor_version": (
                    system_info.get("harbor_version", "unknown")
                    if system_info
                    else "unknown"
                ),
                "registry_url": self.base_url,
                "project_name": getattr(settings, "harbor_default_project", "default"),
            }

            return usage_info

        except Exception as e:
            logger.error(f"获取Harbor存储使用情况失败: {e}")
            return {"error": str(e), "total_images": 0, "total_size_bytes": 0}

    # ================== 通用请求方法 ==================

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送HTTP请求的通用方法"""
        url = f"{self.base_url}/api/v2.0/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 404:
                    return None

                response.raise_for_status()

                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return {"content": await response.text()}

        except aiohttp.ClientError as e:
            logger.error(f"Harbor API请求失败: {method} {url} - {e}")
            raise Exception(f"Harbor API请求失败: {e}")

    # ================== Harbor API 方法 ==================

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

    async def list_repositories(self, project_name: str) -> List[Dict]:
        """列出项目下的仓库"""
        result = await self._request("GET", f"/projects/{project_name}/repositories")
        return result if result else []

    async def get_repository(
        self, project_name: str, repository_name: str
    ) -> Optional[Dict]:
        """获取仓库信息"""
        return await self._request(
            "GET", f"/projects/{project_name}/repositories/{repository_name}"
        )

    async def delete_repository(self, project_name: str, repository_name: str) -> bool:
        """删除仓库"""
        try:
            await self._request(
                "DELETE", f"/projects/{project_name}/repositories/{repository_name}"
            )
            logger.info(f"删除Harbor仓库成功: {project_name}/{repository_name}")
            return True
        except Exception as e:
            logger.error(f"删除Harbor仓库异常: {e}")
            return False

    async def list_artifacts(
        self, project_name: str, repository_name: str
    ) -> List[Dict]:
        """列出仓库的所有artifacts（镜像）"""
        result = await self._request(
            "GET", f"/projects/{project_name}/repositories/{repository_name}/artifacts"
        )
        return result if result else []

    async def delete_artifact(
        self, project_name: str, repository_name: str, tag: str
    ) -> bool:
        """删除特定标签的artifact"""
        try:
            await self._request(
                "DELETE",
                f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}",
            )
            return True
        except Exception:
            return False

    async def get_artifact(
        self, project_name: str, repository_name: str, tag: str
    ) -> Optional[Dict]:
        """获取镜像制品信息"""
        return await self._request(
            "GET",
            f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}",
        )

    # ================== 镜像扫描 ==================

    async def scan_artifact(
        self, project_name: str, repository_name: str, tag: str
    ) -> Dict:
        """扫描镜像安全漏洞"""
        scan_data = {"scan_type": "vulnerability"}

        result = await self._request(
            "POST",
            f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}/scan",
            json=scan_data,
        )
        return result if result else {}

    async def get_scan_result(
        self, project_name: str, repository_name: str, tag: str
    ) -> Optional[Dict]:
        """获取镜像扫描结果"""
        return await self._request(
            "GET",
            f"/projects/{project_name}/repositories/{repository_name}/artifacts/{tag}/scan/vulnerabilities",
        )

    # ================== 连接和工具方法 ==================

    async def test_connection(self) -> bool:
        """测试Harbor连接"""
        try:
            result = await self._request("GET", "/systeminfo")
            return result is not None
        except Exception as e:
            logger.error(f"Harbor连接测试失败: {e}")
            return False

    def generate_image_name(
        self, username: str, repo_name: str, tag: str = "latest"
    ) -> str:
        """生成标准的镜像名称"""
        return f"{username}/{repo_name}:{tag}"

    def parse_image_name(self, full_name: str) -> Dict[str, str]:
        """解析镜像名称"""
        # 格式: project/repository:tag
        if ":" in full_name:
            repo_part, tag = full_name.split(":", 1)
        else:
            repo_part, tag = full_name, "latest"

        if "/" in repo_part:
            project, repository = repo_part.split("/", 1)
        else:
            project, repository = repo_part, repo_part

        return {"project": project, "repository": repository, "tag": tag}
