#!/usr/bin/env python3
"""
OpenGMS集成测试脚本
测试注册和登录功能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.opengms_user_service import OpenGMSUserService

async def test_opengms_integration():
    """测试OpenGMS集成功能"""
    print("=== OpenGMS用户服务器集成测试 ===\n")
    
    service = OpenGMSUserService()
    
    # 测试用户信息
    test_email = "test@example.com"
    test_password = "testpass123"
    test_username = "testuser"
    
    print(f"测试配置:")
    print(f"OpenGMS服务器地址: {service.base_url}")
    print(f"客户端ID: {service.client_id}")
    print(f"客户端密钥: {'*' * len(service.client_secret)}")
    print()
    
    # 1. 测试用户注册
    print("1. 测试用户注册...")
    try:
        register_result = await service.register_user(
            email=test_email,
            password=test_password,
            username=test_username,
            fullName="Test User"
        )
        
        if register_result["success"]:
            print("✅ 注册成功")
            print(f"   用户数据: {register_result['data']}")
        else:
            print(f"❌ 注册失败: {register_result['message']}")
            
    except Exception as e:
        print(f"❌ 注册异常: {str(e)}")
    
    print()
    
    # 2. 测试OAuth2登录
    print("2. 测试OAuth2登录...")
    try:
        token_result = await service.get_oauth2_token(
            email=test_email,
            password=test_password,
            ip_address="127.0.0.1"
        )
        
        if token_result["success"]:
            print("✅ 获取token成功")
            access_token = token_result["data"]["access_token"]
            print(f"   Access Token: {access_token[:20]}...{access_token[-10:]}")
            
            # 3. 测试获取用户信息
            print("\n3. 测试获取用户信息...")
            user_info_result = await service.get_user_info(
                access_token=access_token,
                ip_address="127.0.0.1"
            )
            
            if user_info_result["success"]:
                print("✅ 获取用户信息成功")
                user_data = user_info_result["data"]
                print(f"   用户ID: {user_data.get('userId')}")
                print(f"   用户名: {user_data.get('username')}")
                print(f"   邮箱: {user_data.get('email')}")
            else:
                print(f"❌ 获取用户信息失败: {user_info_result['message']}")
                
            # 4. 测试token验证
            print("\n4. 测试token验证...")
            verify_result = await service.verify_token(access_token)
            
            if verify_result["success"]:
                print("✅ Token验证成功")
            else:
                print(f"❌ Token验证失败: {verify_result['message']}")
                
        else:
            print(f"❌ 获取token失败: {token_result['message']}")
            
    except Exception as e:
        print(f"❌ 登录异常: {str(e)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_opengms_integration())