"""
统计数据定时任务服务
用于定期更新仓库的时间窗口统计数据
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Repository, RepositoryDailyStats
from app.database import get_async_db
from datetime import date, timedelta, datetime
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


async def update_repository_trending_stats(db: AsyncSession):
    """更新所有仓库的时间窗口统计

    计算最近7天和30天的浏览量、下载量，并更新到 Repository 表
    建议每小时或每天运行一次
    """
    try:
        today = date.today()
        date_7d_ago = today - timedelta(days=7)
        date_30d_ago = today - timedelta(days=30)

        # 获取所有活跃仓库
        repo_query = select(Repository).where(Repository.is_active == True)
        repo_result = await db.execute(repo_query)
        repositories = repo_result.scalars().all()

        logger.info(f"开始更新 {len(repositories)} 个仓库的时间窗口统计...")

        updated_count = 0
        for repo in repositories:
            try:
                # 计算最近7天统计
                stats_7d_query = select(
                    func.sum(RepositoryDailyStats.views_count).label('views'),
                    func.sum(RepositoryDailyStats.downloads_count).label('downloads')
                ).where(
                    RepositoryDailyStats.repository_id == repo.id,
                    RepositoryDailyStats.date >= date_7d_ago,
                    RepositoryDailyStats.date <= today
                )
                stats_7d_result = await db.execute(stats_7d_query)
                stats_7d = stats_7d_result.one()

                # 计算最近30天统计
                stats_30d_query = select(
                    func.sum(RepositoryDailyStats.views_count).label('views'),
                    func.sum(RepositoryDailyStats.downloads_count).label('downloads')
                ).where(
                    RepositoryDailyStats.repository_id == repo.id,
                    RepositoryDailyStats.date >= date_30d_ago,
                    RepositoryDailyStats.date <= today
                )
                stats_30d_result = await db.execute(stats_30d_query)
                stats_30d = stats_30d_result.one()

                # 更新仓库字段
                repo.views_count_7d = stats_7d.views or 0
                repo.downloads_count_7d = stats_7d.downloads or 0
                repo.views_count_30d = stats_30d.views or 0
                repo.downloads_count_30d = stats_30d.downloads or 0

                # 计算综合热度分数（可以根据需要调整权重）
                repo.trending_score = (
                    repo.views_count_7d * 1.0 +      # 7天浏览量权重
                    repo.downloads_count_7d * 3.0 +  # 7天下载量权重（更重要）
                    repo.stars_count * 2.0           # 星标数权重
                )

                repo.trending_updated_at = datetime.now()
                updated_count += 1

            except Exception as e:
                logger.error(f"更新仓库 {repo.full_name} 统计失败: {e}")
                continue

        await db.commit()
        logger.info(f"成功更新 {updated_count} 个仓库的时间窗口统计")
        return updated_count

    except Exception as e:
        logger.error(f"更新时间窗口统计失败: {e}")
        await db.rollback()
        raise


async def calculate_unique_visitors(db: AsyncSession, target_date: date = None):
    """计算指定日期的独立访客数（已废弃）

    注意：由于已删除 repository_views 表，此函数不再使用
    独立访客数现在通过模拟数据或其他方式生成
    """
    logger.warning("calculate_unique_visitors 已废弃，repository_views 表已删除")
    return 0


# 定时任务调度函数
async def run_scheduled_tasks():
    """运行所有定时任务

    这个函数应该被 APScheduler 或类似的任务调度器调用
    """
    async for db in get_async_db():
        try:
            # 任务1: 更新时间窗口统计（每小时运行）
            await update_repository_trending_stats(db)

            # 任务2: 计算前一天的独立访客数（每天运行一次）
            yesterday = date.today() - timedelta(days=1)
            await calculate_unique_visitors(db, yesterday)

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}")
        finally:
            await db.close()


# 用于手动触发的函数
async def manual_update_stats():
    """手动更新统计数据

    可以通过 CLI 或管理 API 调用
    """
    async for db in get_async_db():
        try:
            logger.info("=== 开始手动更新统计数据 ===")

            # 更新时间窗口统计
            count1 = await update_repository_trending_stats(db)
            logger.info(f"✓ 更新了 {count1} 个仓库的时间窗口统计")

            # 计算最近7天的独立访客数
            for days_ago in range(7):
                target_date = date.today() - timedelta(days=days_ago)
                count2 = await calculate_unique_visitors(db, target_date)
                logger.info(f"✓ 计算了 {count2} 个仓库在 {target_date} 的独立访客数")

            logger.info("=== 统计数据更新完成 ===")

        except Exception as e:
            logger.error(f"手动更新统计失败: {e}")
            raise
        finally:
            await db.close()


if __name__ == "__main__":
    # 可以直接运行这个脚本来手动更新统计
    asyncio.run(manual_update_stats())
