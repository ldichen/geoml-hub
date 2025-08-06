#!/usr/bin/env python3
"""
测试mManager状态和Docker访问
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db

async def test_mmanager_status():
    """测试mManager状态"""
    print("=== 测试mManager状态 ===")
    
    try:
        # 获取数据库连接
        async for db in get_async_db():
            # 初始化mManager（如果还没有初始化）
            if not mmanager_client.controllers:
                print("初始化mManager控制器管理器...")
                await mmanager_client.initialize(db)
                print(f"控制器管理器已初始化，加载了 {len(mmanager_client.controllers)} 个控制器")
            
            # 获取控制器状态
            controllers_status = await mmanager_client.get_controller_status(db)
            
            if not controllers_status or not controllers_status.get('controllers'):
                print("❌ 没有找到可用的mManager控制器")
                return
            
            controllers_list = controllers_status.get('controllers', [])
            print(f"找到 {len(controllers_list)} 个控制器")
            print(f"状态概览: 总计 {controllers_status.get('total')}, 健康 {controllers_status.get('healthy')}, 不健康 {controllers_status.get('unhealthy')}")
            
            for controller_info in controllers_list:
                controller_id = controller_info.get('id')
                print(f"\n控制器ID: {controller_id}")
                print(f"状态: {controller_info.get('status')}")
                print(f"URL: {controller_info.get('url')}")
                print(f"类型: {controller_info.get('server_type')}")
                print(f"当前容器: {controller_info.get('current_containers')}")
                print(f"最大容器: {controller_info.get('max_containers')}")
                print(f"负载百分比: {controller_info.get('load_percentage')}")
                print(f"启用状态: {controller_info.get('enabled')}")
                print(f"连续失败次数: {controller_info.get('consecutive_failures')}")
                
                # 测试控制器功能
                try:
                    # 获取控制器客户端
                    client = mmanager_client.get_client(controller_id)
                    if client:
                        print(f"✅ 控制器客户端已连接")
                        
                        # 测试健康检查
                        health_result = await client.health_check()
                        print(f"健康检查结果: {health_result}")
                        
                        # 测试获取容器列表
                        containers_result = await client.list_containers()
                        if containers_result:
                            containers = containers_result.get('containers', [])
                            print(f"容器数量: {len(containers)}")
                        else:
                            print(f"容器列表为空或获取失败")
                        
                        # 测试镜像可用性（使用我们修复的方法）
                        print(f"\n测试控制器镜像可用性...")
                        from app.config import settings
                        harbor_auth = {
                            "serveraddress": str(settings.harbor_url.split('://')[-1]),
                            "username": str(settings.harbor_username),
                            "password": str(settings.harbor_password)
                        }
                        
                        test_image = f"{settings.harbor_url.split('://')[-1]}/geoml-hub/redis-7-1:latest"
                        image_available = await mmanager_client.ensure_image_available(
                            controller_id, 
                            test_image, 
                            harbor_auth
                        )
                        
                        if image_available:
                            print(f"✅ 测试镜像可用性检查成功")
                        else:
                            print(f"❌ 测试镜像可用性检查失败")
                        
                    else:
                        print(f"❌ 无法连接到控制器客户端")
                        
                except Exception as e:
                    print(f"❌ 测试控制器功能失败: {e}")
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 测试mManager失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_mmanager_status())