#!/usr/bin/env python3
"""
为演示目的生成模拟的趋势数据
为前10个最受欢迎的仓库生成过去30天的每日统计
"""
import asyncio
import sys
import random
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.database import get_async_db
from app.models import Repository, RepositoryDailyStats

async def main():
    async for db in get_async_db():
        try:
            # 获取浏览量最多的前10个仓库
            query = select(Repository).order_by(Repository.views_count.desc()).limit(10)
            result = await db.execute(query)
            repositories = result.scalars().all()

            if not repositories:
                print("没有找到仓库")
                return

            print(f"为 {len(repositories)} 个仓库生成30天的模拟趋势数据")
            print("-" * 60)

            # 生成过去30天的日期
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            for repo in repositories:
                print(f"\n处理仓库: {repo.name} (ID: {repo.id})")

                # 为每一天生成数据
                current_date = start_date
                days_count = 0

                while current_date <= end_date:
                    # 生成随机但合理的数据
                    # 浏览量: 基于仓库总浏览量的日均值，加上随机波动
                    base_daily_views = max(1, repo.views_count // 90)  # 假设90天的平均值
                    views = random.randint(
                        max(0, base_daily_views - 5),
                        base_daily_views + 15
                    )

                    # 下载量: 通常比浏览量少，约10-20%的浏览会下载
                    downloads = random.randint(0, max(1, views // 5))

                    # 独立访客: 约为浏览量的60-80%
                    unique_visitors = int(views * random.uniform(0.6, 0.8))

                    # 独立下载者: 约为下载量的80-100%
                    unique_downloaders = min(downloads, int(downloads * random.uniform(0.8, 1.0)))

                    # 使用 UPSERT 插入或更新数据
                    stmt = insert(RepositoryDailyStats).values(
                        repository_id=repo.id,
                        date=current_date,
                        views_count=views,
                        downloads_count=downloads,
                        unique_visitors=unique_visitors,
                        unique_downloaders=unique_downloaders
                    ).on_conflict_do_update(
                        index_elements=['repository_id', 'date'],
                        set_=dict(
                            views_count=views,
                            downloads_count=downloads,
                            unique_visitors=unique_visitors,
                            unique_downloaders=unique_downloaders,
                            updated_at=func.now()
                        )
                    )

                    await db.execute(stmt)
                    days_count += 1
                    current_date += timedelta(days=1)

                await db.commit()
                print(f"  ✓ 生成了 {days_count} 天的数据")

            print("\n" + "=" * 60)
            print("✓ 模拟数据生成完成！")
            print("=" * 60)

            # 更新时间窗口统计
            print("\n更新时间窗口统计...")
            from app.services.stats_scheduler import update_repository_trending_stats
            await update_repository_trending_stats(db)
            print("✓ 时间窗口统计更新完成")

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    print("\n模拟趋势数据生成器")
    print("=" * 60)
    print("此脚本将为前10个最受欢迎的仓库生成过去30天的模拟统计数据")
    print("注意: 这仅用于演示目的")
    print("=" * 60)

    response = input("\n是否继续？(y/N): ")
    if response.lower() == 'y':
        asyncio.run(main())
    else:
        print("已取消")
