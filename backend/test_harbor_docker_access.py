#!/usr/bin/env python3
"""
测试Docker是否能够访问Harbor
"""

import asyncio
import subprocess
from app.config import settings

async def test_docker_harbor_access():
    """测试Docker访问Harbor"""
    print("=== 测试Docker访问Harbor ===")
    
    harbor_url = settings.harbor_url
    harbor_username = settings.harbor_username
    harbor_password = settings.harbor_password
    
    # 提取Harbor主机地址
    if '://' in harbor_url:
        harbor_host = harbor_url.split('://')[-1]
    else:
        harbor_host = harbor_url
    
    print(f"Harbor Host: {harbor_host}")
    print(f"Harbor Username: {harbor_username}")
    
    # 测试1: Docker登录
    print("\n=== 测试1: Docker登录Harbor ===")
    login_cmd = f"echo '{harbor_password}' | docker login {harbor_host} -u {harbor_username} --password-stdin"
    
    try:
        process = await asyncio.create_subprocess_shell(
            login_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("✅ Docker登录Harbor成功")
            print(f"输出: {stdout.decode().strip()}")
        else:
            print("❌ Docker登录Harbor失败")
            print(f"错误: {stderr.decode().strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Docker登录命令执行失败: {e}")
        return False
    
    # 测试2: 尝试拉取镜像
    print("\n=== 测试2: 尝试拉取镜像 ===")
    test_image = f"{harbor_host}/geoml-hub/redis-7-1:latest"
    pull_cmd = f"docker pull {test_image}"
    
    try:
        print(f"尝试拉取镜像: {test_image}")
        process = await asyncio.create_subprocess_shell(
            pull_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print("✅ Docker拉取镜像成功")
            print(f"输出: {stdout.decode().strip()}")
            
            # 清理测试镜像
            cleanup_cmd = f"docker rmi {test_image}"
            await asyncio.create_subprocess_shell(cleanup_cmd)
            print("已清理测试镜像")
            
        else:
            print("❌ Docker拉取镜像失败")
            print(f"错误: {stderr.decode().strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Docker拉取命令执行失败: {e}")
        return False
    
    print("\n✅ 所有测试通过，Docker可以正常访问Harbor")
    return True

if __name__ == "__main__":
    asyncio.run(test_docker_harbor_access())