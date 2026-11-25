from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.dependencies import SessionDep
from app.repositories.health import database_reachable

router = APIRouter(tags=["health"])


# FR-9. No token needed. Docker or a monitor can call this to see if the API is up.
@router.get("/health")
def health(session: SessionDep):
    if database_reachable(session):
        return {"status": "ok", "database": "reachable"}
    # 503 Service Unavailable: the API is running but cannot do its job.
    return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unreachable"})
