"""
Docker 操作服务
"""

import asyncio
import docker
import psutil
import logging
import base64
import io
import tarfile
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from docker.errors import DockerException, NotFound, APIError

from app.config import settings, get_server_capabilities
from app.models.container import (
    ContainerCreateRequest,
    ContainerInfo,
    ContainerStatus,
    ContainerStatsResponse,
    ContainerLogsResponse,
    ContainerListResponse,
    ContainerOperationResponse,
    ContainerFileOperationRequest,
    ContainerFileOperationResponse,
    ContainerDirectoryOperationRequest,
    ImageInfo,
    SystemInfo,
)

logger = logging.getLogger(__name__)


class DockerService:
    """Docker 操作服务"""

    def __init__(self):
        self.client = None
        self.server_capabilities = get_server_capabilities()
        self._init_docker_client()

    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            self.client = docker.from_env(timeout=settings.docker_timeout)
            # 测试连接
            self.client.ping()
            logger.info(f"Docker客户端初始化成功，连接到: {settings.docker_host}")
        except Exception as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            self.client = None
            raise

    def _ensure_client(self):
        """确保Docker客户端可用"""
        try:
            if not self.client:
                self._init_docker_client()
            else:
                self.client.ping()
        except Exception as e:
            logger.warning(f"Docker连接异常，尝试重新连接: {e}")
            try:
                self._init_docker_client()
            except Exception as init_error:
                logger.error(f"Docker重新连接失败: {init_error}")
                raise DockerException(f"Docker服务不可用: {str(init_error)}")

    async def create_container(
        self, config: ContainerCreateRequest
    ) -> ContainerOperationResponse:
        """创建容器"""
        self._ensure_client()

        try:
            # 添加调试日志：打印接收到的配置
            logger.info(f"=== 开始创建容器 ===")
            logger.info(f"容器名称: {config.name}")
            logger.info(f"镜像名称: {config.image}")
            logger.info(f"环境变量: {config.environment}")
            logger.info(f"端口映射: {config.ports}")
            logger.info(f"标签: {config.labels}")
            logger.info(f"内存限制: {config.memory_limit}")
            logger.info(f"CPU限制: {config.cpu_limit}")
            logger.info(f"重启策略: {config.restart_policy}")
            logger.info(f"工作目录: {config.working_dir}")
            logger.info(f"启动命令: {config.command}")

            # 检查容器数量限制
            current_containers = len(self.client.containers.list())
            if current_containers >= settings.max_containers:
                raise Exception(f"已达到最大容器数量限制: {settings.max_containers}")

            # 构建Docker创建参数
            create_kwargs = {
                "image": config.image,
                "name": config.name,
                "detach": config.detach,
                "environment": config.environment,
                "volumes": self._format_volumes(config.volumes),
                "ports": self._format_ports(config.ports),
                "mem_limit": config.memory_limit,
                "cpu_quota": int(config.cpu_limit * 100000),
                "cpu_period": 100000,
                "restart_policy": {"Name": config.restart_policy},
                "labels": {
                    **config.labels,
                    "mmanager.managed": "true",
                    "mmanager.server_id": settings.server_id,
                    "mmanager.created_at": datetime.now(timezone.utc).isoformat(),
                },
                "auto_remove": config.auto_remove,
            }

            # 设置工作目录
            if config.working_dir:
                create_kwargs["working_dir"] = config.working_dir

            # 设置启动命令
            if config.command:
                create_kwargs["command"] = config.command

            # 网络配置
            if config.network_mode:
                create_kwargs["network_mode"] = config.network_mode
            elif settings.default_network and settings.default_network.strip():
                # 只有当 default_network 不为空且非空白字符串时才使用
                create_kwargs["network"] = settings.default_network

            # 添加调试日志：打印最终的Docker创建参数
            logger.info(f"=== Docker创建参数 ===")
            logger.info(f"完整参数: {create_kwargs}")
            logger.info(f"格式化后的端口: {create_kwargs.get('ports', {})}")
            logger.info(f"格式化后的卷: {create_kwargs.get('volumes', {})}")
            logger.info(f"最终标签: {create_kwargs.get('labels', {})}")
            logger.info(f"最终环境变量: {create_kwargs.get('environment', {})}")

            # 异步执行Docker操作
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None, lambda: self.client.containers.create(**create_kwargs)
            )

            # 如果指定了额外网络，连接到这些网络
            for network_name in config.networks:
                try:
                    network = self.client.networks.get(network_name)
                    await loop.run_in_executor(None, network.connect, container)
                except Exception as e:
                    logger.warning(f"连接到网络 {network_name} 失败: {e}")

            logger.info(f"容器创建成功: {container.id[:12]} ({config.name})")

            # 添加调试日志：验证创建的容器配置
            try:
                container.reload()
                actual_config = container.attrs.get("Config", {})
                actual_host_config = container.attrs.get("HostConfig", {})
                network_settings = container.attrs.get("NetworkSettings", {})

                logger.info(f"=== 验证创建的容器配置 ===")
                logger.info(f"实际环境变量: {actual_config.get('Env', [])}")
                logger.info(f"实际标签: {actual_config.get('Labels', {})}")
                logger.info(
                    f"实际端口绑定: {actual_host_config.get('PortBindings', {})}"
                )
                logger.info(f"实际网络端口: {network_settings.get('Ports', {})}")
                logger.info(f"实际内存限制: {actual_host_config.get('Memory', 0)}")
                logger.info(f"实际CPU配额: {actual_host_config.get('CpuQuota', 0)}")
                logger.info(
                    f"实际重启策略: {actual_host_config.get('RestartPolicy', {})}"
                )
            except Exception as e:
                logger.warning(f"获取容器验证信息失败: {e}")

            return ContainerOperationResponse(
                success=True,
                container_id=container.id,
                message="容器创建成功",
                operation="create",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "name": container.name,
                    "image": config.image,
                    "status": "created",
                },
            )

        except docker.errors.ImageNotFound:
            error_msg = f"镜像不存在: {config.image}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id="",
                message=error_msg,
                operation="create",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"创建容器失败: {str(e)}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id="",
                message=error_msg,
                operation="create",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    async def start_container(self, container_id: str) -> ContainerOperationResponse:
        """启动容器"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)

            # 检查容器状态
            if container.status == "running":
                return ContainerOperationResponse(
                    success=True,
                    container_id=container_id,
                    message="容器已在运行",
                    operation="start",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            # 异步启动容器
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, container.start)

            logger.info(f"容器启动成功: {container_id[:12]}")

            return ContainerOperationResponse(
                success=True,
                container_id=container_id,
                message="容器启动成功",
                operation="start",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"name": container.name, "status": "running"},
            )

        except NotFound:
            error_msg = f"容器不存在: {container_id}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="start",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"启动容器失败: {str(e)}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="start",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    async def stop_container(
        self, container_id: str, timeout: int = 10
    ) -> ContainerOperationResponse:
        """停止容器"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)

            # 检查容器状态
            if container.status not in ["running", "restarting"]:
                return ContainerOperationResponse(
                    success=True,
                    container_id=container_id,
                    message=f"容器已停止，当前状态: {container.status}",
                    operation="stop",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            # 异步停止容器
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: container.stop(timeout=timeout))

            logger.info(f"容器停止成功: {container_id[:12]}")

            return ContainerOperationResponse(
                success=True,
                container_id=container_id,
                message="容器停止成功",
                operation="stop",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"name": container.name, "status": "exited"},
            )

        except NotFound:
            error_msg = f"容器不存在: {container_id}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="stop",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"停止容器失败: {str(e)}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="stop",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    async def remove_container(
        self, container_id: str, force: bool = False
    ) -> ContainerOperationResponse:
        """删除容器"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)
            container_name = container.name

            # 异步删除容器
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: container.remove(force=force))

            logger.info(f"容器删除成功: {container_id[:12]} ({container_name})")

            return ContainerOperationResponse(
                success=True,
                container_id=container_id,
                message="容器删除成功",
                operation="remove",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"name": container_name, "force": force},
            )

        except NotFound:
            # 容器不存在，认为删除成功
            return ContainerOperationResponse(
                success=True,
                container_id=container_id,
                message="容器不存在，删除成功",
                operation="remove",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"删除容器失败: {str(e)}"
            logger.error(error_msg)
            return ContainerOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="remove",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    async def get_container_info(self, container_id: str) -> ContainerInfo:
        """获取容器详细信息"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)

            # 异步刷新容器状态
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, container.reload)

            # 解析容器信息
            attrs = container.attrs
            config = attrs.get("Config", {})
            network_settings = attrs.get("NetworkSettings", {})
            host_config = attrs.get("HostConfig", {})
            state = attrs.get("State", {})

            # 端口映射
            ports = {}
            port_bindings = network_settings.get("Ports", {})
            for container_port, host_ports in port_bindings.items():
                if host_ports:
                    ports[container_port] = int(host_ports[0]["HostPort"])

            # 网络信息
            networks = network_settings.get("Networks", {})
            ip_address = None
            if networks:
                # 获取第一个网络的IP地址
                first_network = next(iter(networks.values()))
                ip_address = first_network.get("IPAddress")

            # 资源限制
            resource_limits = {
                "memory": host_config.get("Memory", 0),
                "cpu_quota": host_config.get("CpuQuota", 0),
                "cpu_period": host_config.get("CpuPeriod", 0),
            }

            # 挂载点
            mounts = []
            for mount in attrs.get("Mounts", []):
                mounts.append(
                    {
                        "source": mount.get("Source"),
                        "destination": mount.get("Destination"),
                        "mode": mount.get("Mode"),
                        "type": mount.get("Type"),
                    }
                )

            return ContainerInfo(
                id=container.id,
                name=container.name,
                image=config.get("Image", ""),
                status=ContainerStatus(container.status),
                created_at=attrs.get("Created", ""),
                started_at=state.get("StartedAt"),
                finished_at=state.get("FinishedAt"),
                ports=ports,
                networks=networks,
                ip_address=ip_address,
                resource_limits=resource_limits,
                labels=config.get("Labels", {}),
                environment=self._parse_environment_vars(config.get("Env", [])),
                mounts=mounts,
            )

        except NotFound:
            raise Exception(f"容器不存在: {container_id}")
        except Exception as e:
            logger.error(f"获取容器信息失败: {e}")
            raise

    async def get_container_stats(self, container_id: str) -> ContainerStatsResponse:
        """获取容器统计信息"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)

            # 异步获取统计信息
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None, lambda: container.stats(stream=False)
            )

            # 解析统计数据
            cpu_stats = stats.get("cpu_stats", {})
            memory_stats = stats.get("memory_stats", {})
            networks = stats.get("networks", {})
            blkio_stats = stats.get("blkio_stats", {})

            # 计算CPU使用率
            cpu_percent = 0.0
            if "cpu_usage" in cpu_stats and "precpu_stats" in stats:
                precpu_stats = stats["precpu_stats"]
                cpu_usage = cpu_stats["cpu_usage"]["total_usage"]
                precpu_usage = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                system_usage = cpu_stats.get("system_cpu_usage", 0)
                pre_system_usage = precpu_stats.get("system_cpu_usage", 0)

                cpu_delta = cpu_usage - precpu_usage
                system_delta = system_usage - pre_system_usage

                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0

            # 内存使用情况
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0.0
            )

            # 网络统计
            network_rx_bytes = 0
            network_tx_bytes = 0
            for network_data in networks.values():
                network_rx_bytes += network_data.get("rx_bytes", 0)
                network_tx_bytes += network_data.get("tx_bytes", 0)

            # 块IO统计
            block_read_bytes = 0
            block_write_bytes = 0
            for io_stat in blkio_stats.get("io_service_bytes_recursive", []):
                if io_stat["op"] == "Read":
                    block_read_bytes += io_stat["value"]
                elif io_stat["op"] == "Write":
                    block_write_bytes += io_stat["value"]

            return ContainerStatsResponse(
                container_id=container_id,
                cpu_percent=round(cpu_percent, 2),
                cpu_usage=cpu_stats,
                memory_usage_mb=round(memory_usage / 1024 / 1024, 2),
                memory_limit_mb=round(memory_limit / 1024 / 1024, 2),
                memory_percent=round(memory_percent, 2),
                network_rx_bytes=network_rx_bytes,
                network_tx_bytes=network_tx_bytes,
                block_read_bytes=block_read_bytes,
                block_write_bytes=block_write_bytes,
                pids=stats.get("pids_stats", {}).get("current", 0),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except NotFound:
            raise Exception(f"容器不存在: {container_id}")
        except Exception as e:
            logger.error(f"获取容器统计信息失败: {e}")
            raise

    async def get_container_logs(
        self, container_id: str, lines: int = 100, follow: bool = False
    ) -> ContainerLogsResponse:
        """获取容器日志"""
        self._ensure_client()

        try:
            container = self.client.containers.get(container_id)

            # 异步获取日志
            loop = asyncio.get_event_loop()
            logs = await loop.run_in_executor(
                None, lambda: container.logs(tail=lines, follow=follow, decode=True)
            )

            # 处理日志内容
            if isinstance(logs, bytes):
                logs = logs.decode("utf-8", errors="replace")

            # 计算实际行数
            actual_lines = len([line for line in logs.split("\n") if line.strip()])

            return ContainerLogsResponse(
                container_id=container_id,
                logs=logs,
                lines=actual_lines,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except NotFound:
            raise Exception(f"容器不存在: {container_id}")
        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            raise

    async def list_containers(
        self, all_containers: bool = False
    ) -> ContainerListResponse:
        """列出容器"""
        self._ensure_client()

        try:
            # 异步获取容器列表
            loop = asyncio.get_event_loop()
            containers = await loop.run_in_executor(
                None, lambda: self.client.containers.list(all=all_containers)
            )

            container_infos = []
            running_count = 0
            stopped_count = 0

            for container in containers:
                try:
                    # 获取基本信息
                    info = ContainerInfo(
                        id=container.id,
                        name=container.name,
                        image=(
                            container.image.tags[0]
                            if container.image.tags
                            else container.image.id[:12]
                        ),
                        status=ContainerStatus(container.status),
                        created_at=container.attrs.get("Created", ""),
                        labels=container.labels or {},
                    )

                    container_infos.append(info)

                    # 统计数量
                    if container.status == "running":
                        running_count += 1
                    else:
                        stopped_count += 1

                except Exception as e:
                    logger.warning(f"处理容器 {container.id[:12]} 信息失败: {e}")
                    continue

            return ContainerListResponse(
                containers=container_infos,
                total=len(container_infos),
                running=running_count,
                stopped=stopped_count,
            )

        except Exception as e:
            logger.error(f"列出容器失败: {e}")
            raise

    async def get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        self._ensure_client()

        try:
            # 异步获取Docker信息
            loop = asyncio.get_event_loop()
            docker_info = await loop.run_in_executor(None, self.client.info)
            version_info = await loop.run_in_executor(None, self.client.version)

            # 获取系统资源信息
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return SystemInfo(
                docker_version=version_info.get("Version", "unknown"),
                containers_total=docker_info.get("Containers", 0),
                containers_running=docker_info.get("ContainersRunning", 0),
                containers_stopped=docker_info.get("ContainersStopped", 0),
                images_total=docker_info.get("Images", 0),
                cpu_cores=psutil.cpu_count(),
                memory_total_gb=round(memory.total / 1024 / 1024 / 1024, 2),
                memory_available_gb=round(memory.available / 1024 / 1024 / 1024, 2),
                disk_usage={
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "percent": round(disk.used / disk.total * 100, 2),
                },
            )

        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            raise

    def _format_volumes(self, volumes: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """格式化卷挂载"""
        formatted = {}
        for host_path, container_path in volumes.items():
            formatted[host_path] = {"bind": container_path, "mode": "rw"}
        return formatted

    def _format_ports(self, ports: Dict[str, int]) -> Dict[str, int]:
        """格式化端口映射"""
        formatted = {}
        for container_port, host_port in ports.items():
            # 确保端口格式正确
            if "/" not in container_port:
                container_port = f"{container_port}/tcp"
            formatted[container_port] = host_port
        return formatted

    def _parse_environment_vars(self, env_list: List[str]) -> Dict[str, str]:
        """解析环境变量列表为字典

        Args:
            env_list: Docker环境变量列表，格式如 ['VAR1=value1', 'VAR2=value2']

        Returns:
            字典格式的环境变量 {'VAR1': 'value1', 'VAR2': 'value2'}
        """
        env_dict = {}
        for env_var in env_list:
            if "=" in env_var:
                key, value = env_var.split("=", 1)  # 只分割第一个=号
                env_dict[key] = value
            else:
                # 处理没有值的环境变量
                env_dict[env_var] = ""
        return env_dict

    async def copy_file_to_container(
        self, container_id: str, request: ContainerFileOperationRequest
    ) -> ContainerFileOperationResponse:
        """复制文件到容器"""
        self._ensure_client()

        try:
            # 获取容器
            container = self.client.containers.get(container_id)

            # 解码base64内容
            if not request.content_base64:
                raise ValueError("文件内容不能为空")

            file_content = base64.b64decode(request.content_base64)

            # 确定文件名
            file_name = request.file_name or "file"

            # 创建tar包
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                info = tarfile.TarInfo(name=file_name)
                info.size = len(file_content)
                info.mode = 0o644  # 设置文件权限
                tar.addfile(info, io.BytesIO(file_content))

            tar_buffer.seek(0)

            # 复制到容器
            target_dir = os.path.dirname(request.container_path)
            if not target_dir:
                target_dir = "/"

            container.put_archive(target_dir, tar_buffer.read())

            logger.info(f"成功复制文件到容器 {container_id}:{request.container_path}")

            return ContainerFileOperationResponse(
                success=True,
                container_id=container_id,
                message=f"文件复制成功: {file_name}",
                operation="copy_file",
                file_path=request.container_path,
                file_size=len(file_content),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except NotFound:
            error_msg = f"容器 {container_id} 不存在"
            logger.error(error_msg)
            return ContainerFileOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="copy_file",
                file_path=request.container_path,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"复制文件失败: {str(e)}"
            logger.error(f"复制文件到容器失败 {container_id}: {e}")
            return ContainerFileOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="copy_file",
                file_path=request.container_path,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    async def copy_directory_to_container(
        self, container_id: str, request: ContainerDirectoryOperationRequest
    ) -> ContainerFileOperationResponse:
        """复制目录到容器"""
        self._ensure_client()

        try:
            # 获取容器
            container = self.client.containers.get(container_id)

            # 解码base64内容
            tar_content = base64.b64decode(request.archive_base64)

            # 检查容器状态
            container_info = container.attrs
            container_status = container_info["State"]["Status"]
            was_running = container_status == "running"

            logger.info(f"容器 {container_id} 当前状态: {container_status}")

            # 如果容器未运行，先启动容器
            if not was_running:
                logger.info(f"容器未运行，启动容器以执行完整替换")
                try:
                    container.start()
                    logger.info(f"容器 {container_id} 启动成功")

                    # 等待容器启动完成
                    import time

                    # 3次重试机制
                    for _ in range(3):
                        time.sleep(2)
                        # 重新获取容器状态
                        container.reload()
                        if container.attrs["State"]["Status"] == "running":
                            break
                        logger.info(f"等待容器 {container_id} 启动...")

                    if container.attrs["State"]["Status"] != "running":
                        raise Exception(
                            f"容器启动后状态异常: {container.attrs["State"]["Status"]}"
                        )

                except Exception as e:
                    logger.error(f"启动容器失败: {e}")
                    return ContainerFileOperationResponse(
                        success=False,
                        container_id=container_id,
                        message=f"启动容器失败: {str(e)}",
                        operation="copy_directory",
                        file_path=request.container_path,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )

            # 删除现有目录以确保完整替换
            if request.remove_existing:
                try:
                    logger.info(f"删除现有目录: {request.container_path}")
                    result = container.exec_run(f"rm -rf {request.container_path}")
                    if result.exit_code == 0:
                        logger.info(f"成功删除目录: {request.container_path}")
                    else:
                        logger.warning(
                            f"删除目录失败，退出码: {result.exit_code}, 输出: {result.output}"
                        )
                except Exception as e:
                    logger.error(f"删除目录时发生异常: {e}")
                    return ContainerFileOperationResponse(
                        success=False,
                        container_id=container_id,
                        message=f"删除现有目录失败: {str(e)}",
                        operation="copy_directory",
                        file_path=request.container_path,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )

            # 复制新内容
            parent_dir = os.path.dirname(request.container_path)
            if not parent_dir:
                parent_dir = "/"

            container.put_archive(parent_dir, tar_content)

            operation_type = "完整替换" if request.remove_existing else "合并更新"
            startup_info = " (已自动启动容器)" if not was_running else ""

            logger.info(
                f"成功复制目录到容器 {container_id}:{request.container_path} ({operation_type})"
            )

            return ContainerFileOperationResponse(
                success=True,
                container_id=container_id,
                message=f"目录{operation_type}成功: {request.container_path}{startup_info}",
                operation="copy_directory",
                file_path=request.container_path,
                file_size=len(tar_content),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        except NotFound:
            error_msg = f"容器 {container_id} 不存在"
            logger.error(error_msg)
            return ContainerFileOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="copy_directory",
                file_path=request.container_path,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            error_msg = f"复制目录失败: {str(e)}"
            logger.error(f"复制目录到容器失败 {container_id}: {e}")
            return ContainerFileOperationResponse(
                success=False,
                container_id=container_id,
                message=error_msg,
                operation="copy_directory",
                file_path=request.container_path,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )


# 全局Docker服务实例
docker_service = DockerService()
