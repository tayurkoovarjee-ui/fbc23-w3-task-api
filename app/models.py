"""Database tables. Only the repositories and Alembic import this file."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Gives every constraint and index a predictable name. Without this the database
# invents names, and the migration and the models could disagree about them.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # Every table class below inherits from this, which is how SQLAlchemy (and
    # Alembic) find the full list of tables.
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UserRow(Base):
    __tablename__ = "users"

    # Mapped[int] is the Python type. mapped_column() adds the database details.
    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True: the database itself refuses two users with the same email.
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    # server_default means PostgreSQL fills this in with now(), not Python.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskRow(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        # Rules enforced by the database even if someone bypasses the API.
        CheckConstraint("status IN ('todo', 'in_progress', 'done')", name="status_valid"),
        CheckConstraint("char_length(btrim(title)) > 0", name="title_not_blank"),
        # Indexes for the two ways tasks are looked up: list by due date, filter by status.
        Index("ix_tasks_user_id_due_date", "user_id", "due_date"),
        Index("ix_tasks_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Foreign key: every task must belong to a real user. ondelete="CASCADE"
    # means deleting a user also deletes their tasks.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)  # "| None" = the column allows NULL
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), server_default="todo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # onupdate refreshes this every time the row is changed.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
