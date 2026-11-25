from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain import User
from app.errors import EmailAlreadyRegistered
from app.models import UserRow


def _to_user(row: UserRow) -> User:
    # Database row in, plain User out. Nothing above this layer sees SQLAlchemy objects.
    return User(id=row.id, email=row.email, password_hash=row.password_hash, created_at=row.created_at)


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        # The session is passed in (dependency injection), not created here.
        self._session = session

    def add(self, email: str, password_hash: str) -> User:
        row = UserRow(email=email, password_hash=password_hash)
        self._session.add(row)
        try:
            self._session.commit()
        except IntegrityError:
            # Two sign-ups with the same email at the same moment: the unique
            # constraint is the final guard, so the loser lands here.
            self._session.rollback()
            raise EmailAlreadyRegistered() from None
        # Reload so the id and created_at the database filled in are present.
        self._session.refresh(row)
        return _to_user(row)

    def get_by_email(self, email: str) -> User | None:
        # SELECT * FROM users WHERE email = :email LIMIT 1. The value is sent as
        # a parameter, never pasted into the SQL, which prevents SQL injection.
        row = self._session.scalars(select(UserRow).where(UserRow.email == email)).first()
        return _to_user(row) if row else None

    def get_by_id(self, user_id: int) -> User | None:
        # Used by the web pages to show who is signed in.
        row = self._session.get(UserRow, user_id)
        return _to_user(row) if row else None
