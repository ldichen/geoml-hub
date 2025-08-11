"""
容器文件管理服务

该模块提供Docker容器文件更新功能：
- 处理gogogo.py、mc.json单文件更新
- 处理model/和examples/目录压缩包更新
- 自动解压和嵌套目录检测
- 容器重启和健康检查
"""

import os
import shutil
import zipfile
import tarfile
import tempfile
import asyncio
import logging
from typing import Dict, Optional, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.service import ModelService
from app.schemas.service import ServiceStatus, HealthStatus
from app.services.model_service import service_manager
from app.services.mmanager_client import mmanager_client

logger = logging.getLogger(__name__)


class ContainerFileUpdateService:
    """容器文件更新服务"""
    
    def __init__(self):
        self.service_manager = service_manager
        self.supported_archives = {'.zip', '.tar', '.tar.gz', '.tgz'}
        self.container_base_path = "/app"  # 容器内基础路径
        
    async def update_service_files(
        self,
        db: AsyncSession,
        service_id: int,
        file_updates: Dict[str, UploadFile],
        user_id: int
    ) -> Dict[str, Any]:
        """
        更新服务文件 - 优化版：分离数据库操作和长时间文件操作
        
        Args:
            db: 数据库会话
            service_id: 服务ID
            file_updates: 文件更新映射 {file_type: UploadFile}
            user_id: 用户ID
            
        Returns:
            更新结果字典
        """
        try:
            # 第一阶段：快速获取必要信息，然后释放数据库连接压力
            service_info = await self._get_service_info_for_update(db, service_id, user_id)
            
            # 第二阶段：执行长时间的文件操作（不持有数据库连接）
            update_results = await self._perform_file_operations(service_info, file_updates)
            
            # 第三阶段：如果需要重启，重新获取数据库会话进行容器重启
            container_needs_restart = any(r.get('success') for r in update_results.values())
            if container_needs_restart:
                restart_result = await self._restart_container_with_fresh_session(
                    service_id, user_id
                )
                update_results['container_restart'] = restart_result
                
            return {
                'service_id': service_id,
                'updates': update_results,
                'container_restarted': container_needs_restart,
                'overall_success': all(r.get('success', False) for r in update_results.values())
            }
            
        except Exception as e:
            logger.error(f"更新服务 {service_id} 文件失败: {e}")
            raise RuntimeError(f"文件更新失败: {str(e)}")

    async def _get_service_info_for_update(
        self, db: AsyncSession, service_id: int, user_id: int
    ) -> Dict[str, Any]:
        """获取文件更新所需的服务信息"""
        try:
            service = await self._get_service_by_id(db, service_id)
            
            # 检查权限
            if service.user_id != user_id:
                raise PermissionError("无权限操作此服务")
                
            # 检查容器是否存在
            if not service.container_id:
                raise ValueError("服务容器不存在，无法更新文件")
            
            # 获取容器位置信息
            location = await mmanager_client.find_container_location(db, service.container_id)
            if not location:
                raise ValueError(f"无法找到容器 {service.container_id} 的位置")
            
            # 返回后续操作需要的最小信息集
            return {
                'service_id': service.id,
                'container_id': service.container_id,
                'controller_id': location["controller_id"],
                'user_id': user_id,
                'status': service.status
            }
            
        except Exception as e:
            logger.error(f"获取服务信息失败: {e}")
            raise

    async def _perform_file_operations(
        self, service_info: Dict[str, Any], file_updates: Dict[str, UploadFile]
    ) -> Dict[str, Any]:
        """执行文件操作 - 不需要数据库连接"""
        update_results = {}
        
        try:
            # 创建临时工作目录
            with tempfile.TemporaryDirectory() as work_dir:
                # 处理每个文件更新
                for file_type, file_obj in file_updates.items():
                    try:
                        if file_type in ['gogogo', 'mc_config']:
                            # 处理单文件更新
                            result = await self._handle_single_file_update_no_db(
                                service_info, file_obj, file_type, work_dir
                            )
                        elif file_type in ['model', 'examples']:
                            # 处理目录压缩包更新
                            result = await self._handle_directory_update_no_db(
                                service_info, file_obj, file_type, work_dir
                            )
                        else:
                            result = {
                                'success': False,
                                'error': f'不支持的文件类型: {file_type}'
                            }
                            
                        update_results[file_type] = result
                        
                    except Exception as e:
                        logger.error(f"更新文件 {file_type} 失败: {e}")
                        update_results[file_type] = {
                            'success': False,
                            'error': str(e)
                        }
                        
            return update_results
            
        except Exception as e:
            logger.error(f"执行文件操作失败: {e}")
            raise

    async def _handle_single_file_update_no_db(
        self,
        service_info: Dict[str, Any],
        file_obj: UploadFile,
        file_type: str,
        work_dir: str
    ) -> Dict[str, Any]:
        """处理单文件更新 - 无数据库依赖版本"""
        
        # 文件类型映射
        file_mapping = {
            'gogogo': 'gogogo.py',
            'mc_config': 'mc.json'
        }
        
        if file_type not in file_mapping:
            raise ValueError(f"不支持的文件类型: {file_type}")
            
        target_filename = file_mapping[file_type]
        
        try:
            # 读取文件内容
            content = await file_obj.read()
            
            # 验证文件内容
            if file_type == 'gogogo':
                await self._validate_python_file(content)
            elif file_type == 'mc_config':
                await self._validate_json_file(content)
                
            # 复制文件到容器
            temp_file_path = os.path.join(work_dir, target_filename)
            with open(temp_file_path, 'wb') as f:
                f.write(content)
                
            # 复制到容器内
            await self._copy_file_to_container_no_db(
                service_info,
                temp_file_path,
                f"{self.container_base_path}/{target_filename}"
            )
            
            logger.info(f"成功更新服务 {service_info['service_id']} 的文件 {target_filename}")
            return {
                'success': True,
                'file_name': target_filename,
                'file_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"更新文件 {file_type} 失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _handle_directory_update_no_db(
        self,
        service_info: Dict[str, Any],
        file_obj: UploadFile,
        dir_type: str,
        work_dir: str
    ) -> Dict[str, Any]:
        """处理目录压缩包更新 - 无数据库依赖版本"""
        
        if dir_type not in ['model', 'examples']:
            raise ValueError(f"不支持的目录类型: {dir_type}")
            
        try:
            # 创建临时解压目录
            extract_dir = os.path.join(work_dir, f"extract_{dir_type}")
            os.makedirs(extract_dir, exist_ok=True)
            
            # 保存上传的压缩包
            archive_path = os.path.join(work_dir, file_obj.filename)
            content = await file_obj.read()
            with open(archive_path, 'wb') as f:
                f.write(content)
                
            # 解压文件
            await self._extract_archive(archive_path, extract_dir)
            
            # 查找实际内容目录（处理嵌套问题）
            actual_content_dir = await self._find_actual_content_dir(extract_dir, dir_type)
            
            # 验证目录内容
            if dir_type == 'model':
                await self._validate_model_directory(actual_content_dir)
            elif dir_type == 'examples':
                await self._validate_examples_directory(actual_content_dir)
                
            # 复制目录到容器
            container_target_path = f"{self.container_base_path}/{dir_type}"
            await self._copy_directory_to_container_no_db(
                service_info,
                actual_content_dir,
                container_target_path
            )
            
            # 统计文件数量
            file_count = sum(len(files) for _, _, files in os.walk(actual_content_dir))
            
            logger.info(f"成功更新服务 {service_info['service_id']} 的目录 {dir_type}，包含 {file_count} 个文件")
            return {
                'success': True,
                'directory_name': dir_type,
                'file_count': file_count,
                'archive_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"更新目录 {dir_type} 失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _copy_file_to_container_no_db(
        self, service_info: Dict[str, Any], host_path: str, container_path: str
    ):
        """复制文件到容器 - 无数据库依赖版本"""
        
        try:
            import base64
            
            # 读取文件内容并编码为base64
            with open(host_path, 'rb') as f:
                file_content = f.read()
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            file_name = os.path.basename(container_path)
            
            # 使用mManager客户端复制文件
            controller_client = mmanager_client.get_client(service_info["controller_id"])
            result = await controller_client.copy_file_to_container(
                service_info["container_id"], container_path, content_base64, file_name
            )
            
            if not result.get("success", False):
                raise RuntimeError(f"文件复制失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            raise RuntimeError(f"复制文件到容器失败: {str(e)}")

    async def _copy_directory_to_container_no_db(
        self, service_info: Dict[str, Any], host_dir: str, container_path: str
    ):
        """复制目录到容器 - 无数据库依赖版本"""
        
        try:
            import base64
            
            # 创建tar包并编码为base64
            tar_data = self._create_directory_tar_archive(host_dir)
            archive_base64 = base64.b64encode(tar_data).decode('utf-8')
            
            # 使用mManager客户端复制目录
            controller_client = mmanager_client.get_client(service_info["controller_id"])
            result = await controller_client.copy_directory_to_container(
                service_info["container_id"], container_path, archive_base64, remove_existing=True
            )
            
            if not result.get("success", False):
                raise RuntimeError(f"目录复制失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            raise RuntimeError(f"复制目录到容器失败: {str(e)}")

    async def _restart_container_with_fresh_session(
        self, service_id: int, user_id: int
    ) -> Dict[str, Any]:
        """使用新的数据库会话重启容器"""
        from app.database import get_db
        
        try:
            # 获取新的数据库会话
            async with get_db() as fresh_db:
                service = await self._get_service_by_id(fresh_db, service_id)
                result = await self._restart_container_and_verify(fresh_db, service, user_id)
                await fresh_db.commit()  # 显式提交
                return result
        except Exception as e:
            logger.error(f"重启容器失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def _handle_single_file_update(
        self,
        db: AsyncSession,
        service: ModelService,
        file_obj: UploadFile,
        file_type: str,
        work_dir: str
    ) -> Dict[str, Any]:
        """处理单文件更新"""
        
        # 文件类型映射
        file_mapping = {
            'gogogo': 'gogogo.py',
            'mc_config': 'mc.json'
        }
        
        if file_type not in file_mapping:
            raise ValueError(f"不支持的文件类型: {file_type}")
            
        target_filename = file_mapping[file_type]
        
        try:
            # 读取文件内容
            content = await file_obj.read()
            
            # 验证文件内容
            if file_type == 'gogogo':
                await self._validate_python_file(content)
            elif file_type == 'mc_config':
                await self._validate_json_file(content)
                
            # 复制文件到容器
            temp_file_path = os.path.join(work_dir, target_filename)
            with open(temp_file_path, 'wb') as f:
                f.write(content)
                
            # 复制到容器内
            await self._copy_file_to_container(
                db,
                service.container_id,
                temp_file_path,
                f"{self.container_base_path}/{target_filename}"
            )
            
            logger.info(f"成功更新服务 {service.id} 的文件 {target_filename}")
            return {
                'success': True,
                'file_name': target_filename,
                'file_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"更新文件 {file_type} 失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def _handle_directory_update(
        self,
        db: AsyncSession,
        service: ModelService,
        file_obj: UploadFile,
        dir_type: str,
        work_dir: str
    ) -> Dict[str, Any]:
        """处理目录压缩包更新"""
        
        if dir_type not in ['model', 'examples']:
            raise ValueError(f"不支持的目录类型: {dir_type}")
            
        try:
            # 创建临时解压目录
            extract_dir = os.path.join(work_dir, f"extract_{dir_type}")
            os.makedirs(extract_dir, exist_ok=True)
            
            # 保存上传的压缩包
            archive_path = os.path.join(work_dir, file_obj.filename)
            content = await file_obj.read()
            with open(archive_path, 'wb') as f:
                f.write(content)
                
            # 解压文件
            await self._extract_archive(archive_path, extract_dir)
            
            # 查找实际内容目录（处理嵌套问题）
            actual_content_dir = await self._find_actual_content_dir(extract_dir, dir_type)
            
            # 验证目录内容
            if dir_type == 'model':
                await self._validate_model_directory(actual_content_dir)
            elif dir_type == 'examples':
                await self._validate_examples_directory(actual_content_dir)
                
            # 复制目录到容器
            container_target_path = f"{self.container_base_path}/{dir_type}"
            await self._copy_directory_to_container(
                db,
                service.container_id,
                actual_content_dir,
                container_target_path
            )
            
            # 统计文件数量
            file_count = sum(len(files) for _, _, files in os.walk(actual_content_dir))
            
            logger.info(f"成功更新服务 {service.id} 的目录 {dir_type}，包含 {file_count} 个文件")
            return {
                'success': True,
                'directory_name': dir_type,
                'file_count': file_count,
                'archive_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"更新目录 {dir_type} 失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def _extract_archive(self, archive_path: str, extract_dir: str):
        """解压压缩包"""
        
        filename = os.path.basename(archive_path).lower()
        
        try:
            if filename.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif filename.endswith(('.tar', '.tar.gz', '.tgz')):
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                raise ValueError(f"不支持的压缩格式: {filename}")
                
        except Exception as e:
            raise RuntimeError(f"解压失败: {str(e)}")
            
    async def _find_actual_content_dir(self, extract_dir: str, expected_name: str) -> str:
        """
        递归查找实际内容目录，解决嵌套问题
        
        例如：model.zip 解压后为 model/model/，应返回最内层的 model/ 目录
        """
        current_path = extract_dir
        
        while True:
            contents = os.listdir(current_path)
            
            # 如果只有一个子目录且名称匹配期望名称
            if (len(contents) == 1 and 
                os.path.isdir(os.path.join(current_path, contents[0])) and
                contents[0] == expected_name):
                current_path = os.path.join(current_path, contents[0])
            else:
                # 如果当前目录就是期望的内容目录
                if os.path.basename(current_path) == expected_name:
                    return current_path
                # 或者查找子目录中是否有期望的目录
                for item in contents:
                    item_path = os.path.join(current_path, item)
                    if os.path.isdir(item_path) and item == expected_name:
                        return item_path
                # 如果都不是，返回当前路径（可能是直接解压的内容）
                return current_path
                
    async def _validate_python_file(self, content: bytes):
        """验证Python文件"""
        try:
            # 尝试编译Python代码
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"Python文件语法错误: {str(e)}")
            
    async def _validate_json_file(self, content: bytes):
        """验证JSON文件"""
        import json
        try:
            json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON文件格式错误: {str(e)}")
            
    async def _validate_model_directory(self, model_dir: str):
        """验证模型目录结构"""
        if not os.path.exists(model_dir):
            raise ValueError("模型目录不存在")
            
        # 检查是否包含模型文件（可以根据实际需求调整）
        model_files = []
        for root, dirs, files in os.walk(model_dir):
            for file in files:
                if file.endswith(('.pkl', '.pth', '.h5', '.pb', '.onnx', '.joblib')):
                    model_files.append(file)
                    
        if not model_files:
            logger.warning(f"模型目录 {model_dir} 中未找到常见的模型文件格式")
            
    async def _validate_examples_directory(self, examples_dir: str):
        """验证示例数据目录结构"""
        if not os.path.exists(examples_dir):
            raise ValueError("示例数据目录不存在")
            
        # 检查是否包含数据文件
        data_files = []
        for root, dirs, files in os.walk(examples_dir):
            data_files.extend(files)
            
        if not data_files:
            raise ValueError("示例数据目录为空")
            
    async def _copy_file_to_container(self, db: AsyncSession, container_id: str, host_path: str, container_path: str):
        """复制文件到容器"""
        
        try:
            import base64
            
            # 读取文件内容并编码为base64
            with open(host_path, 'rb') as f:
                file_content = f.read()
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            file_name = os.path.basename(container_path)
            
            # 找到容器所在的控制器
            location = await mmanager_client.find_container_location(db, container_id)
            if not location:
                raise RuntimeError(f"无法找到容器 {container_id} 的位置")
            
            # 使用mManager客户端复制文件
            controller_client = mmanager_client.get_client(location["controller_id"])
            result = await controller_client.copy_file_to_container(
                container_id, container_path, content_base64, file_name
            )
            
            if not result.get("success", False):
                raise RuntimeError(f"文件复制失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            raise RuntimeError(f"复制文件到容器失败: {str(e)}")
            
    async def _copy_directory_to_container(self, db: AsyncSession, container_id: str, host_dir: str, container_path: str):
        """复制目录到容器"""
        
        try:
            import base64
            
            # 创建tar包并编码为base64
            tar_data = self._create_directory_tar_archive(host_dir)
            archive_base64 = base64.b64encode(tar_data).decode('utf-8')
            
            # 找到容器所在的控制器
            location = await mmanager_client.find_container_location(db, container_id)
            if not location:
                raise RuntimeError(f"无法找到容器 {container_id} 的位置")
            
            # 使用mManager客户端复制目录
            controller_client = mmanager_client.get_client(location["controller_id"])
            result = await controller_client.copy_directory_to_container(
                container_id, container_path, archive_base64, remove_existing=True
            )
            
            if not result.get("success", False):
                raise RuntimeError(f"目录复制失败: {result.get('message', '未知错误')}")
                
        except Exception as e:
            raise RuntimeError(f"复制目录到容器失败: {str(e)}")
            
    def _create_tar_archive(self, filename: str, content: bytes) -> bytes:
        """创建单文件tar包"""
        import io
        import tarfile
        
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            info = tarfile.TarInfo(name=filename)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        tar_buffer.seek(0)
        return tar_buffer.read()
        
    def _create_directory_tar_archive(self, directory: str) -> bytes:
        """创建目录tar包"""
        import io
        import tarfile
        
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            tar.add(directory, arcname=os.path.basename(directory))
        tar_buffer.seek(0)
        return tar_buffer.read()
        
    async def _restart_container_and_verify(
        self,
        db: AsyncSession,
        service: ModelService,
        user_id: int
    ) -> Dict[str, Any]:
        """重启容器并验证健康状态"""
        
        try:
            # 停止服务
            await self.service_manager.stop_service(db, service.id, user_id, force_stop=True)
            
            # 等待一秒确保完全停止
            await asyncio.sleep(1)
            
            # 启动服务
            updated_service = await self.service_manager.start_service(
                db, service.id, user_id, force_restart=True
            )
            
            # 等待服务启动完成
            await asyncio.sleep(5)
            
            # 执行健康检查
            health_check = await self.service_manager.perform_health_check(db, service.id)
            
            # 更新服务状态
            service.health_status = health_check.status
            service.error_message = health_check.error_message
            await db.commit()
            
            return {
                'success': True,
                'service_status': updated_service.status,
                'health_status': health_check.status,
                'service_url': updated_service.service_url
            }
            
        except Exception as e:
            # 标记服务为有环境问题
            service.status = ServiceStatus.ERROR
            service.health_status = HealthStatus.UNHEALTHY
            service.error_message = f"容器重启后环境检查失败: {str(e)}"
            await db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'health_status': HealthStatus.UNHEALTHY
            }
            
    async def _get_service_by_id(self, db: AsyncSession, service_id: int) -> ModelService:
        """根据ID获取服务"""
        
        service_query = select(ModelService).where(ModelService.id == service_id)
        result = await db.execute(service_query)
        service = result.scalar_one_or_none()
        
        if not service:
            raise ValueError(f"服务 {service_id} 不存在")
            
        return service


# 创建全局实例
container_file_service = ContainerFileUpdateService()