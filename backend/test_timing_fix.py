#!/usr/bin/env python3
"""
测试异步时序问题修复
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings

async def test_timing_fix():
    """测试异步时序问题修复"""
    print("=== 测试异步时序问题修复 ===")
    
    try:
        # 获取数据库连接
        async for db in get_async_db():
            # 初始化mManager
            if not mmanager_client.controllers:
                await mmanager_client.initialize(db)
            
            # 获取控制器
            controllers_status = await mmanager_client.get_controller_status(db)
            controllers_list = controllers_status.get('controllers', [])
            
            if not controllers_list:
                print("❌ 没有可用的控制器")
                return
            
            controller_id = controllers_list[0]['id']
            print(f"使用控制器: {controller_id}")
            
            # 准备测试数据
            test_image = f"{settings.harbor_url.split('://')[-1]}/geoml-hub/redis-7-1:latest"
            harbor_auth = {
                "serveraddress": str(settings.harbor_url.split('://')[-1]),
                "username": str(settings.harbor_username),
                "password": str(settings.harbor_password)
            }
            
            print(f"测试镜像: {test_image}")
            
            # 测试改进后的ensure_image_available方法
            print(f"\n=== 测试改进后的镜像可用性检查 ===")
            try:
                start_time = asyncio.get_event_loop().time()
                
                image_available = await mmanager_client.ensure_image_available(
                    controller_id, test_image, harbor_auth
                )
                
                end_time = asyncio.get_event_loop().time()
                elapsed = end_time - start_time
                
                if image_available:
                    print(f"✅ 镜像可用性检查成功，耗时: {elapsed:.2f}秒")
                else:
                    print(f"❌ 镜像可用性检查失败，耗时: {elapsed:.2f}秒")
                    
            except Exception as e:
                print(f"❌ 镜像可用性检查异常: {e}")
                
            # 测试Harbor客户端镜像检查（模拟services.py中的等待逻辑）
            print(f"\n=== 测试Harbor镜像可用性检查 ===")
            try:
                from app.services.harbor_client import HarborClient
                
                harbor_project = settings.harbor_default_project
                # 从完整镜像名解析出repository路径
                # 格式: 172.21.252.230/geoml-hub/redis-7-1:latest
                # 需要提取: redis-7-1
                image_parts = test_image.split('/')
                if len(image_parts) >= 3:
                    repository_path = image_parts[-1].split(':')[0]  # redis-7-1
                else:
                    repository_path = test_image.split(':')[0]
                
                print(f"Harbor项目: {harbor_project}")
                print(f"Harbor仓库路径: {repository_path}")
                
                async with HarborClient() as harbor:
                    artifact = await harbor.get_artifact(
                        project_name=harbor_project,
                        repository_name=repository_path,
                        tag="latest"
                    )
                    
                    if artifact and artifact.get("digest"):
                        print(f"✅ Harbor镜像可用，digest: {artifact.get('digest')[:12]}...")
                    else:
                        print(f"❌ Harbor镜像不可用或未找到")
                        
            except Exception as e:
                print(f"❌ Harbor镜像检查失败: {e}")
            
            print(f"\n✅ 异步时序问题修复测试完成！")
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_timing_fix())