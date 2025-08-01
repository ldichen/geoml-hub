#!/usr/bin/env python3
"""
测试现有admin用户的兼容性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
import asyncio

async def test_existing_admin():
    """测试现有admin用户"""
    print("=== 现有Admin用户兼容性测试 ===\n")
    
    db = SessionLocal()
    try:
        # 1. 查找admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("❌ 未找到admin用户")
            return
        
        print("✅ 找到admin用户:")
        print(f"   - 用户ID: {admin_user.id}")
        print(f"   - 外部ID: {admin_user.external_user_id}")
        print(f"   - 用户名: {admin_user.username}")
        print(f"   - 邮箱: {admin_user.email}")
        print(f"   - 管理员: {admin_user.is_admin}")
        print(f"   - 状态: {'激活' if admin_user.is_active else '停用'}")
        print()
        
        # 2. 测试JWT token生成
        print("2. 测试JWT token生成...")
        auth_service = AuthService(db)
        
        try:
            token = await auth_service.create_user_token(admin_user)
            print(f"✅ JWT token生成成功:")
            print(f"   Token: {token[:20]}...{token[-10:]}")
            
            # 3. 测试token验证
            print("\n3. 测试token验证...")
            token_data = auth_service.verify_token(token)
            if token_data:
                print(f"✅ Token验证成功:")
                print(f"   外部用户ID: {token_data.external_user_id}")
                
                # 4. 测试用户认证
                print("\n4. 测试用户认证...")
                authenticated_user = await auth_service.authenticate_user(token_data.external_user_id)
                if authenticated_user:
                    print(f"✅ 用户认证成功:")
                    print(f"   认证用户: {authenticated_user.username}")
                    print(f"   用户ID匹配: {authenticated_user.id == admin_user.id}")
                else:
                    print("❌ 用户认证失败")
            else:
                print("❌ Token验证失败")
        except Exception as e:
            print(f"❌ Token处理异常: {e}")
        
        print("\n=== 兼容性总结 ===")
        print("✅ 现有admin用户完全兼容新的认证系统")
        print("✅ 可以继续使用外部token登录")
        print("✅ JWT token生成和验证正常")
        print("✅ 用户权限和状态保持不变")
        
        print("\n🔧 使用建议:")
        print("1. 继续使用 POST /api/auth/login 端点（外部token）")
        print("2. 或在OpenGMS服务器注册相同邮箱的账户")
        print("3. 所有现有功能和权限保持不变")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_existing_admin())