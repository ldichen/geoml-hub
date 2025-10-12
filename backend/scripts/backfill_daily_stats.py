"""
历史数据回填脚本
从 repository_views 和 file_downloads 表回填 repository_daily_stats 表
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.dialects.postgresql import insert
from app.database import get_async_db
from app.models import Repository, RepositoryView, FileDownload, RepositoryFile, RepositoryDailyStats
from datetime import date, timedelta
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def backfill_views_data(db: AsyncSession, start_date: date, end_date: date):
    """回填浏览量历史数据

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
    """
    logger.info(f"开始回填浏览量数据: {start_date} 到 {end_date}")

    current_date = start_date
    total_days = (end_date - start_date).days + 1
    processed_days = 0

    while current_date <= end_date:
        try:
            # 查询该日期的每个仓库的浏览量
            views_query = select(
                RepositoryView.repository_id,
                func.count(RepositoryView.id).label('views_count'),
                func.count(func.distinct(RepositoryView.ip_address)).label('unique_visitors')
            ).where(
                cast(RepositoryView.created_at, Date) == current_date
            ).group_by(RepositoryView.repository_id)

            views_result = await db.execute(views_query)
            views_data = views_result.all()

            # 批量插入/更新
            for row in views_data:
                stmt = insert(RepositoryDailyStats).values(
                    repository_id=row.repository_id,
                    date=current_date,
                    views_count=row.views_count,
                    unique_visitors=row.unique_visitors,
                    downloads_count=0,  # 稍后由下载数据回填
                    unique_downloaders=0
                ).on_conflict_do_update(
                    index_elements=['repository_id', 'date'],
                    set_=dict(
                        views_count=row.views_count,
                        unique_visitors=row.unique_visitors,
                        updated_at=func.now()
                    )
                )
                await db.execute(stmt)

            await db.commit()

            processed_days += 1
            if processed_days % 10 == 0:
                progress = (processed_days / total_days) * 100
                logger.info(f"浏览量回填进度: {processed_days}/{total_days} 天 ({progress:.1f}%)")

        except Exception as e:
            logger.error(f"回填 {current_date} 浏览量失败: {e}")
            await db.rollback()

        current_date += timedelta(days=1)

    logger.info(f"✓ 浏览量数据回填完成，共处理 {processed_days} 天")


async def backfill_downloads_data(db: AsyncSession, start_date: date, end_date: date):
    """回填下载量历史数据

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
    """
    logger.info(f"开始回填下载量数据: {start_date} 到 {end_date}")

    current_date = start_date
    total_days = (end_date - start_date).days + 1
    processed_days = 0

    while current_date <= end_date:
        try:
            # 查询该日期的每个仓库的下载量
            # 需要通过 file_downloads -> repository_files -> repositories 关联
            downloads_query = select(
                RepositoryFile.repository_id,
                func.count(FileDownload.id).label('downloads_count'),
                func.count(func.distinct(FileDownload.ip_address)).label('unique_downloaders')
            ).join(
                RepositoryFile, FileDownload.file_id == RepositoryFile.id
            ).where(
                cast(FileDownload.started_at, Date) == current_date
            ).group_by(RepositoryFile.repository_id)

            downloads_result = await db.execute(downloads_query)
            downloads_data = downloads_result.all()

            # 批量插入/更新
            for row in downloads_data:
                stmt = insert(RepositoryDailyStats).values(
                    repository_id=row.repository_id,
                    date=current_date,
                    views_count=0,  # 已由浏览数据回填
                    downloads_count=row.downloads_count,
                    unique_downloaders=row.unique_downloaders,
                    unique_visitors=0
                ).on_conflict_do_update(
                    index_elements=['repository_id', 'date'],
                    set_=dict(
                        downloads_count=row.downloads_count,
                        unique_downloaders=row.unique_downloaders,
                        updated_at=func.now()
                    )
                )
                await db.execute(stmt)

            await db.commit()

            processed_days += 1
            if processed_days % 10 == 0:
                progress = (processed_days / total_days) * 100
                logger.info(f"下载量回填进度: {processed_days}/{total_days} 天 ({progress:.1f}%)")

        except Exception as e:
            logger.error(f"回填 {current_date} 下载量失败: {e}")
            await db.rollback()

        current_date += timedelta(days=1)

    logger.info(f"✓ 下载量数据回填完成，共处理 {processed_days} 天")


async def main():
    """主函数 - 执行历史数据回填"""
    # 配置回填日期范围
    # 默认回填最近90天的数据，可以根据需要调整
    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    logger.info("=" * 60)
    logger.info("开始历史数据回填")
    logger.info(f"回填日期范围: {start_date} 到 {end_date}")
    logger.info("=" * 60)

    async for db in get_async_db():
        try:
            # 第一步：回填浏览量数据
            logger.info("\n【步骤 1/2】回填浏览量数据")
            await backfill_views_data(db, start_date, end_date)

            # 第二步：回填下载量数据
            logger.info("\n【步骤 2/2】回填下载量数据")
            await backfill_downloads_data(db, start_date, end_date)

            logger.info("\n" + "=" * 60)
            logger.info("✓ 历史数据回填完成")
            logger.info("=" * 60)

            # 回填完成后，立即更新时间窗口统计
            logger.info("\n开始更新时间窗口统计...")
            from app.services.stats_scheduler import update_repository_trending_stats
            await update_repository_trending_stats(db)
            logger.info("✓ 时间窗口统计更新完成")

        except Exception as e:
            logger.error(f"历史数据回填失败: {e}")
            raise
        finally:
            await db.close()


if __name__ == "__main__":
    print("\n历史数据回填脚本")
    print("此脚本将从 repository_views 和 file_downloads 表回填数据到 repository_daily_stats 表")
    print("=" * 60)

    # 提示用户
    response = input("\n是否开始回填？这可能需要几分钟时间。(y/N): ")
    if response.lower() == 'y':
        asyncio.run(main())
    else:
        print("已取消回填")
