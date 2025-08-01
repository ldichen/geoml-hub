#!/usr/bin/env python3
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import async_engine
from app.models import User, Repository
from datetime import datetime, timedelta, timezone

async def debug_admin_dashboard():
    """调试管理员仪表板查询"""
    
    async with async_engine.begin() as conn:
        session = AsyncSession(conn)
        
        try:
            print("1. 测试用户统计...")
            
            # 用户统计
            total_users_query = select(func.count(User.id)).where(User.is_active == True)
            total_users_result = await session.execute(total_users_query)
            total_users = total_users_result.scalar() or 0
            print(f"总用户数: {total_users}")
            
            # 活跃用户统计
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            print(f"30天前时间: {thirty_days_ago}")
            
            active_users_query = select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    User.last_seen_at >= thirty_days_ago,
                )
            )
            active_users_result = await session.execute(active_users_query)
            active_users = active_users_result.scalar() or 0
            print(f"活跃用户数: {active_users}")
            
            print("\n2. 测试仓库统计...")
            
            # 仓库统计
            total_repos_query = select(func.count(Repository.id)).where(Repository.is_active == True)
            total_repos_result = await session.execute(total_repos_query)
            total_repos = total_repos_result.scalar() or 0
            print(f"总仓库数: {total_repos}")
            
            print("\n3. 测试存储统计...")
            
            # 存储统计查询
            storage_stats_query = select(
                func.sum(User.storage_used).label("total_size"),
                func.count(User.id).label("total_files")
            ).where(User.is_active == True)
            
            storage_result = await session.execute(storage_stats_query)
            storage_stats = storage_result.first()
            
            total_size = getattr(storage_stats, "total_size") or 0
            total_files = getattr(storage_stats, "total_files") or 0
            
            print(f"总存储大小: {total_size}")
            print(f"总文件数: {total_files}")
            
            print("\n✅ 所有查询成功完成")
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(debug_admin_dashboard())