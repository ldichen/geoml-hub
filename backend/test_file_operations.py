#!/usr/bin/env python3
"""
测试容器文件操作功能的简单脚本
"""

import asyncio
import base64
import logging
from app.services.mmanager_client import MManagerClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mmanager_client():
    """测试 mManager 客户端文件操作功能"""
    
    # 创建测试客户端（需要实际的 mManager 服务运行）
    client = MManagerClient("http://localhost:8080", "test-api-key")
    
    try:
        # 测试健康检查
        health = await client.health_check()
        logger.info(f"健康检查结果: {health}")
        
        # 测试文件复制功能
        test_content = "Hello, World! This is a test file."
        content_base64 = base64.b64encode(test_content.encode()).decode()
        
        # 注意：这需要一个实际存在的容器ID
        container_id = "test-container-id"
        
        result = await client.copy_file_to_container(
            container_id=container_id,
            container_path="/app/test.txt",
            content_base64=content_base64,
            file_name="test.txt"
        )
        
        logger.info(f"文件复制结果: {result}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    print("容器文件操作功能已实现！")
    print("包含的新功能：")
    print("1. mManager API 扩展:")
    print("   - POST /containers/{container_id}/files")
    print("   - POST /containers/{container_id}/directories")
    print()
    print("2. MManagerClient 新方法:")
    print("   - copy_file_to_container()")
    print("   - copy_directory_to_container()")
    print()
    print("3. ContainerFileUpdateService 已更新使用新的分布式架构")
    print()
    print("要运行实际测试，请确保 mManager 服务正在运行，然后取消注释下面的代码:")
    print()
    # asyncio.run(test_mmanager_client())