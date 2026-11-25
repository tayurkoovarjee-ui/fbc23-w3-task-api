"""What the services need from the data layer, written as Protocols.

The SQL classes and the test fakes both satisfy these shapes, so a service never
knows which one it was given.
"""

from typing import Any, Protocol

from app.domain import NewTask, Task, TaskStatus, User


# A Protocol is a list of methods an object must have. Any class with matching
# methods counts, with no inheritance needed. The "..." means "no body here".
class UserRepository(Protocol):
    def add(self, email: str, password_hash: str) -> User: ...

    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: int) -> User | None: ...


class TaskRepository(Protocol):
    def add(self, user_id: int, new: NewTask) -> Task: ...

    # Every method takes user_id. The data layer never looks at a task without
    # also checking who owns it.
    def get(self, user_id: int, task_id: int) -> Task | None: ...

    def list_for_user(self, user_id: int, status: TaskStatus | None) -> list[Task]: ...

    def update(self, user_id: int, task_id: int, changes: dict[str, Any]) -> Task | None: ...

    def delete(self, user_id: int, task_id: int) -> bool: ...
