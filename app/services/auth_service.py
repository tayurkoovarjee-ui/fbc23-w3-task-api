from typing import Protocol

from app.domain import User
from app.errors import EmailAlreadyRegistered, InvalidCredentials, NotAuthenticated
from app.repositories.interfaces import UserRepository


# The service only knows these two small shapes, not Argon2 or JWT. The real
# classes are in app/security.py and the test fakes are in tests/fakes.py.
class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...


class TokenService(Protocol):
    def create(self, user_id: int) -> str: ...

    def read(self, token: str) -> int: ...


class AuthService:
    # Everything it needs is passed in. It creates nothing itself.
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        # Used when the email is unknown, so a wrong email and a wrong password
        # cost about the same time and give the same answer.
        self._decoy_hash = hasher.hash("decoy-password-never-used")

    def register(self, email: str, password: str) -> User:
        # Emails are stored lowercase so "A@x.com" and "a@x.com" are one account.
        email = email.strip().lower()
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegistered()  # FR-1: 409
        # Only the hash is stored (FR-1: never plain text).
        return self._users.add(email, self._hasher.hash(password))

    def login(self, email: str, password: str) -> str:
        user = self._users.get_by_email(email.strip().lower())
        if user is None:
            # Do the same amount of work as a real check before failing.
            self._hasher.verify(self._decoy_hash, password)
            raise InvalidCredentials()
        if not self._hasher.verify(user.password_hash, password):
            raise InvalidCredentials()  # same error as above (FR-2)
        return self._tokens.create(user.id)

    def get_user(self, user_id: int) -> User:
        # A token can outlive its user (account removed). Treat that as signed out.
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotAuthenticated()
        return user
