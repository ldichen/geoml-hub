#!/usr/bin/env python3
"""
调试Harbor认证问题
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings

async def debug_harbor_auth():
    """调试Harbor认证配置"""
    print("=== 调试Harbor认证配置 ===")
    
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
            
            # 准备Harbor认证信息
            print("\n=== Harbor配置检查 ===")
            print(f"Harbor URL: {settings.harbor_url}")
            print(f"Harbor Username: {settings.harbor_username}")
            print(f"Harbor Password: {'*' * len(settings.harbor_password)}")
            
            # 构建认证配置
            harbor_auth = {
                "serveraddress": str(settings.harbor_url.split('://')[-1]),
                "username": str(settings.harbor_username),
                "password": str(settings.harbor_password)
            }
            
            print(f"\n=== 认证配置 ===")
            for key, value in harbor_auth.items():
                print(f"{key}: {value} (type: {type(value).__name__})")
            
            # 测试镜像名称
            test_image = f"{settings.harbor_url.split('://')[-1]}/geoml-hub/redis-7-1:latest"
            print(f"\n测试镜像: {test_image}")
            
            # 测试拉取镜像（单独测试pull_image方法）
            print(f"\n=== 测试直接拉取镜像 ===")
            try:
                pull_result = await mmanager_client.pull_image(controller_id, test_image, harbor_auth)
                print(f"拉取结果: {pull_result}")
            except Exception as e:
                print(f"❌ 直接拉取失败: {e}")
                
                # 如果是变量类型错误，分析错误详情
                if "Invalid variable type" in str(e):
                    print("\n=== 检查所有配置值的类型 ===")
                    
                    # 检查镜像名称
                    print(f"test_image类型: {type(test_image).__name__}, 值: {test_image}")
                    
                    # 检查认证配置的每个值
                    for key, value in harbor_auth.items():
                        print(f"harbor_auth[{key}]类型: {type(value).__name__}, 值: {repr(value)}")
                    
                    # 检查settings中的原始值
                    print(f"\n=== 原始配置值类型 ===")
                    print(f"settings.harbor_url类型: {type(settings.harbor_url).__name__}")
                    print(f"settings.harbor_username类型: {type(settings.harbor_username).__name__}")
                    print(f"settings.harbor_password类型: {type(settings.harbor_password).__name__}")
                    
                    # 检查是否有其他配置项
                    print(f"\n=== 检查其他Harbor相关配置 ===")
                    for attr in dir(settings):
                        if 'harbor' in attr.lower():
                            value = getattr(settings, attr)
                            print(f"settings.{attr}: {repr(value)} (type: {type(value).__name__})")
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_harbor_auth())