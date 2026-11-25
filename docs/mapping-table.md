# Mapping table: Express (Week 2) to FastAPI (Week 3)

| Concept | Week 2 (Express) | Week 3 (FastAPI) |
|---|---|---|
| Entry point | The start script launches `server.ts` | The Dockerfile runs `scripts/start.sh`, which runs `uvicorn app.main:app`. Uvicorn imports `main.py` and finds the `app` object |
| Startup sequence | Config, create app, middleware, routes, listen | `create_app()` in `main.py`: read settings, set up logging, create `FastAPI()`, add middleware, add error handlers, include routers. Uvicorn does the listening |
| Middleware | `app.use(...)`, in order | `@app.middleware("http")` in `middleware.py`. It wraps every request: code before `call_next` runs on the way in, code after runs on the way out |
| Routing | `router.post("/orders", ...)` | `@router.post("")` on an `APIRouter(prefix="/tasks")`, joined with `app.include_router(...)` |
| Request validation | Zod schema | Pydantic model as a parameter type (`body: TaskCreate`). FastAPI parses and checks the body before the function runs |
| Dependency injection | Constructor arguments, wired at startup | `Depends(...)`. A function declares what it needs in its parameters and FastAPI builds those things per request. `dependencies.py` is the wiring file, and tests replace pieces with `app.dependency_overrides` |
| Configuration | `.env` and environment variables | `pydantic-settings` reads environment variables into a typed `Settings` class and fails at startup if one is missing. Compose passes them in |
| Error handling | Error middleware with `next(err)` | Exception handlers registered with `@app.exception_handler(...)`. Raise anywhere and the handler builds the response |
| Database access | Repository layer | Repository classes in `repositories/`, using SQLAlchemy sessions. The session itself comes from a `Depends` function that opens it and closes it after the request |

## How `Depends` works, in my words

When a request arrives, FastAPI looks at the route function's parameters. For each parameter marked `Depends(f)`, it calls `f` first, and if `f` has its own `Depends` parameters it calls those first. It passes the results in. A function with `yield` (like `get_session`) runs its cleanup after the response is sent. If the same dependency is needed twice in one request, it is built once.

This is the same idea as passing things into a constructor at startup, but done per request and wired by declaring parameters instead of writing the `new` calls by hand.
