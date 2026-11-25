# Small official Python image. "slim" leaves out build tools we do not need.
FROM python:3.13-slim

# Do not write .pyc files, and print logs straight away instead of buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependencies first, so this layer is cached until requirements.txt changes.
# Editing app code later does not reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only what the running app needs. Tests and docs stay out (see .dockerignore).
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY scripts ./scripts

# Do not run as root inside the container.
RUN useradd --create-home appuser && chown -R appuser /srv
USER appuser

# Documentation only: the app listens on 8000. Compose does the real port mapping.
EXPOSE 8000

# Migrate, then serve. See scripts/start.sh.
CMD ["./scripts/start.sh"]
