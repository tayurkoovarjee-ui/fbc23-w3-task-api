"""Tests for the web pages. Same idea as test_api_edge.py: the real app, with the
fakes swapped in, so no database is used."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@localhost:5432/unused")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_password_hasher, get_task_repository, get_token_service, get_user_repository
from app.domain import Task, TaskStatus
from app.main import create_app
from app.web.views import search_and_sort
from tests.fakes import FakeHasher, FakeTaskRepository, FakeTokens, FakeUserRepository


def make_client(users=None, tasks=None):
    app = create_app()
    users, tasks = users or FakeUserRepository(), tasks or FakeTaskRepository()
    app.dependency_overrides[get_user_repository] = lambda: users
    app.dependency_overrides[get_task_repository] = lambda: tasks
    app.dependency_overrides[get_password_hasher] = lambda: FakeHasher()
    app.dependency_overrides[get_token_service] = lambda: FakeTokens()
    # follow_redirects=False so the tests can look at each redirect itself.
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def client():
    return make_client()


def sign_up(client, email="a@example.com", password="long-enough"):
    return client.post("/app/register", data={"email": email, "password": password})


# ---- signing in and out


def test_page_redirects_to_sign_in_when_signed_out(client):
    r = client.get("/app")
    assert r.status_code == 303
    assert r.headers["location"] == "/app/login"


def test_register_signs_you_in_with_an_http_only_cookie(client):
    r = sign_up(client)
    assert r.status_code == 303 and r.headers["location"] == "/app"
    assert "httponly" in r.headers["set-cookie"].lower()
    assert "a@example.com" in client.get("/app").text


def test_register_with_a_short_password_shows_the_error_and_nothing_is_created(client):
    r = sign_up(client, password="short")
    assert r.status_code == 400
    assert "at least 8 characters" in r.text


def test_register_twice_with_the_same_email_shows_a_message():
    shared = FakeUserRepository()  # both browsers share one users table
    sign_up(make_client(shared))
    r = sign_up(make_client(shared))
    assert r.status_code == 409 and "already exists" in r.text


def test_wrong_password_gives_one_generic_message(client):
    sign_up(client)
    client.post("/app/logout")
    r = client.post("/app/login", data={"email": "a@example.com", "password": "not-the-password"})
    assert r.status_code == 401 and "Invalid email or password" in r.text


def test_sign_out_clears_the_session(client):
    sign_up(client)
    client.post("/app/logout")
    client.cookies.clear()
    assert client.get("/app").headers["location"] == "/app/login"


def test_a_garbage_cookie_is_treated_as_signed_out(client):
    client.cookies.set("tt_session", "nonsense")
    assert client.get("/app").headers["location"] == "/app/login"


# ---- tasks


def add(client, **fields):
    data = {"title": "Write tests", "description": "", "due_date": "", "status": "todo", **fields}
    return client.post("/app/tasks", data=data)


def test_add_task_then_see_it_in_the_list(client):
    sign_up(client)
    r = add(client, title="Buy milk")
    assert r.status_code == 303 and r.headers["location"] == "/app?msg=added"
    page = client.get("/app?msg=added").text
    assert "Buy milk" in page and "Task added." in page


def test_blank_title_redraws_the_page_with_the_error_and_keeps_typed_values(client):
    sign_up(client)
    r = add(client, title="   ", description="keep me")
    assert r.status_code == 400
    assert "Title is required" in r.text and "keep me" in r.text


def test_invalid_date_is_rejected(client):
    sign_up(client)
    assert add(client, due_date="not-a-date").status_code == 400


def test_html_in_a_title_is_escaped(client):
    sign_up(client)
    add(client, title="<script>alert(1)</script>")
    page = client.get("/app").text
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page


def test_unknown_notice_code_shows_nothing(client):
    sign_up(client)
    assert "hacked" not in client.get("/app?msg=hacked").text


def test_edit_changes_the_task_and_can_clear_optional_fields(client):
    sign_up(client)
    add(client, title="Old", description="to clear", due_date="2026-12-01")
    r = client.post("/app/tasks/1/edit", data={"title": "New", "description": "", "due_date": "", "status": "in_progress"})
    assert r.headers["location"] == "/app?msg=saved"
    page = client.get("/app").text
    assert "New" in page and "to clear" not in page


def test_done_task_cannot_be_moved_back_to_todo(client):
    sign_up(client)
    add(client, title="Finish", status="done")
    r = client.post("/app/tasks/1/edit", data={"title": "Finish", "description": "", "due_date": "", "status": "todo"})
    assert r.status_code == 409 and "cannot be moved back to todo" in r.text


def test_complete_and_delete(client):
    sign_up(client)
    add(client)
    assert client.post("/app/tasks/1/complete").headers["location"] == "/app?msg=completed"
    assert "Done" in client.get("/app").text
    assert client.post("/app/tasks/1/delete").headers["location"] == "/app?msg=deleted"
    assert "No tasks yet" in client.get("/app").text


def test_cannot_see_edit_complete_or_delete_another_users_task():
    users, tasks = FakeUserRepository(), FakeTaskRepository()
    alice, bob = make_client(users, tasks), make_client(users, tasks)
    sign_up(alice, "alice@example.com")
    add(alice, title="Alice secret")
    sign_up(bob, "bob@example.com")
    assert "Alice secret" not in bob.get("/app").text
    for call in (bob.get("/app/tasks/1/edit"), bob.post("/app/tasks/1/complete"), bob.post("/app/tasks/1/delete")):
        assert call.headers["location"] == "/app?msg=missing"
    assert "Alice secret" in alice.get("/app").text  # untouched


def test_status_filter_and_search(client):
    sign_up(client)
    add(client, title="Alpha", status="todo")
    add(client, title="Beta", status="done")
    only_done = client.get("/app?status=done").text
    assert "Beta" in only_done and "Alpha" not in only_done
    found = client.get("/app?q=alp").text
    assert "Alpha" in found and "Beta" not in found
    assert "No tasks match those filters." in client.get("/app?q=zzz").text


def test_unknown_status_in_the_address_is_ignored(client):
    sign_up(client)
    add(client)
    assert client.get("/app?status=banana").status_code == 200


def test_json_api_still_works_next_to_the_pages(client):
    assert client.get("/tasks").status_code == 401
    assert client.get("/", follow_redirects=False).headers["location"] == "/app"


# ---- search_and_sort on its own


def task(id, title, due=None, status=TaskStatus.todo, description=None):
    when = datetime(2026, 11, id, tzinfo=UTC)
    return Task(id, 1, title, description, due, status, when, when)


def test_sort_due_soonest_puts_undated_tasks_last():
    tasks = [task(1, "none"), task(2, "later", date(2026, 12, 9)), task(3, "sooner", date(2026, 12, 1))]
    assert [t.title for t in search_and_sort(tasks, "", "dueDate:asc")] == ["sooner", "later", "none"]
    assert [t.title for t in search_and_sort(tasks, "", "dueDate:desc")] == ["later", "sooner", "none"]


def test_sort_by_title_ignores_case_and_search_checks_the_description():
    tasks = [task(1, "banana"), task(2, "Apple", description="red fruit")]
    assert [t.title for t in search_and_sort(tasks, "", "title:asc")] == ["Apple", "banana"]
    assert [t.title for t in search_and_sort(tasks, "RED", "createdAt:desc")] == ["Apple"]


def test_unknown_sort_falls_back_to_newest_first():
    tasks = [task(1, "old"), task(2, "new")]
    assert [t.title for t in search_and_sort(tasks, "", "whatever")] == ["new", "old"]
