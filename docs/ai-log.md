# AI log

Tool: Claude (Anthropic), in the Claude app.

Some of this project was written by Claude, Some by me. I ran everything on my own machine, hit the problems below, and used Claude to understand and fix them. To be able to explain the code, I have the comments in every source file and a written study guide in `docs/code-explanation.md`.

## Monday 23 November

**Used it for:** reading the Week 3 brief and building the whole first version: the FastAPI routes, services and repositories, the SQLAlchemy models, the Alembic migration, the Dockerfile and `docker-compose.yml`, the seed script, the pytest tests with fakes, the Postman collection, and first drafts of the README, decision records, mapping table and cut list.

**Kept:** the three layers (routes, services, repositories), Argon2 for password hashing, JWT tokens, running the migrations when the API container starts, a named volume for the data, and a database healthcheck so the API waits for Postgres.

**Asked for changes:** The documents as separate files. 

**Problem:** I ran `docker compose up` from my Desktop and got "no configuration file provided". The command has to be run inside the project folder, next to `docker-compose.yml`.

## Tuesday 24 November

**Used it for:**  to make a new `api.ts` so the old Next.js front end could talk to the new API. I rejected that because I wanted the web app itself in Python. It was replaced with server-rendered pages inside FastAPI (Jinja templates and my Week 2 stylesheet, in `app/web/`). The adapter and the CORS setting that went with it were removed.

**Docker problems, and how they were fixed:**
- "password authentication failed for user taskuser". The database volume from an earlier run still held the old password, because Postgres only sets the password the first time it creates the database. Fix: `docker compose down -v`, then start again.
- Warnings that a variable called `_` was not set. They meant `.env` contained `$_`, which Docker reads as a variable. It came from the PowerShell command for generating a secret. Fix: use the text the command prints, as plain text.

**Also used it for:** step-by-step instructions for running the stack and the Postman collection.


## Wednesday 25 November

**Used it for:**
- Fixing sign-in for the demo users. The `users` table was empty, so the seed had never been run against my database.
- The seed script I first wrote it skipped users that already existed and left their old password in place, which made changed passwords look ignored. I asked about it and the script was changed to read the password from `SEED_PASSWORD` and to say clearly when it skips someone.
- Updating the README and `.env.example` (a warning not to put `$` in values).
- Git: creating the repository, the branches, the commits and the pull requests. Windows showed "Deletion of directory failed" prompts when switching branches. They were caused by OneDrive and open folders, and were harmless. `git log` showed all commits and the merged pull request.

## What I changed or rejected, in short

- Rejected the Next.js adapter. Chose pages served by FastAPI instead.
- Changed the seed script so the demo password can be set.
- Changed my `.env` values after the Docker errors.
- Asked for comments on all the code and for separate documents.

## Things the AI got wrong or left unclear

- My first instructions for generating a secret did not say clearly to paste the result, not the command. That caused the `$_` warnings.
- The Docker setup was written without being run. Problems like the stale volume only showed up when I ran it.