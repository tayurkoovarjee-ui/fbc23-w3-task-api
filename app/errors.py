"""Errors the business rules can raise.

Services raise these. They carry the HTTP status they should become, but they
do not import FastAPI. app/error_handlers.py turns them into responses.
"""


class AppError(Exception):
    # Defaults. Each subclass below overrides what it needs.
    status_code = 500
    message = "Something went wrong"
    headers: dict[str, str] | None = None

    def __init__(self, message: str | None = None) -> None:
        # Use the message passed in, or fall back to the class's own message.
        self.message = message or self.message
        super().__init__(self.message)


class NotAuthenticated(AppError):
    status_code = 401
    message = "Authentication required"
    # The 401 standard says to tell the client which kind of login is expected.
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentials(AppError):
    # One message for both "wrong email" and "wrong password" (FR-2), so an
    # attacker cannot use the error to find out which emails are registered.
    status_code = 401
    message = "Invalid email or password"


class EmailAlreadyRegistered(AppError):
    status_code = 409  # conflict with existing data
    message = "An account with this email already exists"


class TaskNotFound(AppError):
    # Also used when the task belongs to someone else. Same answer on purpose.
    status_code = 404
    message = "Task not found"


class InvalidStatusTransition(AppError):
    # FR-8
    status_code = 409
    message = "A task that is done cannot be moved back to todo"
