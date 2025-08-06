#!/usr/bin/env python3
"""
逐步调试mManager的每个API调用
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings

async def debug_step_by_step():
    """逐步调试每个操作"""
    print("=== 逐步调试mManager API调用 ===")
    
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
            print(f"Harbor认证: {harbor_auth}")
            
            # 步骤1: 测试get_image_info
            print(f"\n=== 步骤1: 测试get_image_info ===")
            try:
                image_info = await mmanager_client.get_image_info(controller_id, test_image)
                print(f"✅ get_image_info成功: {image_info}")
            except Exception as e:
                print(f"❌ get_image_info失败: {e}")
                if "Invalid variable type" in str(e):
                    print("这是导致Invalid variable type错误的调用！")
                    return
            
            # 步骤2: 测试pull_image（如果镜像不存在）
            print(f"\n=== 步骤2: 测试pull_image ===")
            try:
                pull_result = await mmanager_client.pull_image(controller_id, test_image, harbor_auth)
                print(f"✅ pull_image成功: {pull_result}")
            except Exception as e:
                print(f"❌ pull_image失败: {e}")
                if "Invalid variable type" in str(e):
                    print("这是导致Invalid variable type错误的调用！")
                    return
            
            # 步骤3: 测试ensure_image_available（完整流程）
            print(f"\n=== 步骤3: 测试ensure_image_available ===")
            try:
                image_available = await mmanager_client.ensure_image_available(
                    controller_id, test_image, harbor_auth
                )
                print(f"✅ ensure_image_available成功: {image_available}")
            except Exception as e:
                print(f"❌ ensure_image_available失败: {e}")
                if "Invalid variable type" in str(e):
                    print("这是导致Invalid variable type错误的调用！")
                    # 进一步调试
                    print(f"\n=== 调试详细信息 ===")
                    print(f"controller_id类型: {type(controller_id).__name__}, 值: {repr(controller_id)}")
                    print(f"test_image类型: {type(test_image).__name__}, 值: {repr(test_image)}")
                    print(f"harbor_auth类型: {type(harbor_auth).__name__}")
                    for key, value in harbor_auth.items():
                        print(f"  {key}类型: {type(value).__name__}, 值: {repr(value)}")
                    return
            
            print(f"\n✅ 所有测试都成功完成！")
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_step_by_step())