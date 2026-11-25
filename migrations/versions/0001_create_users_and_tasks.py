"""create users and tasks

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

# Alembic remembers the current revision in a table called alembic_version.
# down_revision is the migration that must run before this one. None = the first.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# upgrade() builds the schema. Alembic runs it with "alembic upgrade head".
def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),  # auto-numbered primary key
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="todo", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'done')", name="ck_tasks_status_valid"),
        sa.CheckConstraint("char_length(btrim(title)) > 0", name="ck_tasks_title_not_blank"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_tasks_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
    )
    # Indexes make "my tasks, soonest first" and "my tasks with status X" fast.
    op.create_index("ix_tasks_user_id_due_date", "tasks", ["user_id", "due_date"])
    op.create_index("ix_tasks_user_id_status", "tasks", ["user_id", "status"])


# downgrade() undoes upgrade() in reverse order. tasks goes first because it
# depends on users through the foreign key.
def downgrade() -> None:
    op.drop_index("ix_tasks_user_id_status", table_name="tasks")
    op.drop_index("ix_tasks_user_id_due_date", table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("users")
