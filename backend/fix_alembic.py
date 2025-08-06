#!/usr/bin/env python3
"""修复Alembic版本问题"""

import os
import sys
from sqlalchemy import create_engine, text

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 数据库连接
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/geoml_hub"
engine = create_engine(DATABASE_URL)

def fix_alembic_version():
    with engine.connect() as conn:
        # 查看当前版本
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.fetchone()
        
        if current_version:
            print(f"当前版本: {current_version[0]}")
            
            # 如果是mmanager_001，更新为正确的版本
            if current_version[0] == 'mmanager_001':
                conn.execute(text("UPDATE alembic_version SET version_num = 'add_mmanager_support'"))
                conn.commit()
                print("已更新版本为: add_mmanager_support")
            else:
                print("版本正常，无需修复")
        else:
            print("没有找到版本记录")

if __name__ == "__main__":
    fix_alembic_version()