"""drop repository_views and file_downloads tables

Revision ID: f9284d7ca0b0
Revises: d59851a62005
Create Date: 2025-10-12 18:46:16.744369

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9284d7ca0b0'
down_revision = 'd59851a62005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除 repository_views 表
    op.drop_table('repository_views')

    # 删除 file_downloads 表
    op.drop_table('file_downloads')


def downgrade() -> None:
    # 如果需要回滚，重新创建这两个表
    # repository_views 表
    op.create_table(
        'repository_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_repo_views_repo_id', 'repository_views', ['repository_id'])
    op.create_index('idx_repo_views_created_at', 'repository_views', ['created_at'])

    # file_downloads 表
    op.create_table(
        'file_downloads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('bytes_transferred', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_file_downloads_file_id', 'file_downloads', ['file_id'])
    op.create_index('idx_file_downloads_started_at', 'file_downloads', ['started_at'])