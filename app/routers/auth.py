from fastapi import APIRouter

from app.dependencies import AuthServiceDep
from app.schemas import Credentials, LoginRequest, TokenOut, UserOut

# prefix: every route here starts with /auth. tags: groups them in /docs.
router = APIRouter(prefix="/auth", tags=["auth"])


# Routes stay thin: take the validated input, call the service, return the result.
# "body: Credentials" makes FastAPI parse and validate the JSON before this runs.
# response_model=UserOut filters the output, so the hash can never be sent back.
@router.post("/register", status_code=201, response_model=UserOut)
def register(body: Credentials, auth: AuthServiceDep):
    return auth.register(body.email, body.password)


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, auth: AuthServiceDep):
    return TokenOut(access_token=auth.login(body.email, body.password))
