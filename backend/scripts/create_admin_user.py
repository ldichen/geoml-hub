#!/usr/bin/env python3
"""
创建管理员用户脚本
用于生产环境初始化管理员账户
"""

import sys
import os
import uuid

# 添加父目录到路径，以便可以导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserStorage


def create_admin_user():
    """创建管理员用户"""
    db = SessionLocal()
    
    try:
        print("🔧 GeoML-Hub 管理员用户创建工具")
        print("=" * 50)
        
        # 检查是否已有管理员用户
        existing_admin = db.query(User).filter(User.is_admin.is_(True)).first()
        if existing_admin:
            print(f"⚠️  管理员用户已存在: {existing_admin.username} ({existing_admin.email})")
            response = input("是否要创建另一个管理员用户? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ 已取消创建")
                return
        
        # 获取用户输入
        print("\n📝 请输入管理员信息:")
        
        # 用户名
        while True:
            username = input("用户名 (用于URL路径): ").strip()
            if not username:
                print("❌ 用户名不能为空")
                continue
            if len(username) < 3:
                print("❌ 用户名至少需要3个字符")
                continue
            if not username.replace('_', '').replace('-', '').isalnum():
                print("❌ 用户名只能包含字母、数字、下划线和连字符")
                continue
            
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                print(f"❌ 用户名 '{username}' 已存在")
                continue
            break
        
        # 邮箱
        while True:
            email = input("邮箱地址: ").strip()
            if not email:
                print("❌ 邮箱不能为空")
                continue
            if '@' not in email or '.' not in email:
                print("❌ 请输入有效的邮箱地址")
                continue
            
            # 检查邮箱是否已存在
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                print(f"❌ 邮箱 '{email}' 已存在")
                continue
            break
        
        # 显示名称
        full_name = input(f"显示名称 (默认: {username}): ").strip()
        if not full_name:
            full_name = username
        
        # 个人简介
        bio = input("个人简介 (可选): ").strip()
        
        # 生成外部用户ID (模拟)
        external_user_id = f"admin_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        admin_user = User(
            external_user_id=external_user_id,
            username=username,
            email=email,
            full_name=full_name,
            bio=bio or f"GeoML-Hub 系统管理员",
            is_active=True,
            is_verified=True,
            is_admin=True,
            storage_quota=107374182400,  # 100GB 管理员配额
            storage_used=0,
        )
        
        db.add(admin_user)
        db.flush()  # 获取用户ID
        
        # 创建用户存储记录
        user_storage = UserStorage(
            user_id=admin_user.id,
            total_files=0,
            total_size=0,
            model_files_count=0,
            model_files_size=0,
            dataset_files_count=0,
            dataset_files_size=0,
            image_files_count=0,
            image_files_size=0,
            document_files_count=0,
            document_files_size=0,
            other_files_count=0,
            other_files_size=0
        )
        
        db.add(user_storage)
        db.commit()
        
        print("\n✅ 管理员用户创建成功!")
        print(f"📋 用户信息:")
        print(f"   - 用户ID: {admin_user.id}")
        print(f"   - 外部ID: {external_user_id}")
        print(f"   - 用户名: {username}")
        print(f"   - 邮箱: {email}")
        print(f"   - 显示名称: {full_name}")
        print(f"   - 存储配额: 100GB")
        print(f"   - 管理员权限: 是")
        print(f"   - 账户状态: 已激活")
        print(f"   - 邮箱验证: 已验证")
        
        print(f"\n🌐 用户空间地址: /{username}")
        print(f"🔗 用户主页: https://your-domain.com/{username}")
        
        print("\n⚠️  重要提醒:")
        print("1. 请确保外部认证系统中存在对应的用户账户")
        print("2. 外部用户ID需要在认证系统中配置")
        print("3. 首次登录时请验证管理员权限正常工作")
        print("4. 建议为管理员账户设置强密码和双重认证")
        
        # 保存信息到文件
        try:
            with open('/tmp/geoml_admin_info.txt', 'w') as f:
                f.write(f"GeoML-Hub 管理员账户信息\n")
                f.write(f"创建时间: {admin_user.created_at}\n")
                f.write(f"用户ID: {admin_user.id}\n")
                f.write(f"外部ID: {external_user_id}\n")
                f.write(f"用户名: {username}\n")
                f.write(f"邮箱: {email}\n")
                f.write(f"显示名称: {full_name}\n")
                f.write(f"管理员权限: 是\n")
                f.write(f"存储配额: 100GB\n")
            
            print(f"\n💾 用户信息已保存到: /tmp/geoml_admin_info.txt")
        except Exception as e:
            print(f"\n⚠️  无法保存用户信息到文件: {e}")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
        db.rollback()
    except Exception as e:
        print(f"\n❌ 创建管理员用户时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def list_admin_users():
    """列出所有管理员用户"""
    db = SessionLocal()
    
    try:
        print("👥 现有管理员用户列表")
        print("=" * 50)
        
        admin_users = db.query(User).filter(User.is_admin.is_(True)).all()
        
        if not admin_users:
            print("❌ 没有找到管理员用户")
            return
        
        for i, user in enumerate(admin_users, 1):
            print(f"{i}. {user.username} ({user.email})")
            print(f"   - 用户ID: {user.id}")
            print(f"   - 显示名称: {user.full_name}")
            print(f"   - 账户状态: {'激活' if user.is_active else '停用'}")
            print(f"   - 邮箱验证: {'已验证' if user.is_verified else '未验证'}")
            print(f"   - 创建时间: {user.created_at}")
            print(f"   - 最后活跃: {user.last_active_at}")
            print()
        
        print(f"📊 总计: {len(admin_users)} 个管理员用户")
        
    except Exception as e:
        print(f"❌ 获取管理员用户列表时发生错误: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_admin_users()
            return
        elif sys.argv[1] == "--help":
            print("GeoML-Hub 管理员用户管理工具")
            print("\n用法:")
            print("  python create_admin_user.py          # 创建新管理员用户")
            print("  python create_admin_user.py --list   # 列出现有管理员用户")
            print("  python create_admin_user.py --help   # 显示帮助信息")
            return
    
    create_admin_user()


if __name__ == "__main__":
    main()