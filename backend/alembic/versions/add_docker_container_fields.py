"""Add Docker container fields to model services

Revision ID: add_docker_container_fields
Revises: 3a612e7ae8f0
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_docker_container_fields'
down_revision = '3a612e7ae8f0'
branch_labels = None
depends_on = None


def upgrade():
    # Add new Docker container related fields to model_services table
    op.add_column('model_services', sa.Column('docker_image', sa.String(length=500), nullable=True, comment='Docker镜像名称'))
    op.add_column('model_services', sa.Column('health_status', sa.String(length=50), nullable=True, server_default='unknown', comment='健康状态: healthy, unhealthy, unknown, timeout'))
    op.add_column('model_services', sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'))
    op.add_column('model_services', sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='最后更新时间'))


def downgrade():
    # Remove Docker container related fields from model_services table
    op.drop_column('model_services', 'last_updated')
    op.drop_column('model_services', 'error_message')
    op.drop_column('model_services', 'health_status')
    op.drop_column('model_services', 'docker_image')