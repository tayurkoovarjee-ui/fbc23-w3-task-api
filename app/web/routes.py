"""The web pages. Server-rendered HTML, plain CSS, no JavaScript framework.

These routes follow the same layering as the API: read the form, validate it with
the same Pydantic schemas, call a service, render a template. They never touch
the database. Every page lives under /app, so the JSON API paths are unchanged.
"""

from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.dependencies import AuthServiceDep, SettingsDep, TaskServiceDep
from app.domain import NewTask, TaskStatus
from app.errors import AppError, TaskNotFound
from app.schemas import Credentials, LoginRequest, TaskCreate, TaskUpdate
from app.web import views
from app.web.session import CurrentUser, LoginRequired, clear_session_cookie, set_session_cookie

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# include_in_schema=False keeps the HTML pages out of /docs, which is for the API.
router = APIRouter(prefix="/app", include_in_schema=False)

# Form fields arrive as text. Annotated[str, Form()] tells FastAPI to read each
# from the submitted form instead of the query string or a JSON body.
FormText = Annotated[str, Form()]


def render(request: Request, name: str, status_code: int = 200, **context):
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def redirect(url: str) -> RedirectResponse:
    # 303 See Other: after a form post, the browser follows with a GET. This is
    # the post-redirect-get pattern, so refreshing the page does not re-submit.
    return RedirectResponse(url, status_code=303)


# ---------------------------------------------------------------- sign in / up


@router.get("/login")
def login_page(request: Request):
    return render(request, "login.html", mode="login", email="", errors={}, form_error="")


@router.post("/login")
def login(request: Request, auth: AuthServiceDep, settings: SettingsDep, email: FormText = "", password: FormText = ""):
    # Validation at the edge: the same schema the API uses, before any business rule.
    try:
        body = LoginRequest.model_validate({"email": email, "password": password})
    except ValidationError as exc:
        errors = views.field_errors(exc, views.SIGN_IN_MESSAGES)
        return render(request, "login.html", 400, mode="login", email=email, errors=errors, form_error="")
    try:
        token = auth.login(body.email, body.password)
    except AppError as exc:
        # Same message for a wrong email and a wrong password (FR-2).
        return render(request, "login.html", 401, mode="login", email=email, errors={}, form_error=exc.message)
    response = redirect("/app")
    set_session_cookie(response, token, settings)
    return response


@router.get("/register")
def register_page(request: Request):
    return render(request, "login.html", mode="register", email="", errors={}, form_error="")


@router.post("/register")
def register(request: Request, auth: AuthServiceDep, settings: SettingsDep, email: FormText = "", password: FormText = ""):
    try:
        body = Credentials.model_validate({"email": email, "password": password})
    except ValidationError as exc:
        errors = views.field_errors(exc, views.SIGN_UP_MESSAGES)
        return render(request, "login.html", 400, mode="register", email=email, errors=errors, form_error="")
    try:
        auth.register(body.email, body.password)
        token = auth.login(body.email, body.password)  # sign in straight away
    except AppError as exc:
        return render(request, "login.html", exc.status_code, mode="register", email=email, errors={}, form_error=exc.message)
    response = redirect("/app")
    set_session_cookie(response, token, settings)
    return response


@router.post("/logout")
def logout():
    response = redirect("/app/login")
    clear_session_cookie(response)
    return response


# ---------------------------------------------------------------------- tasks

NEW_TASK_DEFAULTS = {"title": "", "description": "", "due_date": "", "status": TaskStatus.todo.value}


def task_page(request: Request, user, service, *, status: str = "", q: str = "", sort: str = "", notice: str = "",
              values=None, errors=None, form_error: str = "", status_code: int = 200):
    """Builds the main page. Used by the normal GET and by a failed 'add task'."""
    try:
        status_filter = TaskStatus(status) if status else None
    except ValueError:
        status_filter = None  # an unknown value in the address is simply ignored
    tasks = views.search_and_sort(service.list(user.id, status_filter), q, sort)
    return render(
        request,
        "index.html",
        status_code,
        user=user,
        tasks=tasks,
        today=date.today(),
        filters={"status": status_filter.value if status_filter else "", "q": q, "sort": sort or views.DEFAULT_SORT},
        is_filtered=bool(status_filter or q.strip()),
        notice=views.NOTICES.get(notice, ""),
        values=values or NEW_TASK_DEFAULTS,
        errors=errors or {},
        form_error=form_error,
        statuses=views.STATUS_LABELS,
        sort_options=views.SORT_OPTIONS,
    )


