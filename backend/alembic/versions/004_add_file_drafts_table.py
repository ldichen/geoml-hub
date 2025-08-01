"""Add file_drafts table

Revision ID: 004
Revises: 003
Create Date: 2025-07-20 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create file_drafts table
    op.create_table(
        'file_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('draft_content', sa.Text(), nullable=True),
        sa.Column('base_version_id', sa.Integer(), nullable=False),
        sa.Column('cursor_position', sa.JSON(), nullable=True),
        sa.Column('selection_range', sa.JSON(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_auto_saved', sa.Boolean(), nullable=True),
        sa.Column('auto_save_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_access', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['base_version_id'], ['file_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_file_drafts_id'), 'file_drafts', ['id'], unique=False)
    op.create_index('ix_file_drafts_file_id_user_id', 'file_drafts', ['file_id', 'user_id'], unique=True)
    op.create_index('ix_file_drafts_user_id', 'file_drafts', ['user_id'], unique=False)
    op.create_index('ix_file_drafts_updated_at', 'file_drafts', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_file_drafts_updated_at', table_name='file_drafts')
    op.drop_index('ix_file_drafts_user_id', table_name='file_drafts')
    op.drop_index('ix_file_drafts_file_id_user_id', table_name='file_drafts')
    op.drop_index(op.f('ix_file_drafts_id'), table_name='file_drafts')
    
    # Drop table
    op.drop_table('file_drafts')