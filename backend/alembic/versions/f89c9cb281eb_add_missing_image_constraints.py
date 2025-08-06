"""add_missing_image_constraints

Revision ID: f89c9cb281eb
Revises: add_image_management_support
Create Date: 2025-08-04 15:49:14.005268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f89c9cb281eb'
down_revision = 'add_image_management_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing foreign key constraint for model_services.image_id
    # Note: This should have been created in add_image_management_support but was not applied properly
    try:
        op.create_foreign_key(
            'fk_model_services_image_id', 
            'model_services', 
            'images', 
            ['image_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    except Exception:
        # Constraint might already exist, ignore error
        pass
    
    # Create missing image_build_logs table if it doesn't exist
    # Check if table exists first
    from sqlalchemy import text
    from alembic import context
    
    connection = context.get_bind()
    result = connection.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'image_build_logs'"
    ))
    
    if not result.fetchone():
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


def downgrade() -> None:
    # Remove foreign key constraint
    try:
        op.drop_constraint('fk_model_services_image_id', 'model_services', type_='foreignkey')
    except Exception:
        pass
    
    # Drop image_build_logs table if it exists
    from sqlalchemy import text
    from alembic import context
    
    connection = context.get_bind()
    result = connection.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'image_build_logs'"
    ))
    
    if result.fetchone():
        op.drop_index('ix_build_logs_image_created', table_name='image_build_logs')
        op.drop_index(op.f('ix_image_build_logs_id'), table_name='image_build_logs')
        op.drop_table('image_build_logs')