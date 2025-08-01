"""Extend existing tables for file editing

Revision ID: 005
Revises: 004
Create Date: 2025-07-20 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend repository_files table
    op.add_column('repository_files', sa.Column('current_version', sa.Integer(), nullable=True, default=1))
    op.add_column('repository_files', sa.Column('last_edit_session_id', sa.String(length=255), nullable=True))
    op.add_column('repository_files', sa.Column('is_text_file', sa.Boolean(), nullable=True, default=False))
    op.add_column('repository_files', sa.Column('encoding', sa.String(length=20), nullable=True, default='utf-8'))
    
    # Extend repositories table
    op.add_column('repositories', sa.Column('total_commits', sa.Integer(), nullable=True, default=0))
    op.add_column('repositories', sa.Column('last_commit_message', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove repository_files extensions
    op.drop_column('repository_files', 'encoding')
    op.drop_column('repository_files', 'is_text_file')
    op.drop_column('repository_files', 'last_edit_session_id')
    op.drop_column('repository_files', 'current_version')
    
    # Remove repositories extensions
    op.drop_column('repositories', 'last_commit_message')
    op.drop_column('repositories', 'total_commits')