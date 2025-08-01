#!/usr/bin/env python3
"""
初始化管理员用户脚本
创建一个默认的管理员用户以便访问管理面板
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_engine, get_async_db
from app.models.user import User
# 不需要密码哈希，使用外部认证
from datetime import datetime, timezone

async def create_admin_user():
    """创建默认管理员用户"""
    
    # 管理员用户信息
    admin_data = {
        "username": "admin",
        "email": "admin@geoml-hub.com", 
        "full_name": "系统管理员",
        "is_admin": True,
        "is_active": True,
        "is_verified": True,
    }
    
    async with async_engine.begin() as conn:
        # 创建会话
        async_session = AsyncSession(conn)
        
        try:
            # 检查是否已存在管理员用户
            existing_admin = await async_session.execute(
                select(User).where(User.username == admin_data["username"])
            )
            admin_user = existing_admin.scalar_one_or_none()
            
            if admin_user:
                print(f"管理员用户 '{admin_data['username']}' 已存在")
                
                # 确保用户是管理员
                if not getattr(admin_user, "is_admin", False):
                    setattr(admin_user, "is_admin", True)
                    await async_session.commit()
                    print(f"已将用户 '{admin_data['username']}' 设置为管理员")
                
                return admin_user
            
            # 创建新的管理员用户
            new_admin = User(
                username=admin_data["username"],
                email=admin_data["email"],
                full_name=admin_data["full_name"],
                is_admin=admin_data["is_admin"],
                is_active=admin_data["is_active"],
                is_verified=admin_data["is_verified"],
                created_at=datetime.now(timezone.utc),
                external_user_id=f"mock_{admin_data['username']}",  # 模拟外部ID
            )
            
            async_session.add(new_admin)
            await async_session.commit()
            await async_session.refresh(new_admin)
            
            print(f"成功创建管理员用户:")
            print(f"  用户名: {admin_data['username']}")
            print(f"  邮箱: {admin_data['email']}")
            print(f"  外部用户ID: mock_{admin_data['username']}")
            print(f"  管理员权限: {admin_data['is_admin']}")
            print()
            print("请使用以下凭据登录管理面板:")
            print(f"  邮箱: {admin_data['email']}")
            print(f"  密码: admin123")
            print()
            print("登录页面: http://localhost:5173/login")
            print("管理面板: http://localhost:5173/admin/dashboard")
            
            return new_admin
            
        except Exception as e:
            await async_session.rollback()
            print(f"创建管理员用户失败: {e}")
            raise
        finally:
            await async_session.close()

async def main():
    """主函数"""
    print("正在初始化管理员用户...")
    
    try:
        await create_admin_user()
        print("管理员用户初始化完成!")
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())