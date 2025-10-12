"""add repository daily stats table

Revision ID: d59851a62005
Revises: db1f3d67777c
Create Date: 2025-10-11 19:17:36.601052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd59851a62005'
down_revision = 'db1f3d67777c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 repository_daily_stats 表
    op.create_table(
        'repository_daily_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('views_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('downloads_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('unique_visitors', sa.Integer(), server_default='0', nullable=False),
        sa.Column('unique_downloaders', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'date', name='unique_repo_date')
    )

    # 创建索引
    op.create_index('idx_repo_daily_stats_date', 'repository_daily_stats', ['date'])
    op.create_index('idx_repo_daily_stats_repo_id', 'repository_daily_stats', ['repository_id'])
    op.create_index('idx_repo_daily_stats_repo_date', 'repository_daily_stats', ['repository_id', 'date'])

    # 更新 repositories 表，添加时间窗口统计字段
    op.add_column('repositories', sa.Column('views_count_7d', sa.Integer(), server_default='0', nullable=False))
    op.add_column('repositories', sa.Column('downloads_count_7d', sa.Integer(), server_default='0', nullable=False))
    op.add_column('repositories', sa.Column('views_count_30d', sa.Integer(), server_default='0', nullable=False))
    op.add_column('repositories', sa.Column('downloads_count_30d', sa.Integer(), server_default='0', nullable=False))
    op.add_column('repositories', sa.Column('trending_score', sa.Float(), server_default='0', nullable=False))
    op.add_column('repositories', sa.Column('trending_updated_at', sa.DateTime(timezone=True), nullable=True))

    # 注意: 保持 views_count 和 downloads_count 字段名不变，以保持向后兼容
    # 这些字段代表总计数，新的 _7d 和 _30d 字段代表时间窗口统计


def downgrade() -> None:
    # 删除新增字段
    op.drop_column('repositories', 'trending_updated_at')
    op.drop_column('repositories', 'trending_score')
    op.drop_column('repositories', 'downloads_count_30d')
    op.drop_column('repositories', 'views_count_30d')
    op.drop_column('repositories', 'downloads_count_7d')
    op.drop_column('repositories', 'views_count_7d')

    # 删除索引
    op.drop_index('idx_repo_daily_stats_repo_date', table_name='repository_daily_stats')
    op.drop_index('idx_repo_daily_stats_repo_id', table_name='repository_daily_stats')
    op.drop_index('idx_repo_daily_stats_date', table_name='repository_daily_stats')

    # 删除表
    op.drop_table('repository_daily_stats')