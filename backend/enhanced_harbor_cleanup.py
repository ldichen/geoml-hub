#!/usr/bin/env python3
"""
增强版Harbor清理脚本 - 删除所有镜像和空仓库
"""

import asyncio
import logging
from app.services.harbor_client import HarborClient
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def cleanup_all_harbor_data():
    """完全清理Harbor中的所有数据"""
    logger.info("开始完全清理Harbor数据...")
    
    try:
        async with HarborClient() as harbor_client:
            # 检查Harbor连接
            is_connected = await harbor_client.test_connection()
            if not is_connected:
                logger.error("Harbor连接失败")
                return False
            
            logger.info("Harbor连接成功")
            
            # 获取项目名
            project_name = settings.harbor_default_project
            logger.info(f"清理项目: {project_name}")
            
            # 步骤1: 获取所有仓库
            repositories = await harbor_client.list_repositories(project_name)
            logger.info(f"找到 {len(repositories)} 个仓库")
            
            if not repositories:
                logger.info("没有找到仓库，无需清理")
                return True
            
            deleted_repos = 0
            failed_repos = 0
            
            # 步骤2: 删除每个仓库（这会自动删除其中的所有镜像）
            for i, repo in enumerate(repositories, 1):
                try:
                    repo_name = repo['name']
                    # 提取仓库名（去除项目前缀）
                    if '/' in repo_name:
                        short_repo_name = repo_name.split('/')[-1]
                    else:
                        short_repo_name = repo_name
                    
                    logger.info(f"[{i}/{len(repositories)}] 删除仓库: {repo_name}")
                    
                    # 删除整个仓库（包括所有镜像）
                    success = await harbor_client.delete_repository(project_name, short_repo_name)
                    
                    if success:
                        deleted_repos += 1
                        logger.info(f"✅ 成功删除仓库: {repo_name}")
                    else:
                        failed_repos += 1
                        logger.error(f"❌ 删除仓库失败: {repo_name}")
                    
                    # 避免过于频繁的API调用
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    failed_repos += 1
                    logger.error(f"删除仓库时出错: {repo.get('name', 'unknown')} - {e}")
            
            logger.info(f"Harbor清理完成: 成功删除 {deleted_repos} 个仓库, 失败 {failed_repos} 个")
            
            # 步骤3: 验证清理结果
            remaining_repos = await harbor_client.list_repositories(project_name)
            logger.info(f"清理后剩余仓库数量: {len(remaining_repos)}")
            
            if remaining_repos:
                logger.warning("仍有仓库未被清理:")
                for repo in remaining_repos:
                    logger.warning(f"  - {repo['name']}")
                return False
            else:
                logger.info("✅ 所有仓库已成功清理")
                return True
            
    except Exception as e:
        logger.error(f"Harbor清理失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🚨 增强版Harbor清理工具")
    print("🚨 将删除Harbor中所有仓库和镜像数据，此操作不可恢复！")
    print("=" * 60)
    
    confirm = input("输入 'YES' 确认清理Harbor所有数据: ")
    if confirm != 'YES':
        print("清理操作已取消")
        return
    
    success = await cleanup_all_harbor_data()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Harbor完全清理完成！")
        print("✅ 所有仓库和镜像已删除")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Harbor清理失败或不完整，请查看日志")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())