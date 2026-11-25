import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger("app.requests")


def register_request_logging(app: FastAPI) -> None:
    # Middleware wraps every request. Code before call_next runs on the way in,
    # code after it runs on the way out.
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        status = 500  # assume the worst until we know better
        try:
            response = await call_next(request)  # runs the rest of the app
            status = response.status_code
            return response
        finally:
            # "finally" runs whether the request worked or crashed, so crashes
            # are logged as 500 instead of disappearing from the log.
            ms = (time.perf_counter() - start) * 1000
            logger.info("%s %s %s %.1fms", request.method, request.url.path, status, ms)
