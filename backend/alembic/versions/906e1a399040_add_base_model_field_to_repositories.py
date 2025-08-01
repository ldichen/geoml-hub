"""add_base_model_field_to_repositories

Revision ID: 906e1a399040
Revises: 006
Create Date: 2025-07-21 22:34:26.088752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '906e1a399040'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 base_model 字段到 repositories 表
    op.add_column('repositories', sa.Column('base_model', sa.String(255), nullable=True))


def downgrade() -> None:
    # 删除 base_model 字段
    op.drop_column('repositories', 'base_model')