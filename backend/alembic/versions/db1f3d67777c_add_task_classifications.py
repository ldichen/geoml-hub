"""add_task_classifications

Revision ID: db1f3d67777c
Revises: 1e29512324da
Create Date: 2025-10-09 22:27:53.838696

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db1f3d67777c'
down_revision = '1e29512324da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_classifications table
    op.create_table(
        'task_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_zh', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_classifications_id'), 'task_classifications', ['id'], unique=False)
    op.create_index(op.f('ix_task_classifications_is_active'), 'task_classifications', ['is_active'], unique=False)
    op.create_index(op.f('ix_task_classifications_name'), 'task_classifications', ['name'], unique=True)
    op.create_index(op.f('ix_task_classifications_name_zh'), 'task_classifications', ['name_zh'], unique=False)
    op.create_index(op.f('ix_task_classifications_sort_order'), 'task_classifications', ['sort_order'], unique=False)

    # Create repository_task_classifications association table
    op.create_table(
        'repository_task_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('task_classification_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_classification_id'], ['task_classifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'task_classification_id', name='unique_repo_task_classification')
    )
    op.create_index(op.f('ix_repository_task_classifications_id'), 'repository_task_classifications', ['id'], unique=False)
    op.create_index(op.f('ix_repository_task_classifications_repository_id'), 'repository_task_classifications', ['repository_id'], unique=False)
    op.create_index(op.f('ix_repository_task_classifications_task_classification_id'), 'repository_task_classifications', ['task_classification_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_repository_task_classifications_task_classification_id'), table_name='repository_task_classifications')
    op.drop_index(op.f('ix_repository_task_classifications_repository_id'), table_name='repository_task_classifications')
    op.drop_index(op.f('ix_repository_task_classifications_id'), table_name='repository_task_classifications')
    op.drop_table('repository_task_classifications')

    op.drop_index(op.f('ix_task_classifications_sort_order'), table_name='task_classifications')
    op.drop_index(op.f('ix_task_classifications_name_zh'), table_name='task_classifications')
    op.drop_index(op.f('ix_task_classifications_name'), table_name='task_classifications')
    op.drop_index(op.f('ix_task_classifications_is_active'), table_name='task_classifications')
    op.drop_index(op.f('ix_task_classifications_id'), table_name='task_classifications')
    op.drop_table('task_classifications')