#!/usr/bin/env python3
"""检查 repository_views 表中的数据"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, cast, Date
from app.database import get_async_db
from app.models import RepositoryView, Repository

async def main():
    async for db in get_async_db():
        try:
            # 统计总记录数
            result = await db.execute(select(func.count(RepositoryView.id)))
            total_count = result.scalar()
            print(f"repository_views 表中总共有 {total_count} 条记录")

            # 查看日期分布
            query = select(
                cast(RepositoryView.created_at, Date).label('date'),
                func.count(RepositoryView.id).label('count')
            ).group_by('date').order_by('date').limit(20)

            result = await db.execute(query)
            rows = result.all()

            if rows:
                print("\n浏览记录日期分布（前20天）：")
                for row in rows:
                    print(f"  {row.date}: {row.count} 次浏览")
            else:
                print("\n没有找到浏览记录")

            # 查看最近的记录
            query = select(RepositoryView).order_by(RepositoryView.created_at.desc()).limit(5)
            result = await db.execute(query)
            recent = result.scalars().all()

            if recent:
                print("\n最近的5条浏览记录：")
                for view in recent:
                    print(f"  仓库ID: {view.repository_id}, 时间: {view.created_at}, IP: {view.ip_address}")

        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(main())
