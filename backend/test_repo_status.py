#!/usr/bin/env python3
"""
测试仓库状态显示
"""

import requests
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.mock_external_auth import mock_external_auth

def test_repo_status():
    """测试仓库状态显示"""
    
    print("🔍 测试仓库状态显示...")
    
    # 1. 登录
    external_token = mock_external_auth.create_external_token("admin@geoml-hub.com", "admin123")
    login_response = requests.post("http://localhost:8000/api/auth/login", 
                                  json={"external_token": external_token})
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return False
    
    access_token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. 检查仓库状态
    print("检查仓库状态...")
    repos_response = requests.get("http://localhost:8000/api/admin/repositories?skip=0&limit=10&sort_by=created&order=desc", headers=headers)
    if repos_response.status_code == 200:
        repos_data = repos_response.json()
        print(f"总共 {len(repos_data.get('repositories', []))} 个仓库:")
        for repo in repos_data.get("repositories", []):
            status = "正常" if repo.get("is_active", True) else "已删除"
            featured = "推荐" if repo.get("is_featured", False) else "普通"
            print(f"  - {repo['name']}: {status} ({featured}, {repo['visibility']})")
    else:
        print(f"❌ 仓库管理API失败: {repos_response.status_code}")
        return False
    
    print("\n✅ 仓库状态测试完成！")
    return True

if __name__ == "__main__":
    try:
        test_repo_status()
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()