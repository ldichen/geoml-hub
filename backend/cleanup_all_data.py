#!/usr/bin/env python3
"""
数据清理脚本 - 清理所有images、model_services和Harbor数据
警告：此脚本将删除所有相关数据，不可恢复！

包含的清理内容：
- Images (镜像及构建日志)
- Model Services (模型服务及相关数据)
- Harbor镜像和仓库数据
- mManager控制器容器

注意：不会删除数据库中的repositories表，只清理Harbor中的repository
"""

import asyncio
from sqlalchemy import text

from app.database import async_engine, get_async_db
from app.services.harbor_client import HarborClient
from app.config import settings

# 配置日志
from app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def cleanup_database():
    """清理数据库中的相关表数据"""
    logger.info("开始清理数据库数据...")

    async with async_engine.begin() as conn:
        try:
            # 1. 清理service相关表（注意顺序，先清理外键关联的表）
            logger.info("清理 service_health_checks 表...")
            await conn.execute(text("DELETE FROM service_health_checks"))

            logger.info("清理 service_logs 表...")
            await conn.execute(text("DELETE FROM service_logs"))

            logger.info("清理 model_services 表...")
            await conn.execute(text("DELETE FROM model_services"))

            # 2. 清理image相关表
            logger.info("清理 image_build_logs 表...")
            await conn.execute(text("DELETE FROM image_build_logs"))

            logger.info("清理 images 表...")
            await conn.execute(text("DELETE FROM images"))

            # 3. 重置序列（如果使用PostgreSQL）
            logger.info("重置序列...")
            await conn.execute(text("ALTER SEQUENCE images_id_seq RESTART WITH 1"))
            await conn.execute(
                text("ALTER SEQUENCE model_services_id_seq RESTART WITH 1")
            )
            await conn.execute(
                text("ALTER SEQUENCE service_logs_id_seq RESTART WITH 1")
            )
            await conn.execute(
                text("ALTER SEQUENCE service_health_checks_id_seq RESTART WITH 1")
            )
            await conn.execute(
                text("ALTER SEQUENCE image_build_logs_id_seq RESTART WITH 1")
            )

            logger.info("数据库清理完成！")

        except Exception as e:
            logger.error(f"数据库清理失败: {e}")
            raise


async def cleanup_harbor():
    """清理Harbor中的所有镜像"""
    logger.info("开始清理Harbor数据...")

    try:
        async with HarborClient() as harbor_client:
            # 检查Harbor连接
            is_connected = await harbor_client.test_connection()
            if not is_connected:
                logger.error("Harbor连接失败")
                return

            logger.info("Harbor连接成功，开始获取所有镜像...")

            # 直接清理Harbor仓库（删除repository会同时删除其下的所有镜像）
            project_name = settings.harbor_default_project
            logger.info("开始清理Harbor仓库（将同时删除所有镜像）...")
            await cleanup_harbor_repositories(harbor_client, project_name)

    except Exception as e:
        logger.error(f"Harbor清理失败: {e}")
        raise


async def cleanup_harbor_repositories(harbor_client: HarborClient, project_name: str):
    """清理Harbor项目中的所有仓库（包括其下的镜像）"""
    try:
        # 获取项目中所有仓库
        repositories = await harbor_client.list_repositories(project_name)

        if not repositories:
            logger.info("没有找到Harbor仓库需要清理")
            return

        logger.info(
            f"找到 {len(repositories)} 个Harbor仓库，开始清理（将同时删除仓库下的所有镜像）..."
        )

        deleted_repos = 0
        failed_repos = 0

        for repo in repositories:
            repo_name = repo.get("name", "")
            if not repo_name:
                continue

            try:
                # 删除仓库（包括路径编码处理）
                repo_path = repo_name.split("/")[-1] if "/" in repo_name else repo_name
                logger.info(f"删除Harbor仓库（含所有镜像）: {repo_name}")
                success = await harbor_client.delete_repository(project_name, repo_path)

                if success:
                    deleted_repos += 1
                    logger.info(f"成功删除Harbor仓库: {repo_name}")
                else:
                    failed_repos += 1
                    logger.warning(f"删除Harbor仓库失败: {repo_name}")

                # 避免API调用过于频繁
                await asyncio.sleep(0.2)

            except Exception as e:
                failed_repos += 1
                logger.error(f"删除Harbor仓库 {repo_name} 时出错: {e}")

        logger.info(
            f"Harbor仓库清理完成: 成功删除 {deleted_repos} 个仓库（含其下所有镜像）, 失败 {failed_repos} 个"
        )

    except Exception as e:
        logger.error(f"Harbor仓库清理失败: {e}")


async def cleanup_mmanager_controllers():
    """清理mManager控制器中的容器（可选）"""
    logger.info("开始清理mManager控制器数据...")

    try:
        from app.services.mmanager_client import mmanager_client

        # 获取数据库连接
        async for db in get_async_db():
            # 获取所有控制器状态
            controllers_status = await mmanager_client.get_controller_status(db)

            if not controllers_status:
                logger.info("没有找到活跃的控制器")
                return

            # 清理每个控制器上的容器
            controllers_list = controllers_status.get("controllers", [])
            for controller_info in controllers_list:
                controller_id = controller_info["id"]
                if controller_info.get("status") != "healthy":
                    logger.warning(f"控制器 {controller_id} 状态不健康，跳过清理")
                    continue

                try:
                    client = mmanager_client.get_client(controller_id)
                    if client:
                        # 获取所有容器
                        containers = await client.list_containers()

                        # 删除所有带有geoml标签的容器
                        for container in containers:
                            if (
                                container.get("labels", {}).get("geoml.managed")
                                == "true"
                            ):
                                container_id = container.get("id")
                                logger.info(
                                    f"删除容器: {container_id} 在控制器 {controller_id}"
                                )
                                await client.remove_container(container_id, force=True)

                except Exception as e:
                    logger.error(f"清理控制器 {controller_id} 失败: {e}")

            break  # 只需要一个数据库连接

        logger.info("mManager控制器清理完成！")

    except Exception as e:
        logger.error(f"mManager控制器清理失败: {e}")


async def main():
    """主清理函数"""
    print("=" * 70)
    print("🚨 警告：即将删除所有 images、model_services 和 Harbor 数据！")
    print("🚨 包括：镜像、服务、Harbor镜像和仓库、mManager容器")
    print("🚨 注意：不会删除数据库repositories表，只清理Harbor中的repository")
    print("🚨 此操作不可恢复，请确认你真的要继续！")
    print("=" * 70)

    confirm = input("输入 'YES' 确认清理所有数据: ")
    if confirm != "YES":
        print("清理操作已取消")
        return

    try:
        # 1. 清理数据库
        logger.info("步骤 1/3: 清理数据库...")
        await cleanup_database()

        # 2. 清理Harbor
        logger.info("步骤 2/3: 清理Harbor...")
        await cleanup_harbor()

        # 3. 清理mManager控制器（可选）
        logger.info("步骤 3/3: 清理mManager控制器...")
        await cleanup_mmanager_controllers()

        print("\n" + "=" * 60)
        print("✅ 所有数据清理完成！")
        print("✅ 可以开始重新测试了")
        print("=" * 60)

    except Exception as e:
        logger.error(f"清理过程中出现错误: {e}")
        print(f"\n❌ 清理失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
