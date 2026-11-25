# Task API

A REST API for a task tracker with user accounts, plus a small web app on top of it. It is written in Python with FastAPI, stores its data in PostgreSQL, and runs in Docker Compose.

You only need Docker installed to run it.

## Quick start

From the project folder (the one that contains `docker-compose.yml`):

```
cp .env.example .env
docker compose up --build
```

On Windows PowerShell, the first line is `copy .env.example .env`.

Before the second command, open `.env` and set two values:

- `POSTGRES_PASSWORD`: letters and numbers only. It ends up inside a database address, so avoid `@ : / # ? %`.
- `JWT_SECRET`: at least 32 characters. In PowerShell, run `[guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")` and paste what it prints. On macOS or Linux, use `openssl rand -hex 32`.

Every value in `.env` is plain text. Do not put a `$` in any of them, and paste the result of a command, not the command itself. Docker reads `$` as a variable.

The first build takes a few minutes. It is ready when the log shows `Application startup complete`. Then open:

| Address | What it is |
|---|---|
| http://localhost:8000/app | the web app |
| http://localhost:8000/docs | interactive API documentation |
| http://localhost:8000/health | health check |

The API container runs the database migrations every time it starts, so the tables are created on an empty database with no manual steps. The data lives in a named Docker volume, `pgdata`, so it survives `docker compose down` and a restart.

To stop: press `Ctrl+C`, then run `docker compose down`.

## Demo data

In a second terminal, in the same folder:

```
docker compose exec api python -m scripts.seed
```

This creates two users, `alice@example.com` and `bob@example.com`, with a few tasks each. The last line it prints is the password it used (`password123` by default).

To choose the password yourself (8 or more characters):

```
docker compose exec -e SEED_PASSWORD=MyPassword99 api python -m scripts.seed
```

The seed skips any user that already exists, and it leaves their password alone. To replace the demo users, wipe the database first with `docker compose down -v`.

## Using it

**The web app** (`/app`) is the Week 2 task tracker rebuilt as server-rendered pages. You can register, sign in, and add, edit, complete and delete tasks. You can filter by status, search by title or description, and sort. It uses the same services and the same validation as the API, and it lives in `app/web/` so the API does not depend on it.

**The API** can be tried from `/docs`. Register, sign in, copy the `access_token` from the response, click **Authorize** and paste it. After that every task endpoint works.

**Postman**: import `postman/task-api.postman_collection.json` and run the whole collection from top to bottom, with the API already running. It has 24 requests and 39 tests. Every endpoint has a success test and most have a failure test. The requests depend on each other (the token and the task id are saved by earlier ones), so run the whole collection rather than single requests.

## Tests

The service tests use in-memory fakes in place of the database, so they need no Postgres and no Docker.

