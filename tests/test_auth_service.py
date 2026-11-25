import pytest

from app.errors import EmailAlreadyRegistered, InvalidCredentials
from app.services.auth_service import AuthService
from tests.fakes import FakeHasher, FakeTokens, FakeUserRepository


# Each test gets its own empty fake repository, so tests cannot affect each other.
@pytest.fixture
def users():
    return FakeUserRepository()


@pytest.fixture
def auth(users):
    return AuthService(users, FakeHasher(), FakeTokens())


def test_register_stores_a_hash_not_the_password(auth, users):
    user = auth.register("a@example.com", "secret-password")
    assert user.password_hash != "secret-password"
    assert users.users["a@example.com"].password_hash == "hashed:secret-password"


def test_register_lowercases_the_email(auth):
    assert auth.register("  Mixed@Example.COM ", "secret-password").email == "mixed@example.com"


def test_register_rejects_a_duplicate_email(auth):
    auth.register("a@example.com", "secret-password")
    with pytest.raises(EmailAlreadyRegistered):
        auth.register("A@example.com", "another-password")


def test_login_returns_a_token_for_the_right_password(auth):
    user = auth.register("a@example.com", "secret-password")
    assert auth.login("a@example.com", "secret-password") == f"token-for-{user.id}"


def test_wrong_password_and_unknown_email_give_the_same_error(auth):
    auth.register("a@example.com", "secret-password")
    with pytest.raises(InvalidCredentials) as wrong_password:
        auth.login("a@example.com", "not-the-password")
    with pytest.raises(InvalidCredentials) as unknown_email:
        auth.login("nobody@example.com", "secret-password")
    assert str(wrong_password.value) == str(unknown_email.value)
