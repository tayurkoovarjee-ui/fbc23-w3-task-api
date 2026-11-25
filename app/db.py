from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # The engine holds the pool of database connections. One per process.
    # pool_pre_ping tests a connection before use and replaces dead ones quietly.
    # connect_timeout stops the health check from hanging when the database is down.
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    # A factory that makes sessions. expire_on_commit=False keeps objects usable
    # after commit, so repositories can read them to build the result.
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """One session per request, always closed afterwards.

    This is a dependency with yield: FastAPI runs everything up to the yield
    before the route, hands the session over, and runs the rest (closing it)
    after the response is sent, even if the route raised an error.
    """
    with get_sessionmaker()() as session:
        yield session
