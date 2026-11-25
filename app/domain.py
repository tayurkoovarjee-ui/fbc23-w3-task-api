"""Plain data types shared by every layer.

They know nothing about the web framework or the database. That is what lets
the services be tested with fakes.
"""

import enum
from dataclasses import dataclass
from datetime import date, datetime


class TaskStatus(enum.StrEnum):
    # StrEnum: each value is also a normal string, so "done" == TaskStatus.done.
    # Pydantic uses this to reject any status that is not one of these three.
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


# frozen=True makes these read-only after creation. To "change" a task you build
# a new one, which avoids bugs where something edits an object by accident.
@dataclass(frozen=True)
class User:
    id: int
    email: str
    password_hash: str  # the Argon2 hash, never the real password
    created_at: datetime


@dataclass(frozen=True)
class Task:
    id: int
    user_id: int  # the owner. Every query filters on this.
    title: str
    description: str | None  # "| None" means the value is optional
    due_date: date | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class NewTask:
    """What is needed to create a task. No id or timestamps: the database adds them."""

    title: str
    description: str | None = None
    due_date: date | None = None
    status: TaskStatus = TaskStatus.todo  # FR-3: defaults to todo
