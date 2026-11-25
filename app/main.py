import logging

from fastapi import FastAPI

from app.config import get_settings
from app.error_handlers import register_error_handlers
from app.middleware import register_request_logging
from app.routers import auth, health, tasks
from app.web.routes import register_web


def create_app() -> FastAPI:
    # Startup sequence: config, logging, app, middleware, error handlers, routes.
    # It is a function so tests can build a fresh app each time.
    settings = get_settings()  # fails here, at startup, if a setting is missing
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    app = FastAPI(title="Task API", version="1.0.0")
    register_request_logging(app)
    register_error_handlers(app)
    # Each router brings its own routes and prefix.
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(tasks.router)
    # The web pages (under /app) are added last. They use the same services.
    register_web(app)
    return app


# Uvicorn is started with "app.main:app", meaning: in the file app/main.py, use
# the object called "app". This is the entry point. Uvicorn does the listening.
app = create_app()
