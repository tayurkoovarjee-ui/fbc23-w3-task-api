# 0004 Errors and validation

**Validation at the edge.** Pydantic schemas check the body and query before the route function runs. FastAPI returns 422 by default, but the brief says 400, so `error_handlers.py` replaces that handler and lists each bad field.

**Business errors.** Services raise small exception classes from `errors.py`. They carry a status code but do not import FastAPI. One handler turns them into JSON.

**Unexpected errors.** A catch-all handler logs the full traceback and returns `{"message": "Internal server error"}`. I checked this by stopping Postgres mid-run: the client got the safe message and the traceback only appeared in the log.

**Request logging.** One middleware logs method, path, status and duration. It logs in a `finally` block so crashed requests appear as 500.
