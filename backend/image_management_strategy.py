#!/usr/bin/env python3
"""
镜像管理策略 - 智能化Docker镜像管理

这个模块实现了以下策略：
1. 检查优先：避免不必要的删除操作
2. 版本管理：支持镜像版本策略
3. 空间优化：定期清理未使用镜像
4. 错误处理：优雅处理各种异常情况
"""

import asyncio
from typing import Dict, List, Optional
from app.services.mmanager_client import mmanager_client
from app.database import get_async_db
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class ImageManagementStrategy:
    """智能镜像管理策略"""
    
    def __init__(self):
        self.max_images_per_controller = 50  # 每个控制器最大镜像数
        self.cleanup_threshold = 0.8  # 清理阈值(80%)
        
    async def smart_image_check_and_remove(
        self, 
        controller_id: str, 
        image_name: str,
        force: bool = False
    ) -> Dict[str, any]:
        """
        智能镜像检查和删除策略
        
        Args:
            controller_id: 控制器ID
            image_name: 镜像名称
            force: 是否强制删除
            
        Returns:
            操作结果字典
        """
        result = {
            "image_name": image_name,
            "controller_id": controller_id,
            "existed": False,
            "removed": False,
            "error": None,
            "skip_reason": None
        }
        
        try:
            # 1. 检查镜像是否存在
            logger.info(f"检查镜像是否存在: {image_name}")
            image_info = await mmanager_client.get_image_info(controller_id, image_name)
            
            if not image_info:
                result["skip_reason"] = "镜像不存在，跳过删除"
                logger.info(f"镜像不存在，跳过删除: {image_name}")
                return result
            
            result["existed"] = True
            
            # 2. 检查镜像是否正在被使用
            if not force:
                in_use = await self._check_image_in_use(controller_id, image_name)
                if in_use:
                    result["skip_reason"] = "镜像正在被容器使用，跳过删除"
                    logger.warning(f"镜像正在使用中，跳过删除: {image_name}")
                    return result
            
            # 3. 执行删除
            logger.info(f"开始删除镜像: {image_name}")
            remove_success = await mmanager_client.remove_image(
                controller_id, image_name, force
            )
            
            result["removed"] = remove_success
            
            if remove_success:
                logger.info(f"镜像删除成功: {image_name}")
            else:
                result["error"] = "删除操作返回失败"
                logger.error(f"镜像删除失败: {image_name}")
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"镜像管理操作异常: {e}")
            
        return result
    
    async def _check_image_in_use(self, controller_id: str, image_name: str) -> bool:
        """检查镜像是否正在被容器使用"""
        try:
            containers = await mmanager_client.list_containers(controller_id, all_containers=True)
            
            if not containers or "containers" not in containers:
                return False
                
            for container in containers["containers"]:
                container_image = container.get("image", "")
                if image_name in container_image:
                    # 进一步检查容器状态
                    if container.get("status", "").lower() in ["running", "paused"]:
                        return True
                        
            return False
            
        except Exception as e:
            logger.warning(f"检查镜像使用状态失败: {e}")
            # 保守起见，假设镜像正在使用
            return True
    
    async def cleanup_unused_images(self, controller_id: str) -> Dict[str, any]:
        """清理未使用的镜像"""
        result = {
            "controller_id": controller_id,
            "total_images": 0,
            "cleaned_images": 0,
            "freed_space": "unknown",
            "errors": []
        }
        
        try:
            # 1. 获取所有镜像
            images = await mmanager_client.list_images(controller_id)
            result["total_images"] = len(images)
            
            logger.info(f"控制器 {controller_id} 共有 {len(images)} 个镜像")
            
            # 2. 判断是否需要清理
            if len(images) < self.max_images_per_controller * self.cleanup_threshold:
                logger.info(f"镜像数量未达到清理阈值，跳过清理")
                return result
            
            # 3. 执行系统级清理
            cleanup_result = await mmanager_client.clean_unused_images(controller_id)
            
            if cleanup_result:
                result["freed_space"] = cleanup_result.get("space_freed", "unknown")
                result["cleaned_images"] = cleanup_result.get("images_deleted", 0)
                
                logger.info(f"清理完成: 删除 {result['cleaned_images']} 个镜像，释放空间 {result['freed_space']}")
            
        except Exception as e:
            error_msg = f"清理未使用镜像失败: {e}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
            
        return result
    
    async def ensure_image_with_fallback(
        self,
        controller_id: str,
        primary_image: str,
        fallback_images: List[str],
        harbor_auth: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        确保镜像可用，支持备用镜像策略
        
        Args:
            controller_id: 控制器ID
            primary_image: 主要镜像名称
            fallback_images: 备用镜像列表
            harbor_auth: Harbor认证信息
            
        Returns:
            操作结果
        """
        result = {
            "controller_id": controller_id,
            "requested_image": primary_image,
            "used_image": None,
            "success": False,
            "attempts": []
        }
        
        # 尝试主要镜像
        images_to_try = [primary_image] + fallback_images
        
        for i, image_name in enumerate(images_to_try):
            attempt = {
                "image": image_name,
                "type": "primary" if i == 0 else "fallback",
                "success": False,
                "error": None
            }
            
            try:
                logger.info(f"尝试确保镜像可用: {image_name} ({'主要' if i == 0 else '备用'})")
                
                success = await mmanager_client.ensure_image_available(
                    controller_id, image_name, harbor_auth
                )
                
                attempt["success"] = success
                
                if success:
                    result["used_image"] = image_name
                    result["success"] = True
                    logger.info(f"成功使用镜像: {image_name}")
                    break
                    
            except Exception as e:
                attempt["error"] = str(e)
                logger.warning(f"镜像 {image_name} 不可用: {e}")
                
            finally:
                result["attempts"].append(attempt)
        
        if not result["success"]:
            logger.error(f"所有镜像都不可用: {images_to_try}")
            
        return result

# 便捷函数
async def smart_cleanup_before_pull(
    controller_id: str, 
    image_name: str, 
    force: bool = False
) -> bool:
    """
    拉取前的智能清理
    
    Returns:
        是否需要继续拉取
    """
    strategy = ImageManagementStrategy()
    result = await strategy.smart_image_check_and_remove(
        controller_id, image_name, force
    )
    
    # 如果镜像已存在且删除失败，可能需要处理
    if result["existed"] and not result["removed"] and not result["skip_reason"]:
        logger.warning(f"镜像存在但删除失败，可能导致拉取冲突: {image_name}")
        return False
        
    return True

async def periodic_cleanup_task():
    """定期清理任务，可以在后台运行"""
    logger.info("开始执行定期镜像清理任务")
    
    try:
        async for db in get_async_db():
            # 获取所有控制器
            controllers_status = await mmanager_client.get_controller_status(db)
            controllers_list = controllers_status.get('controllers', [])
            
            strategy = ImageManagementStrategy()
            
            for controller_info in controllers_list:
                if controller_info.get('status') == 'healthy':
                    controller_id = controller_info['id']
                    
                    try:
                        cleanup_result = await strategy.cleanup_unused_images(controller_id)
                        logger.info(f"控制器 {controller_id} 清理结果: {cleanup_result}")
                        
                    except Exception as e:
                        logger.error(f"控制器 {controller_id} 定期清理失败: {e}")
            
            break  # 只需要一个数据库连接
            
    except Exception as e:
        logger.error(f"定期清理任务失败: {e}")

if __name__ == "__main__":
    # 测试镜像管理策略
    asyncio.run(periodic_cleanup_task())