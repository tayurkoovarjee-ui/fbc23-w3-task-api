from sqlalchemy import text
from sqlalchemy.orm import Session


def database_reachable(session: Session) -> bool:
    # It lives in the repositories folder because it runs SQL, and the rule is
    # no SQL outside the data layer.
    try:
        session.execute(text("SELECT 1"))  # the cheapest possible query
        return True
    except Exception:
        # Any failure (refused, timeout, wrong password) means "not reachable".
        return False