```
python -m venv .venv
.venv\Scripts\activate          # macOS or Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

There are 43 tests:

| File | What it covers |
|---|---|
| `tests/test_auth_service.py` | registering, hashing, signing in, the same error for a wrong email and a wrong password |
| `tests/test_task_service.py` | creating, listing, filtering, ordering, ownership, partial update, the done to todo rule, delete |
| `tests/test_api_edge.py` | validation errors (400), missing token (401), response shape, with the fakes plugged in through `dependency_overrides` |
| `tests/test_web.py` | the web pages: sign-in, protection, forms, errors, escaping, ownership, search and sort |

## Configuration

Everything that changes between machines is an environment variable. `.env.example` is committed. `.env` is not.

| Variable | Needed | What it does |
|---|---|---|
| `POSTGRES_USER` | yes | database user (Compose creates it) |
| `POSTGRES_PASSWORD` | yes | that user's password |
| `POSTGRES_DB` | yes | database name |
| `JWT_SECRET` | yes | signs the tokens. At least 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | token lifetime. Default 60 |
| `LOG_LEVEL` | no | default `INFO` |
| `DATABASE_URL` | only without Docker | inside Compose it is built from the three `POSTGRES_` values |

If a required value is missing, the API stops at startup and names it.

## Endpoints

| Method | Path | Token | Requirement |
|---|---|---|---|
| GET | `/health` | no | FR-9 |
| POST | `/auth/register` | no | FR-1 |
| POST | `/auth/login` | no | FR-2 |
| POST | `/tasks` | yes | FR-3 |
| GET | `/tasks?status=` | yes | FR-4 |
| GET | `/tasks/{id}` | yes | FR-5 |
| PATCH | `/tasks/{id}` | yes | FR-6, FR-8 |
| DELETE | `/tasks/{id}` | yes | FR-7 |

Send the token as `Authorization: Bearer <token>`.

Status codes: 201 created, 200 ok, 204 deleted, 400 invalid input, 401 missing or bad token or wrong credentials, 404 not found (also for another user's task), 409 conflict (email already registered, or a done task moved back to todo), 503 database unreachable.

Validation errors name each bad field:

```json
{"message": "Validation failed", "errors": [{"field": "title", "message": "String should have at least 1 character"}]}
```

Every other error is `{"message": "..."}`. A server fault returns `{"message": "Internal server error"}`, and the details go to the log only.

## How a request flows

```
request -> logging middleware -> route (body is validated here) -> service -> repository -> PostgreSQL
```

- Routes read the request and call a service. They hold no rules and no SQL.
- Services hold the business rules, such as FR-8. They know nothing about HTTP or SQL.
- Repositories are the only place with SQL. Every task query filters on the owner's id.
- Dependencies are passed in with FastAPI's `Depends`. `app/dependencies.py` is the wiring.

## Project layout

```
app/
  main.py             entry point: builds the app
  config.py           settings from environment variables
  dependencies.py     the Depends() wiring
  routers/            HTTP routes: auth, tasks, health
  services/           business rules
  repositories/       all SQL, plus the Protocols the services depend on
  schemas.py          request and response validation
  models.py           table definitions
  security.py         password hashing (Argon2id) and tokens (JWT)
  errors.py           business errors
  error_handlers.py   turns errors into responses
  middleware.py       request logging
  web/                the web app: routes, templates, stylesheet
migrations/           Alembic migrations
scripts/              seed.py, start.sh
tests/                pytest, with fakes
postman/              the Postman collection
docs/                 decisions, mapping table, cut list, AI log, walkthrough
Dockerfile
docker-compose.yml
```

## Database and migrations

The schema comes from Alembic migrations in `migrations/versions/`. `scripts/start.sh` runs `alembic upgrade head` before it starts the server, and if a migration fails the container exits instead of serving requests.

The rules are also in the database, not only in Python: the status check, the not-blank title check, the unique email and the foreign key from tasks to users.

To rebuild from an empty database:

```
docker compose down -v
docker compose up --build
```

`down -v` deletes the volume, and with it all data.

## Running without Docker

Start a local PostgreSQL 16 and create a database. Put `DATABASE_URL` and `JWT_SECRET` in `.env`, then:

```
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Troubleshooting

**`no configuration file provided: not found`**
You are in the wrong folder. Run `dir` (or `ls`) and make sure you can see `docker-compose.yml`.

**`password authentication failed for user "taskuser"`**
The `pgdata` volume was created earlier with a different password. Postgres only sets the password the first time it creates the database, so it ignores a changed `POSTGRES_PASSWORD`. Run `docker compose down -v` and start again. Do this every time you change that value.

**`The "_" variable is not set` warnings**
Some value in `.env` contains `$_`, usually because a command was pasted instead of its result. Run `findstr /C:"$" .env` to find the line and replace the value with plain text.

**"Invalid email or password" for a demo user**
That message is the same whether the user does not exist or the password is wrong. Check that the user exists with `docker compose exec db psql -U taskuser -d taskdb -c "select id, email from users;"`. If the list is empty, run the seed. If the user is there, the password is whatever they were created with. See Demo data above.

**`port is already allocated`**
Something else is using port 8000. Close it, or change `"8000:8000"` in `docker-compose.yml` to `"8001:8000"` and use port 8001 in the addresses above.

**`exec ./scripts/start.sh: no such file or directory`**
Windows changed the line endings of `start.sh`. The `.gitattributes` file prevents this for git checkouts. If you copied files by hand, extract the zip again instead.

**Postman: "Could not send request"**
The API is not running. Check http://localhost:8000/health.

## More documentation

All in `docs/`:

- `walkthrough.md`: the project in build order, with what to check at each stage
- `mapping-table.md`: Week 2 (Express) compared with Week 3 (FastAPI)
- `decisions/`: why Docker, Postgres, migrations, auth, errors and the web app were done the way they were
- `cut-list.md`: what gets dropped first if time runs out
- `ai-log.md`: the AI use log