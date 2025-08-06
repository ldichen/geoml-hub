#!/usr/bin/env python3
"""
测试拉取镜像后的检查问题
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings
from app.utils.logger import setup_logging, set_docker_operations_quiet

# 设置日志，减少Docker删除信息
setup_logging()
set_docker_operations_quiet()

async def test_image_check_after_pull():
    """测试拉取镜像后的检查"""
    print("=== 测试拉取镜像后的检查 ===")
    
    try:
        # 获取数据库连接
        async for db in get_async_db():
            # 初始化mManager
            if not mmanager_client.controllers:
                await mmanager_client.initialize(db)
            
            # 获取控制器
            controllers_status = await mmanager_client.get_controller_status(db)
            controllers_list = controllers_status.get('controllers', [])
            controller_id = controllers_list[0]['id']
            
            # 准备测试数据
            test_image = f"{settings.harbor_url.split('://')[-1]}/geoml-hub/redis-7-1:latest"
            harbor_auth = {
                "serveraddress": str(settings.harbor_url.split('://')[-1]),
                "username": str(settings.harbor_username),
                "password": str(settings.harbor_password)
            }
            
            print(f"测试镜像: {test_image}")
            
            # 步骤1: 智能镜像管理 - 先检查后删除
            print("=== 智能镜像管理策略 ===")
            image_exists = False
            try:
                image_info = await mmanager_client.get_image_info(controller_id, test_image)
                if image_info:
                    image_exists = True
                    print(f"✅ 发现已存在镜像，准备清理: {test_image}")
                    remove_result = await mmanager_client.remove_image(controller_id, test_image)
                    print(f"删除结果: {'成功' if remove_result else '失败'}")
                else:
                    print(f"ℹ️  镜像不存在，无需删除: {test_image}")
            except Exception as e:
                print(f"ℹ️  镜像检查失败（可能不存在），跳过删除: {e}")
            
            # 等待一下
            if image_exists:
                await asyncio.sleep(2)
                print("等待Docker清理完成...")
            
            # 步骤2: 检查镜像是否存在（应该不存在）
            print(f"\n=== 删除后检查镜像 ===")
            try:
                image_info = await mmanager_client.get_image_info(controller_id, test_image)
                print(f"❌ 意外：删除后镜像仍存在: {image_info}")
            except Exception as e:
                print(f"✅ 确认：删除后镜像不存在: {e}")
            
            # 步骤3: 拉取镜像
            print(f"\n=== 拉取镜像 ===")
            pull_result = await mmanager_client.pull_image(controller_id, test_image, harbor_auth)
            print(f"拉取结果: {pull_result}")
            
            if pull_result.get("status") != "success":
                print("❌ 拉取失败，停止测试")
                return
            
            # 步骤4: 立即检查镜像（应该存在）
            print(f"\n=== 拉取后立即检查镜像 ===")
            try:
                image_info = await mmanager_client.get_image_info(controller_id, test_image)
                print(f"✅ 拉取后镜像存在: {image_info}")
            except Exception as e:
                print(f"❌ 问题：拉取后镜像检查失败: {e}")
            
            # 步骤5: 等待几秒后再次检查
            print(f"\n=== 等待5秒后再次检查镜像 ===")
            await asyncio.sleep(5)
            try:
                image_info = await mmanager_client.get_image_info(controller_id, test_image)
                print(f"✅ 等待后镜像存在: {image_info}")
            except Exception as e:
                print(f"❌ 问题：等待后镜像检查仍失败: {e}")
            
            # 步骤6: 尝试直接调用mManager API
            print(f"\n=== 直接检查mManager镜像列表 ===")
            try:
                client = mmanager_client.get_client(controller_id)
                containers_result = await client._request("GET", "/images/")
                print(f"所有镜像: {containers_result}")
                
                # 查找我们的镜像
                images = containers_result.get('images', [])
                found_image = None
                for img in images:
                    repo_tags = img.get('repository_tags', [])
                    if test_image in repo_tags:
                        found_image = img
                        break
                
                if found_image:
                    print(f"✅ 在镜像列表中找到目标镜像: {found_image}")
                else:
                    print(f"❌ 在镜像列表中未找到目标镜像")
                    print(f"镜像列表中的所有标签:")
                    for img in images:
                        print(f"  - {img.get('repository_tags', [])}")
                        
            except Exception as e:
                print(f"❌ 获取镜像列表失败: {e}")
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_check_after_pull())