"""add_personal_files_models

Revision ID: fd5028fa4e0f
Revises: 6959338e53be
Create Date: 2025-07-22 15:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fd5028fa4e0f'
down_revision = '6959338e53be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create personal files tables
    op.create_table('personal_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_size', sa.BIGINT(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=True),
        sa.Column('mime_type', sa.String(length=200), nullable=True),
        sa.Column('file_hash', sa.String(length=128), nullable=True),
        sa.Column('minio_bucket', sa.String(length=255), nullable=False),
        sa.Column('minio_object_key', sa.String(length=1000), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('upload_status', sa.String(length=20), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'file_path', name='unique_user_file_path')
    )
    op.create_index(op.f('ix_personal_files_created_at'), 'personal_files', ['created_at'], unique=False)
    op.create_index(op.f('ix_personal_files_file_hash'), 'personal_files', ['file_hash'], unique=False)
    op.create_index(op.f('ix_personal_files_filename'), 'personal_files', ['filename'], unique=False)
    op.create_index(op.f('ix_personal_files_id'), 'personal_files', ['id'], unique=False)
    op.create_index(op.f('ix_personal_files_is_deleted'), 'personal_files', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_personal_files_minio_object_key'), 'personal_files', ['minio_object_key'], unique=False)
    op.create_index(op.f('ix_personal_files_upload_status'), 'personal_files', ['upload_status'], unique=False)
    op.create_index(op.f('ix_personal_files_user_id'), 'personal_files', ['user_id'], unique=False)

    op.create_table('personal_folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=1000), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['personal_folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'path', name='unique_user_folder_path')
    )
    op.create_index(op.f('ix_personal_folders_created_at'), 'personal_folders', ['created_at'], unique=False)
    op.create_index(op.f('ix_personal_folders_id'), 'personal_folders', ['id'], unique=False)
    op.create_index(op.f('ix_personal_folders_is_deleted'), 'personal_folders', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_personal_folders_name'), 'personal_folders', ['name'], unique=False)
    op.create_index(op.f('ix_personal_folders_path'), 'personal_folders', ['path'], unique=False)
    op.create_index(op.f('ix_personal_folders_user_id'), 'personal_folders', ['user_id'], unique=False)

    op.create_table('personal_file_downloads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('download_size', sa.BIGINT(), nullable=True),
        sa.Column('download_status', sa.String(length=20), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['personal_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personal_file_downloads_downloaded_at'), 'personal_file_downloads', ['downloaded_at'], unique=False)
    op.create_index(op.f('ix_personal_file_downloads_id'), 'personal_file_downloads', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_personal_file_downloads_id'), table_name='personal_file_downloads')
    op.drop_index(op.f('ix_personal_file_downloads_downloaded_at'), table_name='personal_file_downloads')
    op.drop_table('personal_file_downloads')
    op.drop_index(op.f('ix_personal_folders_user_id'), table_name='personal_folders')
    op.drop_index(op.f('ix_personal_folders_path'), table_name='personal_folders')
    op.drop_index(op.f('ix_personal_folders_name'), table_name='personal_folders')
    op.drop_index(op.f('ix_personal_folders_is_deleted'), table_name='personal_folders')
    op.drop_index(op.f('ix_personal_folders_id'), table_name='personal_folders')
    op.drop_index(op.f('ix_personal_folders_created_at'), table_name='personal_folders')
    op.drop_table('personal_folders')
    op.drop_index(op.f('ix_personal_files_user_id'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_upload_status'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_minio_object_key'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_is_deleted'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_id'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_filename'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_file_hash'), table_name='personal_files')
    op.drop_index(op.f('ix_personal_files_created_at'), table_name='personal_files')
    op.drop_table('personal_files')