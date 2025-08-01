from minio import Minio
from minio.error import S3Error
from typing import Optional, Dict, Any, BinaryIO, List, Union, Tuple, Mapping
from app.config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class MinIOService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def ensure_bucket_exists(self, bucket_name: str) -> None:
        """确保存储桶存在"""

        def _check_bucket():
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

                # 设置桶策略（允许公开读取公共文件）
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/public/*"],
                        }
                    ],
                }

                import json

                self.client.set_bucket_policy(bucket_name, json.dumps(policy))

        await asyncio.get_event_loop().run_in_executor(self.executor, _check_bucket)

    async def upload_file(
        self,
        bucket_name: str,
        object_key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Mapping[str, Union[str, List[str], Tuple[str]]]] = None,
    ) -> Dict[str, Any]:
        """上传文件"""
        await self.ensure_bucket_exists(bucket_name)
        metadata = dict(metadata) if metadata else {}

        def _upload():
            from io import BytesIO

            file_stream = BytesIO(file_data)
            file_size = len(file_data)

            # 计算文件哈希
            file_hash = hashlib.sha256(file_data).hexdigest()

            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=file_stream,
                length=file_size,
                content_type=content_type or "application/octet-stream",
                metadata=metadata,
            )

            return {
                "bucket": bucket_name,
                "object_key": object_key,
                "etag": result.etag,
                "size": file_size,
                "hash": file_hash,
                "content_type": content_type,
            }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _upload)

    async def upload_file_stream(
        self,
        bucket_name: str,
        object_key: str,
        file_stream: BinaryIO,
        file_size: int,
        content_type: Optional[str] = None,
        metadata: Optional[Mapping[str, Union[str, List[str], Tuple[str]]]] = None,
    ) -> Dict[str, Any]:
        """上传文件流"""
        await self.ensure_bucket_exists(bucket_name)
        metadata = dict(metadata) if metadata else {}

        def _upload():
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=file_stream,
                length=file_size,
                content_type=content_type or "application/octet-stream",
                metadata=metadata,
            )

            return {
                "bucket": bucket_name,
                "object_key": object_key,
                "etag": result.etag,
                "size": file_size,
                "content_type": content_type or "application/octet-stream",
            }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _upload)

    async def get_download_url(
        self, bucket_name: str, object_key: str, expires: int = 3600
    ) -> str:
        """获取预签名下载URL"""

        def _get_url():
            return self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_key,
                expires=timedelta(seconds=expires),
            )

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_url)

    async def get_upload_url(
        self, bucket_name: str, object_key: str, expires: int = 3600
    ) -> str:
        """获取预签名上传URL"""
        await self.ensure_bucket_exists(bucket_name)

        def _get_url():
            return self.client.presigned_put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                expires=timedelta(seconds=expires),
            )

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_url)

    async def delete_file(self, bucket_name: str, object_key: str) -> None:
        """删除文件"""

        def _delete():
            self.client.remove_object(bucket_name, object_key)

        await asyncio.get_event_loop().run_in_executor(self.executor, _delete)

    async def list_files(
        self, bucket_name: str, prefix: Optional[str] = None, recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """列出文件"""

        def _list():
            objects = self.client.list_objects(
                bucket_name=bucket_name, prefix=prefix, recursive=recursive
            )

            files = []
            for obj in objects:
                files.append(
                    {
                        "object_key": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                        "content_type": obj.content_type,
                    }
                )

            return files

        return await asyncio.get_event_loop().run_in_executor(self.executor, _list)

    async def get_file_info(
        self, bucket_name: str, object_key: str
    ) -> Optional[Dict[str, Any]]:
        """获取文件信息"""

        def _get_info():
            try:
                stat = self.client.stat_object(bucket_name, object_key)
                return {
                    "object_key": object_key,
                    "size": stat.size,
                    "last_modified": stat.last_modified,
                    "etag": stat.etag,
                    "content_type": stat.content_type,
                    "metadata": stat.metadata,
                }
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return None
                raise

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_info)

    async def copy_file(
        self, source_bucket: str, source_object: str, dest_bucket: str, dest_object: str
    ) -> Dict[str, Any]:
        """复制文件"""
        await self.ensure_bucket_exists(dest_bucket)

        def _copy():
            from minio.commonconfig import CopySource

            result = self.client.copy_object(
                bucket_name=dest_bucket,
                object_name=dest_object,
                source=CopySource(source_bucket, source_object),
            )

            return {
                "source_bucket": source_bucket,
                "source_object": source_object,
                "dest_bucket": dest_bucket,
                "dest_object": dest_object,
                "etag": result.etag,
            }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _copy)

    async def check_health(self) -> Dict[str, Any]:
        """检查MinIO服务健康状态"""

        def _check():
            try:
                # 尝试列出存储桶来检查连接
                buckets = list(self.client.list_buckets())

                # 获取存储信息（如果支持）
                bucket_count = len(buckets)

                return {
                    "healthy": True,
                    "bucket_count": bucket_count,
                    "buckets": [bucket.name for bucket in buckets],
                    "error": None,
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "bucket_count": 0,
                    "buckets": [],
                    "error": str(e),
                }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _check)

    async def create_multipart_upload(
        self, bucket_name: str, object_key: str, content_type: Optional[str] = None
    ) -> str:
        """创建分片上传"""
        await self.ensure_bucket_exists(bucket_name)

        def _create():
            result = self.client._create_multipart_upload(
                bucket_name=bucket_name,
                object_name=object_key,
                headers={} if not content_type else {"Content-Type": content_type},
            )

            # Handle both dict and string return types
            if isinstance(result, dict):
                return result.get("UploadId") or ""
            else:
                return str(result)

        return await asyncio.get_event_loop().run_in_executor(self.executor, _create)

    async def upload_part(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
        part_number: int,
        data: bytes,
    ) -> str:
        """上传分片"""

        def _upload():
            result = self.client._upload_part(
                bucket_name=bucket_name,
                object_name=object_key,
                upload_id=upload_id,
                part_number=part_number,
                data=data,
                headers={},
            )

            # Handle both object and string return types
            if hasattr(result, 'etag'):
                return getattr(result, 'etag', "")
            else:
                return str(result)

        return await asyncio.get_event_loop().run_in_executor(self.executor, _upload)

    async def complete_multipart_upload(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
        parts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """完成分片上传"""

        def _complete():
            from minio.datatypes import Part

            part_list = []
            for part in parts:
                part_list.append(Part(part["part_number"], part["etag"]))

            result = self.client._complete_multipart_upload(
                bucket_name=bucket_name,
                object_name=object_key,
                upload_id=upload_id,
                parts=part_list,
            )

            return {
                "bucket": bucket_name,
                "object_key": object_key,
                "etag": result.etag,
                "location": result.location,
            }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _complete)

    async def abort_multipart_upload(
        self, bucket_name: str, object_key: str, upload_id: str
    ) -> None:
        """取消分片上传"""

        def _abort():
            self.client._abort_multipart_upload(
                bucket_name=bucket_name, object_name=object_key, upload_id=upload_id
            )

        await asyncio.get_event_loop().run_in_executor(self.executor, _abort)

    async def get_file_content(self, bucket_name: str, object_key: str) -> bytes:
        """获取文件内容"""
        def _get_content():
            try:
                response = self.client.get_object(bucket_name, object_key)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise FileNotFoundError(f"File not found: {object_key}")
                raise

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_content)

    async def get_file_stream(self, bucket_name: str, object_key: str):
        """获取文件流"""
        def _get_stream():
            try:
                return self.client.get_object(bucket_name, object_key)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise FileNotFoundError(f"File not found: {object_key}")
                raise

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_stream)

    async def file_exists(self, bucket_name: str, object_key: str) -> bool:
        """检查文件是否存在"""
        def _check():
            try:
                self.client.stat_object(bucket_name, object_key)
                return True
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return False
                raise

        return await asyncio.get_event_loop().run_in_executor(self.executor, _check)

    async def get_bucket_usage(self, bucket_name: str) -> Dict[str, Any]:
        """获取存储桶使用情况"""
        def _get_usage():
            try:
                objects = list(self.client.list_objects(bucket_name, recursive=True))
                total_size = sum(obj.size or 0 for obj in objects)
                total_files = len(objects)
                
                return {
                    "bucket": bucket_name,
                    "total_files": total_files,
                    "total_size": total_size,
                    "files": [{
                        "object_key": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified
                    } for obj in objects[:100]]  # 限制返回前100个文件
                }
            except Exception as e:
                return {
                    "bucket": bucket_name,
                    "total_files": 0,
                    "total_size": 0,
                    "files": [],
                    "error": str(e)
                }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_usage)

    async def cleanup_orphaned_files(self, bucket_name: str, valid_object_keys: List[str]) -> Dict[str, Any]:
        """清理孤儿文件（数据库中不存在但MinIO中存在的文件）"""
        def _cleanup():
            try:
                all_objects = list(self.client.list_objects(bucket_name, recursive=True))
                orphaned_objects = []
                cleaned_size = 0
                
                for obj in all_objects:
                    if obj.object_name not in valid_object_keys:
                        orphaned_objects.append(obj.object_name)
                        cleaned_size += obj.size or 0
                        
                # 删除孤儿文件
                for obj_key in orphaned_objects:
                    self.client.remove_object(bucket_name, obj_key)
                
                return {
                    "cleaned_files": len(orphaned_objects),
                    "cleaned_size": cleaned_size,
                    "orphaned_files": orphaned_objects[:50]  # 只返回前50个
                }
            except Exception as e:
                return {
                    "cleaned_files": 0,
                    "cleaned_size": 0,
                    "orphaned_files": [],
                    "error": str(e)
                }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _cleanup)

# 创建全局MinIO服务实例
minio_service = MinIOService()
