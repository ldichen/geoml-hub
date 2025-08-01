from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "fc1af125e519"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create file_versions table
    op.create_table(
        "file_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("version_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "version_type",
            sa.Enum("INITIAL", "EDIT", "MERGE", "BRANCH", name="fileversiontype"),
            nullable=True,
        ),
        sa.Column("commit_message", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BIGINT(), nullable=False),
        sa.Column("minio_bucket", sa.String(length=255), nullable=False),
        sa.Column("minio_object_key", sa.String(length=1000), nullable=False),
        sa.Column("parent_version_id", sa.Integer(), nullable=True),
        sa.Column("diff_summary", sa.JSON(), nullable=True),
        sa.Column("encoding", sa.String(length=50), nullable=True),
        sa.Column("mime_type", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["file_id"], ["repository_files.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"], ["file_versions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_hash"),
    )
    op.create_index(op.f("ix_file_versions_id"), "file_versions", ["id"], unique=False)
    op.create_index(
        op.f("ix_file_versions_version_hash"),
        "file_versions",
        ["version_hash"],
        unique=False,
    )

    # Create file_edit_sessions table
    op.create_table(
        "file_edit_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_readonly", sa.Boolean(), nullable=True),
        sa.Column("current_content", sa.Text(), nullable=True),
        sa.Column("base_version_id", sa.Integer(), nullable=False),
        sa.Column("auto_save_interval", sa.Integer(), nullable=True),
        sa.Column("last_auto_save", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_position", sa.JSON(), nullable=True),
        sa.Column("selection_range", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["base_version_id"], ["file_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["repository_files.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index(
        op.f("ix_file_edit_sessions_id"), "file_edit_sessions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_file_edit_sessions_session_id"),
        "file_edit_sessions",
        ["session_id"],
        unique=False,
    )

    # Create file_edit_permissions table
    op.create_table(
        "file_edit_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=True),
        sa.Column("can_edit", sa.Boolean(), nullable=True),
        sa.Column("can_commit", sa.Boolean(), nullable=True),
        sa.Column("can_manage", sa.Boolean(), nullable=True),
        sa.Column("permission_source", sa.String(length=50), nullable=True),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["file_id"], ["repository_files.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_file_edit_permissions_id"),
        "file_edit_permissions",
        ["id"],
        unique=False,
    )

    # Create file_templates table
    op.create_table(
        "file_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_content", sa.Text(), nullable=False),
        sa.Column("file_extension", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_file_templates_id"), "file_templates", ["id"], unique=False
    )

    # Add additional indexes for performance
    op.create_index(
        "ix_file_versions_file_id_version_number",
        "file_versions",
        ["file_id", "version_number"],
        unique=True,
    )
    op.create_index(
        "ix_file_versions_author_id", "file_versions", ["author_id"], unique=False
    )
    op.create_index(
        "ix_file_versions_created_at", "file_versions", ["created_at"], unique=False
    )

    op.create_index(
        "ix_file_edit_sessions_file_id", "file_edit_sessions", ["file_id"], unique=False
    )
    op.create_index(
        "ix_file_edit_sessions_user_id", "file_edit_sessions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_file_edit_sessions_is_active",
        "file_edit_sessions",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_file_edit_sessions_last_activity",
        "file_edit_sessions",
        ["last_activity"],
        unique=False,
    )

    op.create_index(
        "ix_file_edit_permissions_file_id_user_id",
        "file_edit_permissions",
        ["file_id", "user_id"],
        unique=True,
    )

    op.create_index(
        "ix_file_templates_category", "file_templates", ["category"], unique=False
    )
    op.create_index(
        "ix_file_templates_language", "file_templates", ["language"], unique=False
    )
    op.create_index(
        "ix_file_templates_is_public", "file_templates", ["is_public"], unique=False
    )


def downgrade() -> None:
    # Remove indexes first
    op.drop_index("ix_file_templates_is_public", table_name="file_templates")
    op.drop_index("ix_file_templates_language", table_name="file_templates")
    op.drop_index("ix_file_templates_category", table_name="file_templates")
    op.drop_index(
        "ix_file_edit_permissions_file_id_user_id", table_name="file_edit_permissions"
    )
    op.drop_index(
        "ix_file_edit_sessions_last_activity", table_name="file_edit_sessions"
    )
    op.drop_index("ix_file_edit_sessions_is_active", table_name="file_edit_sessions")
    op.drop_index("ix_file_edit_sessions_user_id", table_name="file_edit_sessions")
    op.drop_index("ix_file_edit_sessions_file_id", table_name="file_edit_sessions")
    op.drop_index("ix_file_versions_created_at", table_name="file_versions")
    op.drop_index("ix_file_versions_author_id", table_name="file_versions")
    op.drop_index("ix_file_versions_file_id_version_number", table_name="file_versions")

    # Drop tables
    op.drop_index(op.f("ix_file_templates_id"), table_name="file_templates")
    op.drop_table("file_templates")

    op.drop_index(
        op.f("ix_file_edit_permissions_id"), table_name="file_edit_permissions"
    )
    op.drop_table("file_edit_permissions")

    op.drop_index(
        op.f("ix_file_edit_sessions_session_id"), table_name="file_edit_sessions"
    )
    op.drop_index(op.f("ix_file_edit_sessions_id"), table_name="file_edit_sessions")
    op.drop_table("file_edit_sessions")

    op.drop_index(op.f("ix_file_versions_version_hash"), table_name="file_versions")
    op.drop_index(op.f("ix_file_versions_id"), table_name="file_versions")
    op.drop_table("file_versions")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS fileversiontype")
