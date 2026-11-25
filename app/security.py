"""Password hashing and tokens. These are the real implementations.

The services only see the small interfaces in app/services/auth_service.py,
so tests can swap them for fast fakes.
"""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.errors import NotAuthenticated


class Argon2PasswordHasher:
    """Argon2id, the algorithm the OWASP password cheat sheet lists first."""

    def __init__(self) -> None:
        # The library's defaults are already sensible (Argon2id, random salt).
        self._hasher = PasswordHasher()

    def hash(self, password: str) -> str:
        # The result contains the salt and settings, so only this one string is stored.
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            # A wrong password raises an error in this library. We turn it into False.
            return False


class JwtTokenService:
    def __init__(self, secret: str, algorithm: str, expire_minutes: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire = timedelta(minutes=expire_minutes)

    def create(self, user_id: int) -> str:
        now = datetime.now(UTC)
        # "sub" (subject) is the standard JWT field for who the token is for.
        # "iat" is issued-at, "exp" is the expiry. After exp the token is rejected.
        payload = {"sub": str(user_id), "iat": now, "exp": now + self._expire}
        # The signature is made with the secret, so nobody can forge or edit a
        # token without it. The payload itself is readable, so no secrets in it.
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def read(self, token: str) -> int:
        """Return the user id inside a valid token, or raise NotAuthenticated."""
        try:
            payload = jwt.decode(
                token,
                self._secret,
                # Only accept the algorithm we expect. Never let the token pick.
                algorithms=[self._algorithm],
                # A token without an expiry or a subject is rejected.
                options={"require": ["exp", "sub"]},
            )
            return int(payload["sub"])
        except (jwt.PyJWTError, ValueError, KeyError):
            # Bad signature, expired, malformed, missing fields: all one answer.
            # "from None" hides the library's internal error from the logs.
            raise NotAuthenticated("Invalid or expired token") from None
