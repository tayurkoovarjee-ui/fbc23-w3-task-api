# Walkthrough: build it in stages

Deadline: Wednesday 25 Nov, 11:00. Do one stage at a time. Type the code yourself (do not paste), run the check at the end of the stage, then commit. The brief says code you cannot explain will not count, so after each stage close this file and say out loud what each file does.

Make the repository first: create an empty GitHub repo, clone it, and work in a branch for each stage (`git switch -c stage-1-skeleton`). Open a pull request into `main` when the stage works. Make at least three commits a day. Never commit `.env`.

For each stage, finish by writing 2 to 3 lines in `docs/ai-log.md`: what you used AI for, what you kept, what you changed.

---

## Stage 0: Folders and Docker check (15 min)

Check Docker Desktop is running: `docker --version` and `docker compose version`. Copy the folder layout from the README. Add `.gitignore`, `.dockerignore`, `.env.example`, `requirements.txt`.

**Concept:** `.env.example` is committed, `.env` is not. Anyone cloning copies one to the other.
**Commit:** "Add project layout, gitignore and env example"

## Stage 1: Hello FastAPI in a container (45 min)

Files: `app/config.py`, `app/main.py`, `Dockerfile`, `docker-compose.yml` (db service first).

Start with a `/health` that just returns `{"status": "ok"}`. Run `docker compose up --build` and open `localhost:8000/health` and `localhost:8000/docs`.

**Concepts to be able to explain:**
- Why dependencies are copied and installed before the app code in the Dockerfile (layer caching).
- Why the container runs as a non-root user.
- What `depends_on` with `service_healthy` does and why plain `depends_on` is not enough.
- Why settings come from environment variables.

**Check:** `/docs` loads. Stop the db container and start the API again to see what a missing database looks like.
**Commit:** "Run a minimal FastAPI app in Docker with Postgres"

## Stage 2: Tables and migrations (60 min)

Files: `app/models.py`, `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_create_users_and_tasks.py`, `scripts/start.sh`.

Write the models first, then write the migration by hand from them (the finished version is in the project). Then `alembic check` should say "No new upgrade operations detected".

**Concepts:**
- A migration is a versioned script. `upgrade` builds, `downgrade` undoes.
- Why `start.sh` runs `alembic upgrade head` before uvicorn.
- Why rules (check constraints, unique, foreign key) are in the database as well as in Python.

**Check:** `docker compose down -v`, then `docker compose up --build`. The schema rebuilds with no manual steps. Then `docker compose exec db psql -U taskuser -d taskdb -c "\dt"` shows `users`, `tasks`, `alembic_version`.
**Commit:** "Add users and tasks tables with Alembic migration"

## Stage 3: Register and sign in (75 min)

Files: `app/domain.py`, `app/errors.py`, `app/security.py`, `app/db.py`, `app/schemas.py` (Credentials, LoginRequest, UserOut, TokenOut), `app/repositories/interfaces.py`, `users.py`, `app/services/auth_service.py`, `app/dependencies.py`, `app/routers/auth.py`, `app/error_handlers.py`.

**Concepts:**
- The route calls the service, the service calls the repository. No SQL in the first two.
- Why the services take a `PasswordHasher` and `TokenService` in their constructor.
- How `Depends` builds `AuthService` per request (follow the chain in `dependencies.py` with your finger).
- Why the 400 handler replaces FastAPI's default 422.
- Why wrong email and wrong password give the same message.

**Check:** In `/docs`: register (201), register again (409), short password (400), login (200), wrong password (401).
**Commit:** one for models/security, one for the service and routes, one for error handling.

## Stage 4: Tasks (90 min)

Files: `app/repositories/tasks.py`, `app/services/task_service.py`, `app/routers/tasks.py`, the task schemas, `get_current_user_id` in `dependencies.py`.

**Concepts:**
- Every repository query filters on `user_id`. That is how one user cannot see another's tasks.
- FR-8 lives in the service, not the route and not the database.
- `model_dump(exclude_unset=True)` is what makes PATCH partial.
- Why a missing token and a bad token are both 401.
- Why another user's task is 404, not 403.

**Check:** Authorize in `/docs` with the token. Create, list, filter, get, patch, mark done then try todo (409), delete (204).
**Commit:** repository, then service, then routes.

## Stage 5: Health, logging, safe errors, seed (45 min)

Files: `app/routers/health.py` (real version), `app/repositories/health.py`, `app/middleware.py`, the catch-all handler, `scripts/seed.py`.

**Check:** Run `docker compose stop db` and call `/health`: you should get 503. Call `/tasks` with a token: you should get `{"message": "Internal server error"}` and see the traceback only in `docker compose logs api`. Then `docker compose start db`. Run the seed command from the README.
**Commit:** "Add health check, request logging and safe error handling"

## Stage 6: Tests (75 min)

Files: `tests/fakes.py`, `tests/test_auth_service.py`, `tests/test_task_service.py`, `tests/test_api_edge.py`, `pytest.ini`.

**Concepts:**
- A fake satisfies the same Protocol as the real repository, so the service cannot tell.
- `app.dependency_overrides` is how the API-level tests swap the wiring.
- Break a rule on purpose (remove the FR-8 check) and watch a test fail, then put it back.

**Check:** `pytest` passes.
**Commit:** one per test file.

## Stage 7: Postman, docs, final run (60 min)

Import `postman/task-api.postman_collection.json` and run the collection against the running container. Fill in `docs/mapping-table.md` in your own words (the one in the project is a guide, rewrite it), `docs/cut-list.md`, and the decision records. Then do the clean-machine test:

```
docker compose down -v
git clone <your repo> fresh-copy
cd fresh-copy
cp .env.example .env     (then edit the secrets)
docker compose up --build
```

Run the Postman collection once more. Tick off the hard requirements and FR-1 to FR-9 against the brief.

**Before Wednesday 09:00:** be able to explain, without this file: the request path from middleware to the database, `Depends`, the migration flow, and the mapping table.

## Stage 8 (optional, only when stages 0 to 7 are finished and you can explain them): the web app (60 to 90 min)

Files: `app/web/session.py`, `app/web/views.py`, `app/web/routes.py`, `app/web/templates/*`, `app/web/static/style.css`, `get_by_id` in the repositories, `get_user` in `AuthService`, `tests/test_web.py`.

**Concepts:**
- The pages call the same services and the same schemas as the API. Nothing about the rules is duplicated.
- Why the token is in an HttpOnly, SameSite=Lax cookie, and what that protects against.
- Post-redirect-get: why every form post answers with a 303.
- Why the notice uses a code like `?msg=added` instead of text.
- How Jinja escapes values, and the test that proves it.

**Check:** open http://localhost:8000/app, register, add, edit, complete and delete tasks. Try to move a done task back to todo. `pytest` still passes and the Postman collection still passes.
**Commit:** one for the session and views, one for the templates, one for the tests.

If you are short of time, skip this stage. It is first on the cut list.

---

## Questions a reviewer is likely to ask

1. Walk me through what happens when I `POST /tasks`.
2. What does `Depends` do, and what would break if you removed it?
3. Why is the password hash never returned?
4. What happens if the database is slow to start?
5. Where is the rule that a done task cannot go back to todo, and why there?
6. How do your tests run with no database?
7. Where does `JWT_SECRET` come from, and what if it is missing?
8. (If you built the web app) How does the web app know who is signed in, and why a cookie instead of a header?
