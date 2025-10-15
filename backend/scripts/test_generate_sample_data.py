#!/usr/bin/env python3
"""
测试生成模拟数据 API 的脚本
直接调用数据库，不需要管理员 token
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert
from app.database import get_async_db
from app.models import Repository, RepositoryDailyStats
from datetime import datetime, timezone, timedelta, date
import random

async def main():
    """执行模拟数据生成（内部调用）"""

    # 参数配置
    days = 30
    views_min = 0
    views_max = 20
    downloads_min = 0
    downloads_max = 8
    add_trends = True
    weekend_effect = True
    spike_probability = 0.05

    print("=" * 60)
    print("生成模拟趋势数据")
    print("=" * 60)
    print(f"参数: {days}天, 浏览量[{views_min},{views_max}], 下载量[{downloads_min},{downloads_max}]")
    print(f"趋势效果: {add_trends}, 周末效应: {weekend_effect}, 爆发概率: {spike_probability}")
    print("=" * 60)

    async for db in get_async_db():
        try:
            # 1. 获取所有活跃仓库
            query = select(Repository).where(Repository.is_active == True)
            result = await db.execute(query)
            repositories = result.scalars().all()

            if not repositories:
                print("未找到活跃仓库")
                return

            print(f"\n找到 {len(repositories)} 个活跃仓库")

            # 2. 计算日期范围
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            print(f"日期范围: {start_date} ~ {end_date}")

            # 3. 批量生成数据
            batch_data = []
            total_records = len(repositories) * days
            processed = 0
            affected_repo_ids = set()

            print(f"\n开始生成 {total_records} 条记录...")

            for repo in repositories:
                current_date = start_date
                day_index = 0

                while current_date <= end_date:
                    # 策略2：添加趋势因子
                    trend_factor = 1.0
                    if add_trends:
                        progress = day_index / days
                        trend_factor = 0.5 + progress * 1.0

                    # 生成基础浏览量
                    base_views = random.randint(views_min, views_max)
                    views = int(base_views * trend_factor)

                    # 策略3：周末效应
                    if weekend_effect and current_date.weekday() in [5, 6]:
                        views = int(views * 0.7)

                    # 策略4：随机爆发日
                    if random.random() < spike_probability:
                        views = views * 2

                    # 生成下载量
                    base_downloads = random.randint(downloads_min, downloads_max)
                    downloads = int(base_downloads * trend_factor)

                    if weekend_effect and current_date.weekday() in [5, 6]:
                        downloads = int(downloads * 0.7)

                    # 生成独立访客数
                    unique_visitors = int(views * random.uniform(0.6, 0.8))
                    unique_downloaders = min(downloads, int(downloads * random.uniform(0.8, 1.0)))

                    batch_data.append({
                        'repository_id': repo.id,
                        'date': current_date,
                        'views_count': max(0, views),
                        'downloads_count': max(0, downloads),
                        'unique_visitors': max(0, unique_visitors),
                        'unique_downloaders': max(0, unique_downloaders)
                    })

                    affected_repo_ids.add(repo.id)
                    current_date += timedelta(days=1)
                    day_index += 1
                    processed += 1

                    # 每100条批量插入一次
                    if len(batch_data) >= 100:
                        stmt = insert(RepositoryDailyStats).values(batch_data)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['repository_id', 'date'])
                        await db.execute(stmt)
                        await db.commit()
                        batch_data = []

                        if processed % 500 == 0:
                            progress_pct = (processed / total_records) * 100
                            print(f"  进度: {processed}/{total_records} ({progress_pct:.1f}%)")

            # 插入剩余数据
            if batch_data:
                stmt = insert(RepositoryDailyStats).values(batch_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['repository_id', 'date'])
                await db.execute(stmt)
                await db.commit()

            print(f"\n✓ 数据生成完成，共处理 {processed} 条记录")

            # 4. 同步更新所有受影响仓库的时间窗口统计
            print(f"\n开始更新 {len(affected_repo_ids)} 个仓库的时间窗口统计...")

            for idx, repo_id in enumerate(affected_repo_ids):
                # 计算最近7天和30天的统计
                today = date.today()
                date_7d_ago = today - timedelta(days=7)
                date_30d_ago = today - timedelta(days=30)

                # 7天统计
                stats_7d_query = select(
                    func.sum(RepositoryDailyStats.views_count).label('views'),
                    func.sum(RepositoryDailyStats.downloads_count).label('downloads')
                ).where(
                    RepositoryDailyStats.repository_id == repo_id,
                    RepositoryDailyStats.date >= date_7d_ago,
                    RepositoryDailyStats.date <= today
                )
                stats_7d_result = await db.execute(stats_7d_query)
                stats_7d = stats_7d_result.one()

                # 30天统计
                stats_30d_query = select(
                    func.sum(RepositoryDailyStats.views_count).label('views'),
                    func.sum(RepositoryDailyStats.downloads_count).label('downloads')
                ).where(
                    RepositoryDailyStats.repository_id == repo_id,
                    RepositoryDailyStats.date >= date_30d_ago,
                    RepositoryDailyStats.date <= today
                )
                stats_30d_result = await db.execute(stats_30d_query)
                stats_30d = stats_30d_result.one()

                # 获取仓库的 stars_count
                repo_query = select(Repository.stars_count).where(Repository.id == repo_id)
                repo_result = await db.execute(repo_query)
                stars_count = repo_result.scalar() or 0

                # 计算综合热度分数
                views_7d = stats_7d.views or 0
                downloads_7d = stats_7d.downloads or 0
                views_30d = stats_30d.views or 0
                downloads_30d = stats_30d.downloads or 0

                trending_score = (
                    views_7d * 1.0 +
                    downloads_7d * 3.0 +
                    stars_count * 2.0
                )

                # 更新仓库字段
                await db.execute(
                    update(Repository)
                    .where(Repository.id == repo_id)
                    .values(
                        views_count_7d=views_7d,
                        downloads_count_7d=downloads_7d,
                        views_count_30d=views_30d,
                        downloads_count_30d=downloads_30d,
                        trending_score=trending_score,
                        trending_updated_at=datetime.now(timezone.utc)
                    )
                )

                if (idx + 1) % 10 == 0:
                    print(f"  已更新 {idx + 1}/{len(affected_repo_ids)} 个仓库")

            await db.commit()
            print(f"\n✓ 时间窗口统计更新完成")

            print("\n" + "=" * 60)
            print("模拟数据生成成功！")
            print("=" * 60)
            print(f"仓库数量: {len(repositories)}")
            print(f"总记录数: {processed}")
            print(f"日期范围: {start_date} ~ {end_date}")
            print("=" * 60)

        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    print("\n模拟数据生成脚本")
    response = input("\n是否继续生成模拟数据？(y/N): ")
    if response.lower() == 'y':
        asyncio.run(main())
    else:
        print("已取消")
