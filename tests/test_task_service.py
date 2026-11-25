from datetime import date

import pytest

from app.domain import NewTask, TaskStatus
from app.errors import InvalidStatusTransition, TaskNotFound
from app.services.task_service import TaskService
from tests.fakes import FakeTaskRepository

# Two different user ids, to prove one user cannot touch the other's tasks.
ALICE, BOB = 1, 2


# A fixture builds a fresh service (with an empty fake) for every test.
@pytest.fixture
def service():
    return TaskService(FakeTaskRepository())


def test_new_task_defaults_to_todo(service):
    assert service.create(ALICE, NewTask("Write tests")).status == TaskStatus.todo


def test_list_only_returns_the_users_own_tasks(service):
    service.create(ALICE, NewTask("Alice's task"))
    service.create(BOB, NewTask("Bob's task"))
    assert [t.title for t in service.list(ALICE)] == ["Alice's task"]


def test_list_filters_by_status(service):
    service.create(ALICE, NewTask("one", status=TaskStatus.todo))
    service.create(ALICE, NewTask("two", status=TaskStatus.done))
    assert [t.title for t in service.list(ALICE, TaskStatus.done)] == ["two"]


def test_list_puts_the_soonest_due_date_first_and_undated_last(service):
    service.create(ALICE, NewTask("no date"))
    service.create(ALICE, NewTask("later", due_date=date(2026, 12, 1)))
    service.create(ALICE, NewTask("sooner", due_date=date(2026, 11, 25)))
    assert [t.title for t in service.list(ALICE)] == ["sooner", "later", "no date"]


def test_getting_someone_elses_task_is_not_found(service):
    task = service.create(BOB, NewTask("Bob's task"))
    with pytest.raises(TaskNotFound):
        service.get(ALICE, task.id)


def test_partial_update_changes_only_the_sent_fields(service):
    task = service.create(ALICE, NewTask("Old title", "keep me"))
    updated = service.update(ALICE, task.id, {"title": "New title"})
    assert (updated.title, updated.description) == ("New title", "keep me")


def test_done_task_cannot_go_back_to_todo(service):
    task = service.create(ALICE, NewTask("Finish", status=TaskStatus.done))
    with pytest.raises(InvalidStatusTransition):
        service.update(ALICE, task.id, {"status": TaskStatus.todo})


def test_done_task_can_move_to_in_progress(service):
    task = service.create(ALICE, NewTask("Finish", status=TaskStatus.done))
    assert service.update(ALICE, task.id, {"status": TaskStatus.in_progress}).status == TaskStatus.in_progress


def test_cannot_update_or_delete_someone_elses_task(service):
    task = service.create(BOB, NewTask("Bob's task"))
    with pytest.raises(TaskNotFound):
        service.update(ALICE, task.id, {"title": "hijacked"})
    with pytest.raises(TaskNotFound):
        service.delete(ALICE, task.id)


def test_delete_removes_the_task(service):
    task = service.create(ALICE, NewTask("Temporary"))
    service.delete(ALICE, task.id)
    with pytest.raises(TaskNotFound):
        service.get(ALICE, task.id)
