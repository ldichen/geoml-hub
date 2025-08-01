#!/usr/bin/env python3
"""
初始化分类数据的脚本
"""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.classification import Classification


async def init_classifications():
    """初始化三级分类数据"""
    
    classifications_data = [
        # 一级分类
        {"name": "计算机视觉", "level": 1, "parent_id": None},
        {"name": "自然语言处理", "level": 1, "parent_id": None},
        {"name": "地理空间分析", "level": 1, "parent_id": None},
        
        # 二级分类 - 计算机视觉
        {"name": "图像分类", "level": 2, "parent_name": "计算机视觉"},
        {"name": "目标检测", "level": 2, "parent_name": "计算机视觉"},
        {"name": "语义分割", "level": 2, "parent_name": "计算机视觉"},
        
        # 二级分类 - 自然语言处理
        {"name": "文本分类", "level": 2, "parent_name": "自然语言处理"},
        {"name": "命名实体识别", "level": 2, "parent_name": "自然语言处理"},
        {"name": "机器翻译", "level": 2, "parent_name": "自然语言处理"},
        
        # 二级分类 - 地理空间分析
        {"name": "遥感影像分析", "level": 2, "parent_name": "地理空间分析"},
        {"name": "地理信息系统", "level": 2, "parent_name": "地理空间分析"},
        {"name": "时空数据挖掘", "level": 2, "parent_name": "地理空间分析"},
        
        # 三级分类 - 图像分类
        {"name": "卫星影像分类", "level": 3, "parent_name": "图像分类"},
        {"name": "航拍影像分类", "level": 3, "parent_name": "图像分类"},
        {"name": "地面影像分类", "level": 3, "parent_name": "图像分类"},
        
        # 三级分类 - 目标检测
        {"name": "建筑物检测", "level": 3, "parent_name": "目标检测"},
        {"name": "车辆检测", "level": 3, "parent_name": "目标检测"},
        {"name": "植被检测", "level": 3, "parent_name": "目标检测"},
        
        # 三级分类 - 遥感影像分析
        {"name": "土地利用分类", "level": 3, "parent_name": "遥感影像分析"},
        {"name": "变化检测", "level": 3, "parent_name": "遥感影像分析"},
        {"name": "特征提取", "level": 3, "parent_name": "遥感影像分析"},
    ]
    
    async with AsyncSessionLocal() as db:
        # 检查是否已经有数据
        query = select(Classification)
        result = await db.execute(query)
        existing = result.scalars().all()
        
        if existing:
            print(f"数据库中已存在 {len(existing)} 个分类，跳过初始化")
            return
        
        print("开始初始化分类数据...")
        
        # 创建名称到ID的映射
        name_to_id = {}
        
        # 按级别创建分类
        for level in [1, 2, 3]:
            level_classifications = [c for c in classifications_data if c["level"] == level]
            
            for classification_data in level_classifications:
                parent_id = None
                if "parent_name" in classification_data:
                    parent_name = classification_data["parent_name"]
                    parent_id = name_to_id.get(parent_name)
                    if not parent_id:
                        print(f"警告: 找不到父分类 '{parent_name}'")
                        continue
                
                classification = Classification(
                    name=classification_data["name"],
                    level=classification_data["level"],
                    parent_id=parent_id,
                    sort_order=0,
                    is_active=True
                )
                
                db.add(classification)
                await db.flush()  # 获取ID
                
                name_to_id[classification.name] = classification.id
                print(f"创建分类: {classification.name} (级别: {classification.level}, ID: {classification.id})")
        
        await db.commit()
        print("分类数据初始化完成！")


async def show_classifications():
    """显示所有分类"""
    async with AsyncSessionLocal() as db:
        query = select(Classification).order_by(Classification.level, Classification.sort_order, Classification.name)
        result = await db.execute(query)
        classifications = result.scalars().all()
        
        print(f"\n当前数据库中共有 {len(classifications)} 个分类:")
        
        current_level = 0
        for classification in classifications:
            if classification.level != current_level:
                current_level = classification.level
                print(f"\n{'='*10} {current_level}级分类 {'='*10}")
            
            indent = "  " * (classification.level - 1)
            parent_info = f" (父分类ID: {classification.parent_id})" if classification.parent_id else ""
            print(f"{indent}ID: {classification.id}, 名称: {classification.name}{parent_info}")


if __name__ == "__main__":
    async def main():
        await init_classifications()
        await show_classifications()
    
    asyncio.run(main())