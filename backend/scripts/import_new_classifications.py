"""
Import new Earth System Science classification structure
Author: Claude
Date: 2025-10-09

This script will:
1. Backup existing classifications (optional)
2. Deactivate old classifications
3. Import new two-level classification system (spheres and processes)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import AsyncSessionLocal
from app.models.classification import Classification
from app.models.repository import RepositoryClassification


# New classification structure
NEW_CLASSIFICATIONS = {
    "Geosphere": [
        "Geomorphological Processes",
        "Geological Structure",
        "Geodynamic Processes",
        "Geochemical Cycles",
        "Geophysical Fields",
        "Soil Processes",
        "Geohazards",
    ],
    "Hydrosphere": [
        "Surface Hydrology",
        "Groundwater",
        "Watershed Processes",
        "Water Quality",
        "Ocean and Coastal Processes",
        "Hydroclimate",
    ],
    "Atmosphere": [
        "Weather Prediction",
        "Climate Change",
        "Atmospheric Composition",
        "Radiation Balance",
        "Atmospheric Dynamics",
        "Atmosphere–Surface Interactions",
    ],
    "Biosphere": [
        "Land Cover",
        "Ecosystem Function",
        "Biogeochemical Cycles",
        "Biodiversity",
        "Ecosystem Resilience",
        "Ecosystem Services",
    ],
    "Cryosphere": [
        "Snow Processes",
        "Glaciers",
        "Sea Ice",
        "Permafrost",
        "Ice Sheet Dynamics",
        "Cryosphere–Climate Interactions",
    ],
    "Anthroposphere": [
        "Urban Systems",
        "Agricultural Systems",
        "Energy Systems",
        "Transportation Systems",
        "Socioeconomic Systems",
        "Human–Environment Interactions",
        "Environmental Governance and Policy",
    ],
}


async def backup_existing_classifications(db: AsyncSession) -> list:
    """备份现有分类数据"""
    print("📦 Backing up existing classifications...")

    result = await db.execute(
        select(Classification).order_by(Classification.level, Classification.sort_order)
    )
    classifications = result.scalars().all()

    backup_data = []
    for c in classifications:
        backup_data.append(
            {
                "id": c.id,
                "name": c.name,
                "level": c.level,
                "parent_id": c.parent_id,
                "sort_order": c.sort_order,
                "is_active": c.is_active,
            }
        )

    print(f"   ✅ Backed up {len(backup_data)} classifications")
    return backup_data


async def deactivate_old_classifications(db: AsyncSession):
    """停用所有旧分类"""
    print("🔒 Deactivating old classifications...")

    await db.execute(update(Classification).values(is_active=False))
    await db.commit()
    print("   ✅ All old classifications deactivated")


async def delete_old_classifications(db: AsyncSession):
    """删除所有旧分类（包括关联关系）"""
    print("🗑️  Deleting old classifications...")

    # 先删除仓库分类关联
    result = await db.execute(select(RepositoryClassification))
    repo_classifications = result.scalars().all()
    count = len(repo_classifications)

    if count > 0:
        print(f"   ⚠️  Found {count} repository-classification associations")
        confirm = input("   Delete these associations? (yes/no): ")
        if confirm.lower() != "yes":
            print("   ❌ Operation cancelled")
            return False

    await db.execute(delete(RepositoryClassification))
    await db.execute(delete(Classification))
    await db.commit()

    print(f"   ✅ Deleted {count} associations and all classifications")
    return True


async def import_new_classifications(db: AsyncSession):
    """导入新分类体系"""
    print("📥 Importing new classification structure...")

    created_count = 0

    for sort_order, (sphere_name, processes) in enumerate(
        NEW_CLASSIFICATIONS.items(), start=1
    ):
        # Create Level 1 (Sphere)
        sphere = Classification(
            name=sphere_name,
            level=1,
            parent_id=None,
            sort_order=sort_order,
            is_active=True,
        )
        db.add(sphere)
        await db.flush()  # Get the sphere ID

        print(f"   ✅ Created: {sphere_name} (Level 1)")
        created_count += 1

        # Create Level 2 (Processes)
        for process_order, process_name in enumerate(processes, start=1):
            process = Classification(
                name=process_name,
                level=2,
                parent_id=sphere.id,
                sort_order=process_order,
                is_active=True,
            )
            db.add(process)
            print(f"      └─ {process_name} (Level 2)")
            created_count += 1

    await db.commit()
    print(f"\n   ✅ Successfully imported {created_count} classifications")


async def verify_import(db: AsyncSession):
    """验证导入结果"""
    print("\n🔍 Verifying import...")

    # Count by level
    result = await db.execute(
        select(Classification).where(Classification.is_active == True)
    )
    all_classifications = result.scalars().all()

    level1_count = sum(1 for c in all_classifications if c.level == 1)
    level2_count = sum(1 for c in all_classifications if c.level == 2)

    print(f"   Level 1 (Spheres): {level1_count}")
    print(f"   Level 2 (Processes): {level2_count}")
    print(f"   Total: {len(all_classifications)}")

    # Show tree structure
    print("\n📊 Classification Tree:")
    for sphere in all_classifications:
        if sphere.level == 1:
            print(f"\n   {sphere.name}")
            children = [c for c in all_classifications if c.parent_id == sphere.id]
            for child in children:
                print(f"      └─ {child.name}")


async def main():
    """主函数"""
    print("=" * 70)
    print("🌍 GeoML-Hub Classification System Update")
    print("=" * 70)
    print("\nThis will replace the existing 3-level classification system")
    print("with a new 2-level Earth System Science classification.\n")

    # Confirm action
    print("Options:")
    print("  1. DELETE old classifications and import new (⚠️  DESTRUCTIVE)")
    print("  2. DEACTIVATE old classifications and import new (Safe, keeps old data)")
    print("  3. Just IMPORT new classifications (keeps old active)")
    print("  4. CANCEL")

    choice = input("\nChoose option (1-4): ").strip()

    if choice == "4":
        print("❌ Operation cancelled")
        return

    async with AsyncSessionLocal() as db:
        try:
            # Backup first
            await backup_existing_classifications(db)

            if choice == "1":
                # Delete old
                success = await delete_old_classifications(db)
                if not success:
                    return
            elif choice == "2":
                # Deactivate old
                await deactivate_old_classifications(db)
            elif choice == "3":
                # Do nothing, just import
                print("ℹ️  Keeping old classifications active")
            else:
                print("❌ Invalid choice")
                return

            # Import new
            await import_new_classifications(db)

            # Verify
            await verify_import(db)

            print("\n" + "=" * 70)
            print("✅ Classification system updated successfully!")
            print("=" * 70)

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
