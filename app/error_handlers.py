"""One place that turns errors into responses.

Every error body has a "message". Validation errors also list each bad field.
Unexpected errors return a fixed safe message and the details go to the log.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import AppError

logger = logging.getLogger("app.errors")


def _field_name(loc: tuple) -> str:
    # Pydantic describes where an error happened as a path, for example
    # ("body", "title") or ("query", "status"). We drop the first part ("body")
    # and keep the field name, so the client sees "title".
    parts = [str(p) for p in loc[1:]]
    return ".".join(parts) if parts else str(loc[0])


def register_error_handlers(app: FastAPI) -> None:
    # A handler runs when that kind of exception escapes a route or dependency.
    # This is the FastAPI version of Express's error middleware.

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        # Our own business errors: 401, 404, 409. The status is stored on the class.
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message}, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # FastAPI would use 422 here. The brief says 400, so we replace it, and
        # list every bad field with its own message.
        errors = [{"field": _field_name(e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=400, content={"message": "Validation failed", "errors": errors})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Anything we did not plan for. The full traceback goes to the log, and
        # the client only gets a fixed message, so no internal detail leaks.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
