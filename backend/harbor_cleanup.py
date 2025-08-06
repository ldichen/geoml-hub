#!/usr/bin/env python3
"""
Harbor数据清理脚本 - 只清理Harbor中的镜像数据
"""

import asyncio
import logging
from app.services.harbor_client import HarborClient
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def cleanup_harbor_images():
    """清理Harbor中的所有镜像"""
    logger.info("开始清理Harbor镜像数据...")
    
    try:
        async with HarborClient() as harbor_client:
            # 检查Harbor连接
            is_connected = await harbor_client.test_connection()
            if not is_connected:
                logger.error("Harbor连接失败")
                return False
            
            logger.info("Harbor连接成功，开始获取所有镜像...")
            
            # 获取所有项目中的镜像
            project_name = settings.harbor_default_project
            harbor_images = await harbor_client.get_all_harbor_images(project_name)
            
            if not harbor_images:
                logger.info("Harbor中没有找到镜像，无需清理")
                return True
            
            logger.info(f"找到 {len(harbor_images)} 个镜像，开始删除...")
            
            # 删除所有镜像
            deleted_count = 0
            failed_count = 0
            
            for i, image in enumerate(harbor_images, 1):
                try:
                    project_name = image.get('project_name')
                    repository_name = image.get('repository_name')
                    digest = image.get('digest')
                    
                    if not all([project_name, repository_name, digest]):
                        logger.warning(f"镜像信息不完整，跳过: {image}")
                        failed_count += 1
                        continue
                    
                    logger.info(f"[{i}/{len(harbor_images)}] 删除镜像: {project_name}/{repository_name}@{digest}")
                    success = await harbor_client.delete_artifact(project_name, repository_name, digest)
                    
                    if success:
                        deleted_count += 1
                        logger.info(f"✅ 成功删除: {project_name}/{repository_name}@{digest}")
                    else:
                        failed_count += 1
                        logger.error(f"❌ 删除失败: {project_name}/{repository_name}@{digest}")
                    
                    # 避免过于频繁的API调用
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"删除镜像时出错: {e}")
            
            logger.info(f"Harbor清理完成: 成功删除 {deleted_count} 个镜像, 失败 {failed_count} 个")
            return failed_count == 0
            
    except Exception as e:
        logger.error(f"Harbor清理失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🚨 Harbor镜像清理工具")
    print("🚨 将删除Harbor中所有镜像数据，此操作不可恢复！")
    print("=" * 60)
    
    confirm = input("输入 'YES' 确认清理Harbor镜像: ")
    if confirm != 'YES':
        print("清理操作已取消")
        return
    
    success = await cleanup_harbor_images()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Harbor镜像清理完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Harbor镜像清理失败，请查看日志")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())