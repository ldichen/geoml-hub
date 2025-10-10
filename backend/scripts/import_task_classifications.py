"""
Import Task Classifications
Author: Claude
Date: 2025-10-09

This script imports the 8 task classifications for GeoML-Hub.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.task_classification import TaskClassification


# Task classification data
TASK_CLASSIFICATIONS = [
    {
        "name": "Recognition",
        "name_zh": "识别类",
        "description": "Identification and classification of geographic features, objects, and patterns",
        "sort_order": 1,
        "icon": "eye",
    },
    {
        "name": "Monitoring",
        "name_zh": "监测类",
        "description": "Continuous observation and tracking of geographic phenomena and changes",
        "sort_order": 2,
        "icon": "activity",
    },
    {
        "name": "Retrieval",
        "name_zh": "反演类",
        "description": "Inverse estimation of physical parameters from remote sensing observations",
        "sort_order": 3,
        "icon": "rotate-ccw",
    },
    {
        "name": "Simulation & Prediction",
        "name_zh": "模拟预测类",
        "description": "Numerical modeling and forecasting of geographic processes and future states",
        "sort_order": 4,
        "icon": "trending-up",
    },
    {
        "name": "Assessment",
        "name_zh": "评估类",
        "description": "Evaluation and quantification of environmental conditions, resources, and impacts",
        "sort_order": 5,
        "icon": "check-circle",
    },
    {
        "name": "Risk & Early Warning",
        "name_zh": "风险防控类",
        "description": "Hazard identification, risk assessment, and early warning systems",
        "sort_order": 6,
        "icon": "alert-triangle",
    },
    {
        "name": "Decision Support",
        "name_zh": "决策支持类",
        "description": "Information systems and tools for planning and decision-making",
        "sort_order": 7,
        "icon": "compass",
    },
    {
        "name": "Model Analysis",
        "name_zh": "模型解析类",
        "description": "Interpretation, explanation, and analysis of model behaviors and predictions",
        "sort_order": 8,
        "icon": "layers",
    },
]


async def check_existing(db: AsyncSession) -> list:
    """检查已存在的任务分类"""
    result = await db.execute(select(TaskClassification))
    existing = result.scalars().all()
    return existing


async def import_classifications(db: AsyncSession):
    """导入任务分类"""
    print("=" * 70)
    print("🎯 Importing Task Classifications for GeoML-Hub")
    print("=" * 70)

    # Check existing
    existing = await check_existing(db)
    if existing:
        print(f"\n⚠️  Found {len(existing)} existing task classifications:")
        for tc in existing:
            print(f"   - {tc.name} ({tc.name_zh})")

        confirm = input("\n   Delete existing and reimport? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Operation cancelled")
            return

        # Delete existing
        for tc in existing:
            await db.delete(tc)
        await db.commit()
        print("   ✅ Deleted existing classifications")

    # Import new classifications
    print("\n📥 Importing task classifications...")

    for data in TASK_CLASSIFICATIONS:
        task_classification = TaskClassification(**data)
        db.add(task_classification)
        print(f"   ✅ {data['name']} ({data['name_zh']})")

    await db.commit()

    print(f"\n✅ Successfully imported {len(TASK_CLASSIFICATIONS)} task classifications")

    # Verify import
    print("\n🔍 Verification:")
    result = await db.execute(
        select(TaskClassification).order_by(TaskClassification.sort_order)
    )
    all_classifications = result.scalars().all()

    print(f"   Total: {len(all_classifications)}")
    print(f"   Active: {sum(1 for tc in all_classifications if tc.is_active)}")

    print("\n📊 Task Classifications:")
    for tc in all_classifications:
        status = "✓" if tc.is_active else "✗"
        print(f"   {status} [{tc.sort_order}] {tc.name} ({tc.name_zh})")

    print("\n" + "=" * 70)
    print("✅ Task classifications imported successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run database migration: alembic upgrade head")
    print("  2. Start the backend server")
    print("  3. Access API docs: http://localhost:8000/docs")
    print("  4. Test endpoint: GET /api/task-classifications")


async def main():
    """主函数"""
    async with AsyncSessionLocal() as db:
        try:
            await import_classifications(db)
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
