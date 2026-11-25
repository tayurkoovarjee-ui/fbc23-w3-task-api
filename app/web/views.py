"""Small helpers for the pages. This is presentation only: no business rules and no SQL."""

from pydantic import ValidationError

from app.domain import Task, TaskStatus

STATUS_LABELS = {
    TaskStatus.todo: "To do",
    TaskStatus.in_progress: "In progress",
    TaskStatus.done: "Done",
}

# (value in the dropdown, label). Same options as the Week 2 app.
SORT_OPTIONS = [
    ("createdAt:desc", "Newest first"),
    ("createdAt:asc", "Oldest first"),
    ("dueDate:asc", "Due soonest"),
    ("dueDate:desc", "Due latest"),
    ("title:asc", "Title A to Z"),
    ("status:asc", "Status"),
]
DEFAULT_SORT = "createdAt:desc"

# Fixed texts for the one-off notice after an action. The address carries a short
# code, never free text, so nobody can put their own words on the page.
NOTICES = {
    "added": "Task added.",
    "saved": "Changes saved.",
    "completed": "Task marked as done.",
    "deleted": "Task deleted.",
    "missing": "That task no longer exists.",
}

TASK_MESSAGES = {
    "title": "Title is required (1 to 100 characters)",
    "description": "Description must be 2000 characters or fewer",
    "due_date": "Enter a valid date",
    "status": "Pick one of the listed statuses",
}
SIGN_UP_MESSAGES = {
    "email": "Enter a valid email address",
    "password": "Password must be at least 8 characters",
}
SIGN_IN_MESSAGES = {
    "email": "Enter a valid email address",
    "password": "Enter your password",
}


def field_errors(exc: ValidationError, messages: dict[str, str]) -> dict[str, str]:
    """Turn Pydantic's errors into one friendly message per field."""
    errors: dict[str, str] = {}
    for e in exc.errors():
        field = str(e["loc"][0]) if e["loc"] else "form"
        errors.setdefault(field, messages.get(field, e["msg"]))
    return errors


_STATUS_ORDER = {TaskStatus.todo: 0, TaskStatus.in_progress: 1, TaskStatus.done: 2}


def search_and_sort(tasks: list[Task], search: str, sort: str) -> list[Task]:
    """The Week 2 search box and sort menu. The API only filters by status, so
    these two are applied here, on the list the service returned."""
    needle = search.strip().casefold()
    if needle:
        tasks = [t for t in tasks if needle in t.title.casefold() or needle in (t.description or "").casefold()]

    field, _, order = (sort if sort in dict(SORT_OPTIONS) else DEFAULT_SORT).partition(":")
    reverse = order == "desc"

    if field == "dueDate":
        # Tasks with no due date always go last, whichever way it is sorted.
        dated = sorted((t for t in tasks if t.due_date), key=lambda t: t.due_date, reverse=reverse)
        return dated + [t for t in tasks if not t.due_date]
    if field == "title":
        return sorted(tasks, key=lambda t: t.title.casefold(), reverse=reverse)
    if field == "status":
        return sorted(tasks, key=lambda t: _STATUS_ORDER[t.status], reverse=reverse)
    return sorted(tasks, key=lambda t: (t.created_at, t.id), reverse=reverse)
