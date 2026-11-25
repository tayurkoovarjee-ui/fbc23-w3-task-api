"""Request and response shapes. This is where input is checked, before any
business rule runs (validation at the edge)."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.domain import TaskStatus

# A reusable type: a string with spaces trimmed, 1 to 100 characters long (FR-3).
# Trimming first means "   " becomes "" and fails the min_length check.
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Credentials(BaseModel):
    """Body of POST /auth/register."""

    email: EmailStr  # checks it looks like a real email address
    password: str = Field(min_length=8, max_length=128)  # FR-1: at least 8 characters


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""

    # No length rule on the password here: a wrong password should be a 401,
    # not a 400 that reveals the length rule.
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    """What a user looks like in a response. There is no password field, so the
    hash cannot leak, even by accident."""

    # from_attributes lets Pydantic read the fields off a dataclass object.
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    """Body of POST /tasks."""

    title: Title
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None  # "2026-12-01" is parsed into a date
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    """Every field optional. Only the fields the client sent are changed."""

    title: Title | None = None
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None
    status: TaskStatus | None = None

    @field_validator("title", "status")
    @classmethod
    def not_null(cls, value):
        # Leaving a field out is fine. Sending title: null or status: null is
        # not, because a task must always have both. (description and due_date
        # may be sent as null to clear them.)
        if value is None:
            raise ValueError("cannot be null")
        return value


class TaskOut(BaseModel):
    """What a task looks like in a response."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    due_date: date | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
