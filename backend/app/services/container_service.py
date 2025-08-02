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
        更新服务文件
        
        Args:
            db: 数据库会话
            service_id: 服务ID
            file_updates: 文件更新映射 {file_type: UploadFile}
            user_id: 用户ID
            
        Returns:
            更新结果字典
        """
        # 获取服务信息
        service = await self._get_service_by_id(db, service_id)
        
        # 检查权限
        if service.user_id != user_id:
            raise PermissionError("无权限操作此服务")
            
        # 检查容器是否存在
        if not service.container_id:
            raise ValueError("服务容器不存在，无法更新文件")
            
        update_results = {}
        container_needs_restart = False
        
        try:
            # 创建临时工作目录
            with tempfile.TemporaryDirectory() as work_dir:
                # 处理每个文件更新
                for file_type, file_obj in file_updates.items():
                    try:
                        if file_type in ['gogogo', 'mc_config']:
                            # 处理单文件更新
                            result = await self._handle_single_file_update(
                                service, file_obj, file_type, work_dir
                            )
                            container_needs_restart = True
                        elif file_type in ['model', 'examples']:
                            # 处理目录压缩包更新
                            result = await self._handle_directory_update(
                                service, file_obj, file_type, work_dir
                            )
                            container_needs_restart = True
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
                        
            # 如果有成功的更新，重启容器
            if container_needs_restart and any(r.get('success') for r in update_results.values()):
                restart_result = await self._restart_container_and_verify(db, service, user_id)
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
            
    async def _handle_single_file_update(
        self,
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
            
    async def _copy_file_to_container(self, container_id: str, host_path: str, container_path: str):
        """复制文件到容器"""
        
        if not self.service_manager.docker_client:
            raise RuntimeError("Docker客户端未初始化")
            
        try:
            container = self.service_manager.docker_client.containers.get(container_id)
            
            # 创建tar包并复制到容器
            with open(host_path, 'rb') as f:
                container.put_archive(
                    os.path.dirname(container_path),
                    self._create_tar_archive(os.path.basename(container_path), f.read())
                )
                
        except Exception as e:
            raise RuntimeError(f"复制文件到容器失败: {str(e)}")
            
    async def _copy_directory_to_container(self, container_id: str, host_dir: str, container_path: str):
        """复制目录到容器"""
        
        if not self.service_manager.docker_client:
            raise RuntimeError("Docker客户端未初始化")
            
        try:
            container = self.service_manager.docker_client.containers.get(container_id)
            
            # 先删除容器中的目标目录
            try:
                container.exec_run(f"rm -rf {container_path}")
            except:
                pass  # 忽略删除失败
                
            # 创建tar包并复制到容器
            tar_data = self._create_directory_tar_archive(host_dir)
            container.put_archive(os.path.dirname(container_path), tar_data)
            
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