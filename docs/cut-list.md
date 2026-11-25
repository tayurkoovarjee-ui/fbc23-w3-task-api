# Cut list

Written on Day 1. What I drop first if I fall behind, in order. Hard requirements (Docker, PostgreSQL, FastAPI) are never cut.

1. The web app (`app/web/`, `/app`). It is outside the specification. Delete the folder and the `register_web(app)` line in `main.py` and nothing else changes.
2. The `docs/decisions` files beyond a few lines each.
3. The API-level tests (`tests/test_api_edge.py`). The six service tests stay.
4. Postman failure cases beyond one per endpoint.
5. The decoy-hash timing detail in login.
6. The `Location` header test.

Never cut: the Dockerfile, `docker-compose.yml`, migrations, `.env.example`, the six service tests, the Postman success tests, the mapping table.
