"""In-memory stand-ins for the data layer and the security helpers.

They satisfy the same Protocols as the real classes, so the services cannot tell
the difference. Nothing here touches PostgreSQL.
"""

from datetime import UTC, datetime
from typing import Any

from app.domain import NewTask, Task, TaskStatus, User
from app.errors import EmailAlreadyRegistered, NotAuthenticated


class FakeUserRepository:
    def __init__(self) -> None:
        # A dictionary stands in for the users table, keyed by email.
        self.users: dict[str, User] = {}
        self._next_id = 1

    def add(self, email: str, password_hash: str) -> User:
        if email in self.users:
            # Mimics the database's unique constraint.
            raise EmailAlreadyRegistered()
        user = User(self._next_id, email, password_hash, datetime.now(UTC))
        self._next_id += 1
        self.users[email] = user
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def get_by_id(self, user_id: int) -> User | None:
        return next((u for u in self.users.values() if u.id == user_id), None)


class FakeTaskRepository:
    def __init__(self) -> None:
        # A dictionary stands in for the tasks table, keyed by id.
        self.tasks: dict[int, Task] = {}
        self._next_id = 1

    def add(self, user_id: int, new: NewTask) -> Task:
        now = datetime.now(UTC)
        task = Task(self._next_id, user_id, new.title, new.description, new.due_date, new.status, now, now)
        self.tasks[task.id] = task
        self._next_id += 1
        return task

    def get(self, user_id: int, task_id: int) -> Task | None:
        task = self.tasks.get(task_id)
        # Same ownership rule as the SQL version: someone else's task is None.
        return task if task and task.user_id == user_id else None

    def list_for_user(self, user_id: int, status: TaskStatus | None) -> list[Task]:
        mine = [t for t in self.tasks.values() if t.user_id == user_id]
        if status is not None:
            mine = [t for t in mine if t.status == status]
        # Same order as SQL: soonest due date first, no date last.
        return sorted(mine, key=lambda t: (t.due_date is None, t.due_date or t.created_at.date(), t.id))

    def update(self, user_id: int, task_id: int, changes: dict[str, Any]) -> Task | None:
        task = self.get(user_id, task_id)
        if task is None:
            return None
        # Tasks are frozen, so build a new one: old values, then the changes on top.
        updated = Task(**{**task.__dict__, **changes, "updated_at": datetime.now(UTC)})
        self.tasks[task_id] = updated
        return updated

    def delete(self, user_id: int, task_id: int) -> bool:
        if self.get(user_id, task_id) is None:
            return False
        del self.tasks[task_id]
        return True


class FakeHasher:
    """Not secure on purpose. It makes the tests fast."""

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeTokens:
    # Token is just the text "token-for-<id>". No signing, no expiry.
    def create(self, user_id: int) -> str:
        return f"token-for-{user_id}"

    def read(self, token: str) -> int:
        if not token.startswith("token-for-"):
            raise NotAuthenticated("Invalid or expired token")
        return int(token.removeprefix("token-for-"))
