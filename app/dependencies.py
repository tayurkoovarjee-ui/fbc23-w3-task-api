"""The wiring. Each function builds one thing and FastAPI passes it to whoever
asks for it with Depends(...). Tests replace these with fakes through
app.dependency_overrides.

Read it from the bottom of the chain up:
  route -> get_task_service -> get_task_repository -> get_session
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.errors import NotAuthenticated
from app.repositories.interfaces import TaskRepository, UserRepository
from app.repositories.tasks import SqlTaskRepository
from app.repositories.users import SqlUserRepository
from app.security import Argon2PasswordHasher, JwtTokenService
from app.services.auth_service import AuthService, PasswordHasher, TokenService
from app.services.task_service import TaskService

# Reads the "Authorization: Bearer <token>" header. auto_error=False means a
# missing header gives us None instead of FastAPI's own error, so we can return
# our own 401 in the same format as every other error.
bearer_scheme = HTTPBearer(auto_error=False)

# Shortcuts. Annotated[X, Depends(f)] reads as "a parameter of type X, filled in
# by calling f". Routes can then just write "session: SessionDep".
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service(settings: SettingsDep) -> TokenService:
    # "settings" is itself a dependency, so FastAPI calls get_settings() first.
    return JwtTokenService(settings.jwt_secret, settings.jwt_algorithm, settings.access_token_expire_minutes)


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlUserRepository(session)


def get_task_repository(session: SessionDep) -> TaskRepository:
    return SqlTaskRepository(session)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> AuthService:
    # The service is handed its tools instead of creating them (dependency injection).
    return AuthService(users, hasher, tokens)


def get_task_service(tasks: Annotated[TaskRepository, Depends(get_task_repository)]) -> TaskService:
    return TaskService(tasks)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> int:
    """Guards a route. If the token is missing or bad, the route never runs."""
    if credentials is None:
        raise NotAuthenticated()
    # read() raises NotAuthenticated for an invalid or expired token.
    return tokens.read(credentials.credentials)


# Used in the routers. Adding "user_id: CurrentUserId" to a route makes it
# require a valid token and gives the route the signed-in user's id.
CurrentUserId = Annotated[int, Depends(get_current_user_id)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