@router.get("")
def tasks_page(request: Request, user: CurrentUser, service: TaskServiceDep, status: str = "", q: str = "",
               sort: str = "", msg: str = ""):
    return task_page(request, user, service, status=status, q=q, sort=sort, notice=msg)


def clean_task_form(title: str, description: str, due_date: str, status: str) -> dict:
    # A browser sends empty text for a blank optional field. The API schema wants null.
    return {"title": title, "description": description.strip() or None, "due_date": due_date or None, "status": status}


@router.post("/tasks")
def create_task(request: Request, user: CurrentUser, service: TaskServiceDep, title: FormText = "",
                description: FormText = "", due_date: FormText = "", status: FormText = "todo"):
    shown = {"title": title, "description": description, "due_date": due_date, "status": status}
    try:
        body = TaskCreate.model_validate(clean_task_form(title, description, due_date, status))
    except ValidationError as exc:
        # Show the page again with the typed values and the error under each field.
        return task_page(request, user, service, values=shown, errors=views.field_errors(exc, views.TASK_MESSAGES),
                         status_code=400)
    service.create(user.id, NewTask(**body.model_dump()))
    return redirect("/app?msg=added")


@router.get("/tasks/{task_id}/edit")
def edit_page(request: Request, task_id: int, user: CurrentUser, service: TaskServiceDep):
    try:
        task = service.get(user.id, task_id)  # 404 for a missing task and for someone else's
    except TaskNotFound:
        return redirect("/app?msg=missing")
    values = {
        "title": task.title,
        "description": task.description or "",
        "due_date": task.due_date.isoformat() if task.due_date else "",
        "status": task.status.value,
    }
    return render(request, "edit.html", user=user, task=task, values=values, errors={}, form_error="",
                  statuses=views.STATUS_LABELS)


@router.post("/tasks/{task_id}/edit")
def edit_task(request: Request, task_id: int, user: CurrentUser, service: TaskServiceDep, title: FormText = "",
              description: FormText = "", due_date: FormText = "", status: FormText = "todo"):
    shown = {"title": title, "description": description, "due_date": due_date, "status": status}

    def again(errors, form_error="", code=400):
        # Re-draw the edit page with what the user typed and what went wrong.
        try:
            task = service.get(user.id, task_id)
        except TaskNotFound:
            return redirect("/app?msg=missing")
        return render(request, "edit.html", code, user=user, task=task, values=shown, errors=errors,
                      form_error=form_error, statuses=views.STATUS_LABELS)

    try:
        body = TaskUpdate.model_validate(clean_task_form(title, description, due_date, status))
    except ValidationError as exc:
        return again(views.field_errors(exc, views.TASK_MESSAGES))
    try:
        service.update(user.id, task_id, body.model_dump(exclude_unset=True))
    except TaskNotFound:
        return redirect("/app?msg=missing")
    except AppError as exc:
        # FR-8: a done task cannot go back to todo. The service's message is shown as is.
        return again({}, exc.message, exc.status_code)
    return redirect("/app?msg=saved")


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, user: CurrentUser, service: TaskServiceDep):
    try:
        service.update(user.id, task_id, {"status": TaskStatus.done})
    except TaskNotFound:
        return redirect("/app?msg=missing")
    return redirect("/app?msg=completed")


@router.post("/tasks/{task_id}/delete")
def delete_task(task_id: int, user: CurrentUser, service: TaskServiceDep):
    try:
        service.delete(user.id, task_id)
    except TaskNotFound:
        return redirect("/app?msg=missing")
    return redirect("/app?msg=deleted")


# ---------------------------------------------------------------- registration


def register_web(app: FastAPI) -> None:
    """Called from create_app(). Adds the pages, the stylesheet and the redirects."""

    @app.exception_handler(LoginRequired)
    async def send_to_login(request: Request, exc: LoginRequired):
        # Not signed in (or the session ran out): go to the sign-in page.
        response = redirect("/app/login")
        clear_session_cookie(response)
        return response

    @app.get("/", include_in_schema=False)
    def home():
        return redirect("/app")

    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    app.include_router(router)
