"""add mManager support tables

Revision ID: mmanager_001
Revises: add_docker_container_fields
Create Date: 2024-12-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'mmanager_001'
down_revision = 'add_docker_container_fields'
branch_labels = None
depends_on = None

def upgrade():
    """升级数据库结构以支持mManager"""
    
    # 创建mManager控制器表
    op.create_table(
        'mmanager_controllers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('controller_id', sa.String(255), nullable=False),
        sa.Column('controller_url', sa.String(500), nullable=False),
        sa.Column('server_type', sa.String(50), nullable=False),
        sa.Column('server_location', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), server_default='unknown', nullable=True),
        sa.Column('last_check_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('health_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_checks', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_failures', sa.Integer(), server_default='0', nullable=True),
        sa.Column('current_containers', sa.Integer(), server_default='0', nullable=True),
        sa.Column('max_containers', sa.Integer(), server_default='100', nullable=True),
        sa.Column('cpu_cores', sa.Integer(), nullable=True),
        sa.Column('memory_total_gb', sa.Float(), nullable=True),
        sa.Column('memory_available_gb', sa.Float(), nullable=True),
        sa.Column('disk_total_gb', sa.Float(), nullable=True),
        sa.Column('disk_available_gb', sa.Float(), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('load_percentage', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('priority', sa.Integer(), server_default='100', nullable=True),
        sa.Column('weight', sa.Integer(), server_default='100', nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_mmanager_controllers_id', 'mmanager_controllers', ['id'])
    op.create_index('ix_mmanager_controllers_controller_id', 'mmanager_controllers', ['controller_id'], unique=True)
    op.create_index('ix_mmanager_controllers_status', 'mmanager_controllers', ['status'])
    op.create_index('ix_mmanager_controllers_enabled', 'mmanager_controllers', ['enabled'])
    
    # 创建容器注册表
    op.create_table(
        'container_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('container_id', sa.String(255), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('controller_id', sa.String(255), nullable=False),
        sa.Column('controller_url', sa.String(500), nullable=False),
        sa.Column('controller_type', sa.String(50), server_default='mmanager', nullable=True),
        sa.Column('container_name', sa.String(255), nullable=False),
        sa.Column('image_name', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), server_default='unknown', nullable=True),
        sa.Column('server_info', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('resource_allocation', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('resource_usage', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('port_mappings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('host_port', sa.Integer(), nullable=True),
        sa.Column('container_port', sa.Integer(), server_default='7860', nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('networks', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(50), server_default='unknown', nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['model_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_container_registry_id', 'container_registry', ['id'])
    op.create_index('ix_container_registry_container_id', 'container_registry', ['container_id'], unique=True)
    op.create_index('ix_container_registry_service_id', 'container_registry', ['service_id'])
    op.create_index('ix_container_registry_controller_id', 'container_registry', ['controller_id'])
    op.create_index('ix_container_registry_status', 'container_registry', ['status'])
    
    # 创建容器操作记录表
    op.create_table(
        'container_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('container_id', sa.String(255), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('controller_id', sa.String(255), nullable=True),
        sa.Column('operation_type', sa.String(50), nullable=True),
        sa.Column('operation_status', sa.String(50), nullable=True),
        sa.Column('operation_details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('automated', sa.Boolean(), server_default='false', nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['model_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_container_operations_id', 'container_operations', ['id'])
    op.create_index('ix_container_operations_container_id', 'container_operations', ['container_id'])
    op.create_index('ix_container_operations_service_id', 'container_operations', ['service_id'])
    op.create_index('ix_container_operations_controller_id', 'container_operations', ['controller_id'])
    op.create_index('ix_container_operations_operation_type', 'container_operations', ['operation_type'])
    
    # 创建服务部署历史表
    op.create_table(
        'service_deployment_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('deployment_version', sa.String(50), nullable=False),
        sa.Column('controller_id', sa.String(255), nullable=False),
        sa.Column('container_id', sa.String(255), nullable=False),
        sa.Column('deployment_config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('terminated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.ForeignKeyConstraint(['service_id'], ['model_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_service_deployment_history_id', 'service_deployment_history', ['id'])
    op.create_index('ix_service_deployment_history_service_id', 'service_deployment_history', ['service_id'])
    op.create_index('ix_service_deployment_history_controller_id', 'service_deployment_history', ['controller_id'])

def downgrade():
    """回滚mManager支持"""
    
    # 删除索引
    op.drop_index('ix_service_deployment_history_controller_id')
    op.drop_index('ix_service_deployment_history_service_id') 
    op.drop_index('ix_service_deployment_history_id')
    
    op.drop_index('ix_container_operations_operation_type')
    op.drop_index('ix_container_operations_controller_id')
    op.drop_index('ix_container_operations_service_id')
    op.drop_index('ix_container_operations_container_id')
    op.drop_index('ix_container_operations_id')
    
    op.drop_index('ix_container_registry_status')
    op.drop_index('ix_container_registry_controller_id')
    op.drop_index('ix_container_registry_service_id')
    op.drop_index('ix_container_registry_container_id')
    op.drop_index('ix_container_registry_id')
    
    op.drop_index('ix_mmanager_controllers_enabled')
    op.drop_index('ix_mmanager_controllers_status')
    op.drop_index('ix_mmanager_controllers_controller_id')
    op.drop_index('ix_mmanager_controllers_id')
    
    # 删除表
    op.drop_table('service_deployment_history')
    op.drop_table('container_operations')
    op.drop_table('container_registry')
    op.drop_table('mmanager_controllers')