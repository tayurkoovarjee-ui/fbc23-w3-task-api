"""Checks the edge of the API (validation, 401, error shape) with the fakes
swapped in through dependency_overrides. No database is used."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@localhost:5432/unused")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_password_hasher, get_task_repository, get_token_service, get_user_repository
from app.main import create_app
from tests.fakes import FakeHasher, FakeTaskRepository, FakeTokens, FakeUserRepository


@pytest.fixture
def client():
    # Build the real app, then replace each database/security dependency with a
    # fake. The routes and services run as normal, only the bottom layer changes.
    app = create_app()
    users, tasks = FakeUserRepository(), FakeTaskRepository()
    app.dependency_overrides[get_user_repository] = lambda: users
    app.dependency_overrides[get_task_repository] = lambda: tasks
    app.dependency_overrides[get_password_hasher] = lambda: FakeHasher()
    app.dependency_overrides[get_token_service] = lambda: FakeTokens()
    return TestClient(app)


# Helper: register and log in, then return the header that goes on later requests.
def auth_header(client, email="a@example.com"):
    client.post("/auth/register", json={"email": email, "password": "long-enough"})
    token = client.post("/auth/login", json={"email": email, "password": "long-enough"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_short_password_is_a_400_that_names_the_field(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "password"


def test_register_response_has_no_password(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": "long-enough"})
    assert r.status_code == 201
    assert "password" not in r.text


def test_tasks_need_a_token(client):
    assert client.get("/tasks").status_code == 401


def test_create_returns_201_and_a_location_header(client):
    r = client.post("/tasks", json={"title": "Hello"}, headers=auth_header(client))
    assert r.status_code == 201
    assert r.headers["location"] == f"/tasks/{r.json()['id']}"


def test_unknown_status_filter_is_a_400(client):
    assert client.get("/tasks?status=banana", headers=auth_header(client)).status_code == 400


def test_reopening_a_done_task_is_a_409(client):
    h = auth_header(client)
    task = client.post("/tasks", json={"title": "x", "status": "done"}, headers=h).json()
    r = client.patch(f"/tasks/{task['id']}", json={"status": "todo"}, headers=h)
    assert r.status_code == 409
