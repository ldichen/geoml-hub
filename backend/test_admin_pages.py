#!/usr/bin/env python3
"""
测试所有管理员页面的API
"""

import requests
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.mock_external_auth import mock_external_auth

def test_all_admin_pages():
    """测试所有管理员页面的API"""
    
    print("🔍 测试所有管理员页面的API...")
    
    # 1. 登录
    external_token = mock_external_auth.create_external_token("admin@geoml-hub.com", "admin123")
    login_response = requests.post("http://localhost:8000/api/auth/login", 
                                  json={"external_token": external_token})
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return False
    
    access_token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. 测试仪表板
    print("1. 测试仪表板...")
    dashboard_response = requests.get("http://localhost:8000/api/admin/dashboard", headers=headers)
    if dashboard_response.status_code == 200:
        print("   ✅ 仪表板API正常")
    else:
        print(f"   ❌ 仪表板API失败: {dashboard_response.status_code}")
    
    # 3. 测试用户管理
    print("2. 测试用户管理...")
    users_response = requests.get("http://localhost:8000/api/admin/users?skip=0&limit=10&sort_by=created&order=desc", headers=headers)
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"   ✅ 用户管理API正常，返回 {len(users_data.get('users', []))} 个用户")
    else:
        print(f"   ❌ 用户管理API失败: {users_response.status_code}")
    
    # 4. 测试仓库管理
    print("3. 测试仓库管理...")
    repos_response = requests.get("http://localhost:8000/api/admin/repositories?skip=0&limit=10&sort_by=created&order=desc", headers=headers)
    if repos_response.status_code == 200:
        repos_data = repos_response.json()
        print(f"   ✅ 仓库管理API正常，返回 {len(repos_data.get('repositories', []))} 个仓库")
    else:
        print(f"   ❌ 仓库管理API失败: {repos_response.status_code}")
    
    # 5. 测试存储管理
    print("4. 测试存储管理...")
    storage_response = requests.get("http://localhost:8000/api/admin/storage/stats", headers=headers)
    if storage_response.status_code == 200:
        print("   ✅ 存储管理API正常")
    else:
        print(f"   ❌ 存储管理API失败: {storage_response.status_code}")
    
    # 6. 测试系统监控
    print("5. 测试系统监控...")
    health_response = requests.get("http://localhost:8000/api/admin/system/health", headers=headers)
    if health_response.status_code == 200:
        print("   ✅ 系统监控API正常")
    else:
        print(f"   ❌ 系统监控API失败: {health_response.status_code}")
    
    # 7. 测试系统日志
    print("6. 测试系统日志...")
    logs_response = requests.get("http://localhost:8000/api/admin/logs", headers=headers)
    if logs_response.status_code == 200:
        print("   ✅ 系统日志API正常")
    else:
        print(f"   ❌ 系统日志API失败: {logs_response.status_code}")
    
    print("\n🎉 所有管理员页面API测试完成！")
    return True

if __name__ == "__main__":
    try:
        test_all_admin_pages()
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()