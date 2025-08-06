#!/usr/bin/env python3
"""
简单的mManager测试
"""

import asyncio
import aiohttp

async def test_mmanager_simple():
    """简单测试mManager连接和基本功能"""
    print("=== 简单mManager测试 ===")
    
    base_url = "http://localhost:8001"
    api_key = "mmanager-default-key"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    timeout = aiohttp.ClientTimeout(total=60)  # 增加超时时间
    
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            # 测试1: 健康检查
            print("1. 测试健康检查...")
            async with session.get(f"{base_url}/health") as response:
                health_data = await response.json()
                print(f"✅ 健康检查成功: {health_data['status']}")
            
            # 测试2: 列出镜像
            print("\n2. 测试列出镜像...")
            async with session.get(f"{base_url}/images/") as response:
                images_data = await response.json()
                print(f"✅ 镜像列表获取成功，共 {len(images_data.get('images', []))} 个镜像")
                
                # 显示前几个镜像
                for i, image in enumerate(images_data.get('images', [])[:3]):
                    print(f"   镜像 {i+1}: {image.get('repository', 'N/A')}:{image.get('tag', 'N/A')}")
            
            # 测试3: 检查特定镜像是否存在
            print("\n3. 检查特定镜像...")
            target_image = "172.21.252.230/geoml-hub/redis-7-1:latest"
            try:
                async with session.get(f"{base_url}/images/{target_image}") as response:
                    if response.status == 200:
                        image_info = await response.json()
                        print(f"✅ 镜像存在: {target_image}")
                        print(f"   大小: {image_info.get('size', 'N/A')}")
                    else:
                        print(f"❌ 镜像不存在: {target_image} (状态码: {response.status})")
            except Exception as e:
                print(f"❌ 检查镜像失败: {e}")
            
            # 测试4: 尝试拉取镜像（如果不存在）
            print(f"\n4. 尝试拉取镜像: {target_image}")
            pull_data = {
                "image": target_image,
                "auth": {
                    "serveraddress": "172.21.252.230",
                    "username": "admin",
                    "password": "ZXCvbnm1"
                }
            }
            
            try:
                async with session.post(f"{base_url}/images/pull", json=pull_data) as response:
                    response_data = await response.json()
                    print(f"拉取响应: {response_data}")
                    
                    if response.status == 200:
                        print("✅ 镜像拉取请求已提交")
                    else:
                        print(f"❌ 镜像拉取失败 (状态码: {response.status})")
                        
            except Exception as e:
                print(f"❌ 镜像拉取请求失败: {e}")
                
                # 如果是变量类型错误，显示详细信息
                if "Invalid variable type" in str(e):
                    print("\n=== 调试变量类型 ===")
                    print(f"pull_data: {pull_data}")
                    for key, value in pull_data.items():
                        print(f"{key}: {value} (type: {type(value).__name__})")
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                print(f"  {subkey}: {subvalue} (type: {type(subvalue).__name__})")
    
    except asyncio.TimeoutError:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mmanager_simple())