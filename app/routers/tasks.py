from fastapi import APIRouter, Response

from app.dependencies import CurrentUserId, TaskServiceDep
from app.domain import NewTask, TaskStatus
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Every route below takes "user_id: CurrentUserId". That is what makes them
# require a token (401 without one) and tells the service whose tasks to use.


@router.post("", status_code=201, response_model=TaskOut)
def create_task(body: TaskCreate, user_id: CurrentUserId, service: TaskServiceDep, response: Response):
    # Turn the validated request into the plain NewTask the service expects.
    task = service.create(user_id, NewTask(**body.model_dump()))
    # FR-3: tell the client where the new task lives.
    response.headers["Location"] = f"/tasks/{task.id}"
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(user_id: CurrentUserId, service: TaskServiceDep, status: TaskStatus | None = None):
    # "status" is not in the path or a body class, so FastAPI reads it from the
    # query string (?status=done). Typing it as TaskStatus means ?status=banana
    # fails validation and becomes a 400.
    return service.list(user_id, status)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user_id: CurrentUserId, service: TaskServiceDep):
    # task_id comes from the path. Typed as int, so /tasks/abc is a 400.
    return service.get(user_id, task_id)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, user_id: CurrentUserId, service: TaskServiceDep):
    # exclude_unset=True keeps only the fields the client actually sent. That is
    # what makes this a partial update: fields left out are not touched.
    return service.update(user_id, task_id, body.model_dump(exclude_unset=True))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, user_id: CurrentUserId, service: TaskServiceDep):
    # Returns nothing, so the response is 204 with an empty body.
    service.delete(user_id, task_id)
