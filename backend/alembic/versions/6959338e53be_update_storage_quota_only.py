"""update_storage_quota_only

Revision ID: 6959338e53be
Revises: 906e1a399040
Create Date: 2025-07-22 15:08:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6959338e53be'
down_revision = '906e1a399040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing users' storage quota from 5GB to 500GB (536870912000 bytes)
    op.execute("UPDATE users SET storage_quota = 536870912000 WHERE storage_quota = 5368709120")


def downgrade() -> None:
    # Revert storage quota from 500GB back to 5GB (5368709120 bytes)
    op.execute("UPDATE users SET storage_quota = 5368709120 WHERE storage_quota = 536870912000")