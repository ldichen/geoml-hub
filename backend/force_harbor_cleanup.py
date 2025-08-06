#!/usr/bin/env python3
"""
强制Harbor清理脚本 - 直接删除所有可见的仓库
"""

import asyncio
import logging
from app.services.harbor_client import HarborClient
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从截图中看到的仓库列表
KNOWN_REPOSITORIES = [
    "redis-7-1",
    "redis-7-19", 
    "redis-7-18",
    "minio-latest-17",
    "opengms/prithvi-eo-1.0-100m-sen1floods11"
]

async def force_cleanup_known_repositories():
    """强制删除已知的仓库"""
    logger.info("开始强制清理已知仓库...")
    
    try:
        async with HarborClient() as harbor_client:
            # 检查Harbor连接
            is_connected = await harbor_client.test_connection()
            if not is_connected:
                logger.error("Harbor连接失败")
                return False
            
            logger.info("Harbor连接成功")
            project_name = settings.harbor_default_project
            
            # 方法1: 删除已知仓库
            deleted_count = 0
            failed_count = 0
            
            for repo_name in KNOWN_REPOSITORIES:
                try:
                    logger.info(f"尝试删除仓库: {repo_name}")
                    
                    # 处理带有斜杠的仓库名
                    if '/' in repo_name:
                        # 对于 opengms/prithvi-eo-1.0-100m-sen1floods11 这样的名称
                        # 需要URL编码斜杠
                        encoded_repo_name = repo_name.replace('/', '%2F')
                        success = await harbor_client.delete_repository(project_name, encoded_repo_name)
                        if not success:
                            # 尝试不编码的版本
                            success = await harbor_client.delete_repository(project_name, repo_name)
                    else:
                        success = await harbor_client.delete_repository(project_name, repo_name)
                    
                    if success:
                        deleted_count += 1
                        logger.info(f"✅ 成功删除仓库: {repo_name}")
                    else:
                        failed_count += 1
                        logger.error(f"❌ 删除仓库失败: {repo_name}")
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"删除仓库时出错: {repo_name} - {e}")
            
            logger.info(f"已知仓库清理结果: 成功 {deleted_count}, 失败 {failed_count}")
            
            # 方法2: 再次获取仓库列表并删除剩余的
            await asyncio.sleep(2)  # 等待Harbor更新
            remaining_repos = await harbor_client.list_repositories(project_name)
            logger.info(f"获取剩余仓库: {len(remaining_repos)} 个")
            
            if remaining_repos:
                logger.info("删除剩余仓库:")
                for repo in remaining_repos:
                    try:
                        repo_full_name = repo['name']
                        logger.info(f"删除剩余仓库: {repo_full_name}")
                        
                        # 提取仓库名（去除项目前缀）
                        if '/' in repo_full_name:
                            repo_short_name = repo_full_name.split('/', 1)[1]  # 只分割第一个斜杠
                        else:
                            repo_short_name = repo_full_name
                        
                        # 尝试URL编码版本
                        encoded_name = repo_short_name.replace('/', '%2F')
                        success = await harbor_client.delete_repository(project_name, encoded_name)
                        
                        if not success:
                            # 尝试原名称
                            success = await harbor_client.delete_repository(project_name, repo_short_name)
                        
                        if success:
                            logger.info(f"✅ 成功删除剩余仓库: {repo_full_name}")
                        else:
                            logger.error(f"❌ 删除剩余仓库失败: {repo_full_name}")
                        
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"删除剩余仓库时出错: {repo.get('name', 'unknown')} - {e}")
            
            # 最终验证
            await asyncio.sleep(2)
            final_repos = await harbor_client.list_repositories(project_name)
            logger.info(f"最终剩余仓库数量: {len(final_repos)}")
            
            if final_repos:
                logger.warning("仍有仓库未被清理:")
                for repo in final_repos:
                    logger.warning(f"  - {repo['name']}")
                    
                # 显示详细的仓库信息以便调试
                for repo in final_repos:
                    logger.info(f"仓库详情: {repo}")
                
                return False
            else:
                logger.info("✅ 所有仓库已成功清理")
                return True
            
    except Exception as e:
        logger.error(f"强制清理失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🚨 强制Harbor清理工具")
    print("🚨 将强制删除Harbor中所有可见的仓库")
    print("=" * 60)
    
    confirm = input("输入 'YES' 确认强制清理: ")
    if confirm != 'YES':
        print("清理操作已取消")
        return
    
    success = await force_cleanup_known_repositories()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Harbor强制清理完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Harbor清理未完全成功，请查看日志")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())