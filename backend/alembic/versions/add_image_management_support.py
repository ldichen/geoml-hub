"""add image management support

Revision ID: add_image_management_support
Revises: add_mmanager_support
Create Date: 2025-08-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = 'add_image_management_support'
down_revision = 'add_mmanager_support'
branch_labels = None
depends_on = None


def upgrade():
    # Create images table
    op.create_table('images',
        sa.Column('id', sa.Integer(), nullable=False, comment='镜像ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='镜像名称'),
        sa.Column('tag', sa.String(length=100), nullable=False, comment='镜像标签'),
        sa.Column('repository_id', sa.Integer(), nullable=False, comment='所属仓库ID'),
        sa.Column('harbor_project', sa.String(length=255), nullable=False, comment='Harbor项目名称'),
        sa.Column('harbor_repository', sa.String(length=500), nullable=False, comment='Harbor仓库路径'),
        sa.Column('harbor_digest', sa.String(length=255), nullable=True, comment='镜像摘要'),
        sa.Column('harbor_size', sa.Integer(), nullable=True, comment='镜像大小(字节)'),
        sa.Column('description', sa.Text(), nullable=True, comment='镜像描述'),
        sa.Column('dockerfile_content', sa.Text(), nullable=True, comment='Dockerfile内容'),
        sa.Column('build_context', JSON(), nullable=True, comment='构建上下文信息'),
        sa.Column('status', sa.String(length=50), nullable=True, comment='镜像状态: uploading, ready, failed, deleted'),
        sa.Column('upload_progress', sa.Integer(), nullable=True, comment='上传进度(0-100)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('is_public', sa.Boolean(), nullable=True, comment='是否公开'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='创建用户ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='镜像管理表'
    )
    
    # Create indexes for images table
    op.create_index('ix_images_repository_status', 'images', ['repository_id', 'status'])
    op.create_index('ix_images_harbor_path', 'images', ['harbor_project', 'harbor_repository'])
    op.create_index('ix_images_created_by', 'images', ['created_by'])
    op.create_index(op.f('ix_images_id'), 'images', ['id'])
    
    # Create image_build_logs table
    op.create_table('image_build_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='日志ID'),
        sa.Column('image_id', sa.Integer(), nullable=False, comment='镜像ID'),
        sa.Column('stage', sa.String(length=100), nullable=True, comment='构建阶段'),
        sa.Column('message', sa.Text(), nullable=True, comment='日志消息'),
        sa.Column('level', sa.String(length=20), nullable=True, comment='日志级别: debug, info, warning, error'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='镜像构建日志表'
    )
    
    # Create indexes for image_build_logs table
    op.create_index('ix_build_logs_image_created', 'image_build_logs', ['image_id', 'created_at'])
    op.create_index(op.f('ix_image_build_logs_id'), 'image_build_logs', ['id'])
    
    # Add image_id column to model_services table
    op.add_column('model_services', sa.Column('image_id', sa.Integer(), nullable=True, comment='关联的镜像ID'))
    
    # Add foreign key constraint for image_id (after adding column with nullable=True)
    op.create_foreign_key('fk_model_services_image_id', 'model_services', 'images', ['image_id'], ['id'], ondelete='CASCADE')
    
    # Set default status for images
    op.execute("ALTER TABLE images ALTER COLUMN status SET DEFAULT 'uploading'")
    op.execute("ALTER TABLE images ALTER COLUMN upload_progress SET DEFAULT 0")
    op.execute("ALTER TABLE images ALTER COLUMN is_public SET DEFAULT false")
    op.execute("ALTER TABLE image_build_logs ALTER COLUMN level SET DEFAULT 'info'")


def downgrade():
    # Remove foreign key constraint first
    op.drop_constraint('fk_model_services_image_id', 'model_services', type_='foreignkey')
    
    # Remove image_id column from model_services
    op.drop_column('model_services', 'image_id')
    
    # Drop image_build_logs table
    op.drop_index(op.f('ix_image_build_logs_id'), table_name='image_build_logs')
    op.drop_index('ix_build_logs_image_created', table_name='image_build_logs')
    op.drop_table('image_build_logs')
    
    # Drop images table
    op.drop_index(op.f('ix_images_id'), table_name='images')
    op.drop_index('ix_images_created_by', table_name='images')
    op.drop_index('ix_images_harbor_path', table_name='images')
    op.drop_index('ix_images_repository_status', table_name='images')
    op.drop_table('images')