"""Add is_active field to file_templates

Revision ID: 006
Revises: 19f0080584be
Create Date: 2025-07-20 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '19f0080584be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active field to file_templates table
    op.add_column('file_templates', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    
    # Set default value for existing records
    op.execute("UPDATE file_templates SET is_active = TRUE WHERE is_active IS NULL")


def downgrade() -> None:
    # Remove is_active field
    op.drop_column('file_templates', 'is_active')