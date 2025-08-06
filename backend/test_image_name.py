#!/usr/bin/env python3
"""
测试镜像名称生成
"""

from app.config import settings

# 模拟Image对象的方法
def test_full_docker_image_name(harbor_storage_name="redis-7-1"):
    """测试完整Docker镜像地址生成"""
    harbor_url = settings.harbor_url
    
    # 处理Harbor URL，提取主机地址（去除协议，保留端口）
    if '://' in harbor_url:
        harbor_host = harbor_url.split('://')[-1]
    else:
        harbor_host = harbor_url
    
    harbor_project = settings.harbor_default_project
    return f"{harbor_host}/{harbor_project}/{harbor_storage_name}:latest"

if __name__ == "__main__":
    print("=== Harbor配置信息 ===")
    print(f"Harbor URL: {settings.harbor_url}")
    print(f"Harbor Project: {settings.harbor_default_project}")
    
    print("\n=== 生成的镜像名称 ===")
    test_image_name = test_full_docker_image_name("redis-7-1")
    print(f"生成的镜像名称: {test_image_name}")
    
    print("\n=== 错误信息中的镜像名称 ===")
    print("错误中的镜像名称: 172.21.252.230/geoml-hub/redis-7-1:latest")
    
    print("\n=== 比较结果 ===")
    error_image = "172.21.252.230/geoml-hub/redis-7-1:latest"
    if test_image_name == error_image:
        print("✅ 镜像名称匹配，问题可能在其他地方")
    else:
        print(f"❌ 镜像名称不匹配")
        print(f"应该是: {test_image_name}")
        print(f"实际是: {error_image}")