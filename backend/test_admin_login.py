#!/usr/bin/env python3
"""
测试管理员登录和权限的脚本
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000"

async def test_admin_login():
    """测试管理员登录流程"""
    
    async with aiohttp.ClientSession() as session:
        print("1. 测试模拟外部认证...")
        
        # 步骤1: 获取外部令牌
        async with session.post(f"{API_BASE}/api/auth/mock-external-auth", 
                               json={
                                   "email": "admin@geoml-hub.com",
                                   "password": "admin123"
                               }) as resp:
            if resp.status != 200:
                print(f"模拟外部认证失败: {resp.status}")
                text = await resp.text()
                print(f"错误详情: {text}")
                return
                
            external_auth_data = await resp.json()
            external_token = external_auth_data.get("external_token")
            print(f"外部认证成功，令牌: {external_token[:20]}...")
        
        print("\n2. 测试系统登录...")
        
        # 步骤2: 使用外部令牌登录系统
        async with session.post(f"{API_BASE}/api/auth/login",
                               json={"external_token": external_token}) as resp:
            if resp.status != 200:
                print(f"系统登录失败: {resp.status}")
                text = await resp.text()
                print(f"错误详情: {text}")
                return
                
            login_data = await resp.json()
            access_token = login_data.get("access_token")
            user_info = login_data.get("user", {})
            print(f"系统登录成功")
            print(f"访问令牌: {access_token[:20]}...")
            print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
        
        print("\n3. 测试获取当前用户信息...")
        
        # 步骤3: 获取当前用户详细信息
        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get(f"{API_BASE}/api/auth/me", headers=headers) as resp:
            if resp.status != 200:
                print(f"获取用户信息失败: {resp.status}")
                text = await resp.text()
                print(f"错误详情: {text}")
                return
                
            me_data = await resp.json()
            print(f"当前用户信息:")
            print(json.dumps(me_data, indent=2, ensure_ascii=False))
            
            # 检查管理员权限
            is_admin = me_data.get("is_admin", False)
            print(f"\n管理员权限: {'✅ 是' if is_admin else '❌ 否'}")
            
            if not is_admin:
                print("⚠️  用户没有管理员权限！")
                return
        
        print("\n4. 测试管理员API访问...")
        
        # 步骤4: 测试访问管理员API
        async with session.get(f"{API_BASE}/api/admin/dashboard", headers=headers) as resp:
            print(f"管理员仪表板API状态: {resp.status}")
            if resp.status == 200:
                print("✅ 管理员API访问成功")
                stats_data = await resp.json()
                print(f"仪表板数据: {json.dumps(stats_data, indent=2, ensure_ascii=False)}")
            else:
                print("❌ 管理员API访问失败")
                text = await resp.text()
                print(f"错误详情: {text}")

if __name__ == "__main__":
    print("开始测试管理员登录流程...")
    print("="*50)
    
    try:
        asyncio.run(test_admin_login())
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*50)
    print("测试完成")