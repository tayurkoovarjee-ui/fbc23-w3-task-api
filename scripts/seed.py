"""Creates two demo users and a few tasks. Safe to run twice: it skips users that exist.

    python -m scripts.seed
"""

from datetime import date, timedelta

from app.db import get_sessionmaker
from app.domain import NewTask, TaskStatus
from app.repositories.tasks import SqlTaskRepository
from app.repositories.users import SqlUserRepository
from app.security import Argon2PasswordHasher

DEMO_PASSWORD = "password123"  # demo data only


def main() -> None:
    # Dates are relative to today so the demo data always looks current.
    today = date.today()
    hasher = Argon2PasswordHasher()
    demo = {
        "alice@example.com": [
            NewTask("Write the README", "Cover the two commands", today + timedelta(days=1)),
            NewTask("Review the migrations", None, today + timedelta(days=3), TaskStatus.in_progress),
            NewTask("Set up Postman collection", None, None, TaskStatus.done),
        ],
        "bob@example.com": [
            NewTask("Plan the demo", "Walk through register to delete", today + timedelta(days=2)),
            NewTask("Practise explaining Depends", None, today, TaskStatus.in_progress),
        ],
    }
    # The seed uses the same repositories as the API, so it goes through the
    # same rules (and hashes the passwords the same way).
    with get_sessionmaker()() as session:
        users = SqlUserRepository(session)
        tasks = SqlTaskRepository(session)
        for email, items in demo.items():
            if users.get_by_email(email):  # makes running it twice harmless
                print(f"skip {email} (already exists)")
                continue
            user = users.add(email, hasher.hash(DEMO_PASSWORD))
            for item in items:
                tasks.add(user.id, item)
            print(f"seeded {email} with {len(items)} tasks")
    print(f"Demo password for both users: {DEMO_PASSWORD}")


# Runs main() only when the file is run directly (python -m scripts.seed),
# not when it is imported.
if __name__ == "__main__":
    main()
