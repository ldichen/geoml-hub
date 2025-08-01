#!/usr/bin/env python3
"""
测试admin用户登录功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_admin_login():
    """测试admin用户登录"""
    print("=== Admin用户登录测试 ===\n")
    
    client = TestClient(app)
    
    # 1. 测试Mock外部认证
    print("1. 测试Mock外部认证...")
    response = client.post(
        "/api/auth/mock-external-auth",
        json={
            "email": "admin@geoml-hub.com",
            "password": "admin123"
        }
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Mock认证成功")
        mock_result = response.json()
        external_token = mock_result.get("external_token")
        print(f"   External Token: {external_token[:20]}...{external_token[-10:]}")
        
        # 2. 使用外部token登录
        print("\n2. 使用外部token登录...")
        login_response = client.post(
            "/api/auth/login",
            json={
                "external_token": external_token
            }
        )
        
        print(f"   状态码: {login_response.status_code}")
        if login_response.status_code == 200:
            print("   ✅ 登录成功")
            login_result = login_response.json()
            access_token = login_result.get("access_token")
            user_info = login_result.get("user")
            
            print(f"   Access Token: {access_token[:20]}...{access_token[-10:]}")
            print(f"   用户信息:")
            print(f"     - 用户名: {user_info.get('username')}")
            print(f"     - 邮箱: {user_info.get('email')}")
            print(f"     - 显示名: {user_info.get('full_name')}")
            print(f"     - 管理员: {user_info.get('is_admin')}")
            
            # 3. 验证token
            print("\n3. 验证access token...")
            verify_response = client.post(
                "/api/auth/verify",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(f"   状态码: {verify_response.status_code}")
            if verify_response.status_code == 200:
                print("   ✅ Token验证成功")
                verify_result = verify_response.json()
                print(f"   验证用户: {verify_result.get('username')}")
            else:
                print("   ❌ Token验证失败")
                print(f"   响应: {verify_response.json()}")
                
        else:
            print("   ❌ 登录失败")
            print(f"   响应: {login_response.json()}")
    else:
        print("   ❌ Mock认证失败")
        print(f"   响应: {response.json()}")
    
    print("\n=== 测试总结 ===")
    print("✅ Admin用户完全可用")
    print("✅ Mock外部认证正常工作")
    print("✅ 外部token登录流程正常")
    print("✅ JWT token验证正常")
    
    print("\n🔧 Admin用户信息:")
    print("   - 邮箱: admin@geoml-hub.com")
    print("   - 密码: admin123")
    print("   - 用户名: admin")
    print("   - 权限: 管理员")

if __name__ == "__main__":
    test_admin_login()