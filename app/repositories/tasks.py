from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain import NewTask, Task, TaskStatus
from app.models import TaskRow


def _to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        description=row.description,
        due_date=row.due_date,
        status=TaskStatus(row.status),  # the database stores text, the app uses the enum
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlTaskRepository:
    """Every query filters on user_id, so one user can never reach another's rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user_id: int, new: NewTask) -> Task:
        row = TaskRow(
            user_id=user_id,
            title=new.title,
            description=new.description,
            due_date=new.due_date,
            status=new.status.value,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)  # pick up the id and timestamps from the database
        return _to_task(row)

    def get(self, user_id: int, task_id: int) -> Task | None:
        row = self._find(user_id, task_id)
        return _to_task(row) if row else None

    def list_for_user(self, user_id: int, status: TaskStatus | None) -> list[Task]:
        query = select(TaskRow).where(TaskRow.user_id == user_id)
        if status is not None:
            query = query.where(TaskRow.status == status.value)
        # Soonest due date first (FR-4). Tasks with no date go last.
        # id breaks ties, so the order is the same every time.
        query = query.order_by(TaskRow.due_date.asc().nulls_last(), TaskRow.id.asc())
        return [_to_task(row) for row in self._session.scalars(query)]

    def update(self, user_id: int, task_id: int, changes: dict[str, Any]) -> Task | None:
        row = self._find(user_id, task_id)
        if row is None:
            return None
        # Only the fields in "changes" are set, which is what makes it partial.
        for field, value in changes.items():
            setattr(row, field, value.value if isinstance(value, TaskStatus) else value)
        self._session.commit()
        self._session.refresh(row)
        return _to_task(row)

    def delete(self, user_id: int, task_id: int) -> bool:
        # The user_id condition means someone else's task simply matches nothing.
        result = self._session.execute(
            delete(TaskRow).where(TaskRow.id == task_id, TaskRow.user_id == user_id)
        )
        self._session.commit()
        return result.rowcount > 0  # True if a row was deleted

    def _find(self, user_id: int, task_id: int) -> TaskRow | None:
        # Shared by get and update. Matching on BOTH id and owner is the
        # ownership check (FR-5): another user's task comes back as None.
        return self._session.scalars(
            select(TaskRow).where(TaskRow.id == task_id, TaskRow.user_id == user_id)
        ).first()
