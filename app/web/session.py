"""Sign-in for the web pages.

The API uses an Authorization header. A browser page cannot add that header to a
plain form post, so the same JWT is kept in a cookie instead. The token itself
is exactly the one the API issues and checks.
"""

from typing import Annotated

from fastapi import Cookie, Depends, Response

from app.config import Settings
from app.dependencies import AuthServiceDep, get_token_service
from app.domain import User
from app.errors import AppError
from app.services.auth_service import TokenService

COOKIE_NAME = "tt_session"


class LoginRequired(Exception):
    """Raised when a page needs a signed-in user. A handler turns it into a redirect."""


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.access_token_expire_minutes * 60,  # same lifetime as the token
        httponly=True,  # JavaScript on the page cannot read it
        samesite="lax",  # not sent on cross-site form posts (the CSRF protection)
        path="/",
        # secure=True would be right behind HTTPS. It is left off so it works on http://localhost.
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def get_current_user(
    auth: AuthServiceDep,
    tokens: Annotated[TokenService, Depends(get_token_service)],
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    """Guards a page. No cookie, a bad token or an expired one all mean: go and sign in."""
    if not token:
        raise LoginRequired()
    try:
        return auth.get_user(tokens.read(token))
    except AppError:
        raise LoginRequired() from None


CurrentUser = Annotated[User, Depends(get_current_user)]
