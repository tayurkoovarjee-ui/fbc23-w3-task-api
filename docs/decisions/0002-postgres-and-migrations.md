# 0002 PostgreSQL, SQLAlchemy and Alembic

**Decision.** PostgreSQL 16 in its own container. SQLAlchemy for queries. Alembic for the schema. The API container runs `alembic upgrade head` before it starts the server (`scripts/start.sh`).

**Why migrations run on start.** The brief says the schema must be built from scratch with no manual steps. Running them at startup means `docker compose up` is enough. If the migration fails, the container exits instead of serving requests against the wrong schema.

**Rules in the database, not only in Python.** The status check constraint, the not-blank title check, the unique email and the foreign key are in the migration. If someone writes to the database without going through the API, those rules still hold.

**Named volume.** `pgdata` is mounted at `/var/lib/postgresql/data`. Without it the data would disappear with the container.

**Healthcheck.** The API waits for `pg_isready` to pass (`depends_on` with `service_healthy`). Plain `depends_on` only waits for the container to start, and Postgres takes a few seconds longer than that.

**Checked.** `alembic check` reports no difference between the models and the migration. I dropped the database, ran the migration again, and got the same schema.
