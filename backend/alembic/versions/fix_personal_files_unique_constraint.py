"""fix_personal_files_unique_constraint

Revision ID: fix_unique_constraint
Revises: fd5028fa4e0f
Create Date: 2025-07-22 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_unique_constraint'
down_revision = 'fd5028fa4e0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('unique_user_file_path', 'personal_files', type_='unique')
    
    # Create the new constraint with filename included
    op.create_unique_constraint('unique_user_file_path_name', 'personal_files', ['user_id', 'file_path', 'filename'])


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('unique_user_file_path_name', 'personal_files', type_='unique')
    
    # Restore the old constraint
    op.create_unique_constraint('unique_user_file_path', 'personal_files', ['user_id', 'file_path'])