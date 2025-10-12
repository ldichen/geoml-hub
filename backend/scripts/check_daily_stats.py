#!/usr/bin/env python3
"""检查 repository_daily_stats 表中的数据"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from app.database import get_async_db
from app.models import RepositoryDailyStats, Repository

async def main():
    async for db in get_async_db():
        try:
            # 统计总记录数
            result = await db.execute(select(func.count(RepositoryDailyStats.id)))
            total_count = result.scalar()
            print(f"repository_daily_stats 表中总共有 {total_count} 条记录")

            # 查看按仓库分组的统计
            query = select(
                Repository.id,
                Repository.name,
                func.count(RepositoryDailyStats.id).label('days_count'),
                func.sum(RepositoryDailyStats.views_count).label('total_views'),
                func.sum(RepositoryDailyStats.downloads_count).label('total_downloads')
            ).join(
                RepositoryDailyStats, Repository.id == RepositoryDailyStats.repository_id
            ).group_by(
                Repository.id, Repository.name
            ).order_by(
                func.count(RepositoryDailyStats.id).desc()
            ).limit(10)

            result = await db.execute(query)
            rows = result.all()

            if rows:
                print("\n前10个有统计数据的仓库：")
                print(f"{'ID':<6} {'Name':<40} {'Days':<8} {'Views':<10} {'Downloads':<10}")
                print("-" * 80)
                for row in rows:
                    print(f"{row.id:<6} {row.name:<40} {row.days_count:<8} {row.total_views:<10} {row.total_downloads:<10}")
            else:
                print("\n没有找到任何统计数据")

            # 查看最近的记录
            query = select(RepositoryDailyStats).order_by(RepositoryDailyStats.date.desc()).limit(5)
            result = await db.execute(query)
            recent = result.scalars().all()

            if recent:
                print("\n最近的5条记录：")
                for stat in recent:
                    print(f"  仓库ID: {stat.repository_id}, 日期: {stat.date}, 浏览: {stat.views_count}, 下载: {stat.downloads_count}")

        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(main())
