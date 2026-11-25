#!/bin/sh
# Runs inside the API container: bring the schema up to date, then start the server.

# Stop at the first error. If the migration fails, the container exits instead
# of serving requests against a wrong schema.
set -e

alembic upgrade head

# "exec" replaces this shell with uvicorn, so uvicorn becomes the main process
# and receives Docker's stop signal directly.
# 0.0.0.0 means "listen on every network interface". Inside a container,
# 127.0.0.1 would not be reachable from outside.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
