#!/usr/bin/env python3
"""
使用智能镜像管理策略的测试脚本
"""

import asyncio
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings
from app.utils.logger import setup_logging, get_logger, set_docker_operations_quiet

# 设置日志
setup_logging()
set_docker_operations_quiet()  # 减少Docker操作的详细输出
logger = get_logger(__name__)

async def smart_image_test():
    """使用智能镜像管理策略的测试"""
    print("=== 智能镜像管理测试 ===")
    
    try:
        # 获取数据库连接
        async for db in get_async_db():
            # 初始化mManager
            if not mmanager_client.controllers:
                await mmanager_client.initialize(db)
            
            # 获取控制器
            controllers_status = await mmanager_client.get_controller_status(db)
            controllers_list = controllers_status.get('controllers', [])
            
            if not controllers_list:
                print("❌ 没有可用的控制器")
                return
            
            controller_id = controllers_list[0]['id']
            print(f"使用控制器: {controller_id}")
            
            # 准备测试数据
            test_image = f"{settings.harbor_url.split('://')[-1]}/geoml-hub/redis-7-1:latest"
            harbor_auth = {
                "serveraddress": str(settings.harbor_url.split('://')[-1]),
                "username": str(settings.harbor_username),
                "password": str(settings.harbor_password)
            }
            
            print(f"测试镜像: {test_image}")
            
            # 🎯 智能镜像管理策略
            await smart_image_cleanup_and_pull(controller_id, test_image, harbor_auth)
            
            break  # 只需要一个数据库连接
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def smart_image_cleanup_and_pull(controller_id: str, image_name: str, harbor_auth: dict):
    """智能镜像清理和拉取"""
    
    print(f"\n=== 🎯 智能镜像管理策略 ===")
    
    # 1. 检查镜像是否存在
    print("1️⃣ 检查镜像是否存在...")
    image_exists = False
    in_use = False
    
    try:
        image_info = await mmanager_client.get_image_info(controller_id, image_name)
        if image_info:
            image_exists = True
            print(f"✅ 镜像存在: {image_name}")
            
            # 2. 检查是否被容器使用
            print("2️⃣ 检查镜像使用状态...")
            containers = await mmanager_client.list_containers(controller_id, all_containers=True)
            
            if containers and "containers" in containers:
                for container in containers["containers"]:
                    container_image = container.get("image", "")
                    if image_name in container_image:
                        status = container.get("status", "").lower()
                        if status in ["running", "paused"]:
                            in_use = True
                            print(f"⚠️  镜像正在被容器使用: {container.get('name', 'unknown')}")
                            break
            
            if not in_use:
                print("✅ 镜像未被使用，可以安全删除")
        else:
            print(f"ℹ️  镜像不存在: {image_name}")
            
    except Exception as e:
        print(f"ℹ️  镜像检查失败（可能不存在）: {e}")
    
    # 3. 智能删除决策
    if image_exists:
        print("3️⃣ 执行智能删除...")
        if in_use:
            print("🛡️  跳过删除：镜像正在使用中")
            print("💡 提示：如果需要强制删除，请先停止相关容器")
        else:
            try:
                remove_success = await mmanager_client.remove_image(controller_id, image_name, force=False)
                if remove_success:
                    print("✅ 镜像删除成功")
                    await asyncio.sleep(2)  # 等待清理完成
                else:
                    print("❌ 镜像删除失败")
            except Exception as e:
                print(f"❌ 删除操作异常: {e}")
    else:
        print("3️⃣ 跳过删除：镜像不存在")
    
    # 4. 确保镜像可用
    print("4️⃣ 确保镜像可用...")
    try:
        start_time = asyncio.get_event_loop().time()
        
        image_available = await mmanager_client.ensure_image_available(
            controller_id, image_name, harbor_auth
        )
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        if image_available:
            print(f"✅ 镜像现在可用，总耗时: {elapsed:.2f}秒")
        else:
            print(f"❌ 镜像获取失败，耗时: {elapsed:.2f}秒")
            
    except Exception as e:
        print(f"❌ 镜像可用性确保失败: {e}")
    
    # 5. 最终验证
    print("5️⃣ 最终验证...")
    try:
        final_check = await mmanager_client.get_image_info(controller_id, image_name)
        if final_check:
            print("✅ 最终验证成功：镜像可用")
            print(f"📊 镜像信息: ID={final_check.get('id', 'unknown')[:12]}...")
        else:
            print("❌ 最终验证失败：镜像不可用")
    except Exception as e:
        print(f"❌ 最终验证异常: {e}")
    
    print(f"\n🎉 智能镜像管理测试完成！")

async def cleanup_all_test_images():
    """清理所有测试镜像（可选功能）"""
    print("\n=== 🧹 清理所有测试镜像 ===")
    
    try:
        async for db in get_async_db():
            if not mmanager_client.controllers:
                await mmanager_client.initialize(db)
            
            controllers_status = await mmanager_client.get_controller_status(db)
            controllers_list = controllers_status.get('controllers', [])
            
            for controller_info in controllers_list:
                if controller_info.get('status') == 'healthy':
                    controller_id = controller_info['id']
                    print(f"清理控制器 {controller_id} 的测试镜像...")
                    
                    try:
                        cleanup_result = await mmanager_client.clean_unused_images(controller_id)
                        if cleanup_result:
                            print(f"✅ 清理成功: {cleanup_result}")
                        else:
                            print("ℹ️  无需清理或清理完成")
                    except Exception as e:
                        print(f"❌ 清理失败: {e}")
            
            break
            
    except Exception as e:
        print(f"❌ 清理操作失败: {e}")

if __name__ == "__main__":
    # 选择运行模式
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        # 清理模式
        asyncio.run(cleanup_all_test_images())
    else:
        # 正常测试模式
        asyncio.run(smart_image_test())