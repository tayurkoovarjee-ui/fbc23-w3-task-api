from typing import Any

from app.domain import NewTask, Task, TaskStatus
from app.errors import InvalidStatusTransition, TaskNotFound
from app.repositories.interfaces import TaskRepository


class TaskService:
    """The business rules for tasks. No HTTP and no SQL in here."""

    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def create(self, user_id: int, new: NewTask) -> Task:
        return self._tasks.add(user_id, new)

    def list(self, user_id: int, status: TaskStatus | None = None) -> list[Task]:
        return self._tasks.list_for_user(user_id, status)

    def get(self, user_id: int, task_id: int) -> Task:
        task = self._tasks.get(user_id, task_id)
        if task is None:
            # Same answer whether it does not exist or belongs to someone else.
            raise TaskNotFound()
        return task

    def update(self, user_id: int, task_id: int, changes: dict[str, Any]) -> Task:
        # Fetching first also does the ownership check and gives us the current status.
        current = self.get(user_id, task_id)
        # FR-8: a finished task cannot be reopened as todo. The rule is here
        # because it is a business rule, so it is the same whichever route or
        # database is used. (done -> in_progress is allowed.)
        if current.status == TaskStatus.done and changes.get("status") == TaskStatus.todo:
            raise InvalidStatusTransition()
        updated = self._tasks.update(user_id, task_id, changes)
        if updated is None:
            raise TaskNotFound()  # deleted between the two calls
        return updated

    def delete(self, user_id: int, task_id: int) -> None:
        if not self._tasks.delete(user_id, task_id):
            raise TaskNotFound()
