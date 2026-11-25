from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every setting that changes between machines comes from an environment variable.

    pydantic-settings reads the variables, matches them to the field names below
    (DATABASE_URL -> database_url, case does not matter) and checks the types.
    If a required one is missing the app stops at startup and names it, which is
    better than failing on the first request.
    """

    # Ignore variables we do not use (Compose also passes POSTGRES_USER etc.).
    model_config = SettingsConfigDict(extra="ignore")

    # No default, so it is required.
    database_url: str
    # min_length=32 refuses a short, guessable signing secret.
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    # gt=0 means "greater than 0", so a token cannot be set to expire instantly.
    access_token_expire_minutes: int = Field(default=60, gt=0)
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    # lru_cache means the environment is read once and the same object is reused.
    # It is also a function (not a global) so tests can swap it with Depends.
    return Settings()  # type: ignore[call-arg]
