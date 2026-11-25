# 0001 Routes, services, repositories

**Decision.** Three layers. Routers handle HTTP. Services hold business rules. Repositories are the only place with SQL.

**Why.** The brief requires it, and it also makes the service tests possible: a service only needs something that looks like a repository, so a dictionary-backed fake can stand in for the database.

**How the layers talk.** Services depend on `Protocol` classes in `repositories/interfaces.py`, not on the SQL classes. The SQL classes and the test fakes both fit those shapes.

**Trade-off.** More files than putting queries in the route functions. For six endpoints that is a bit heavy, but it is what the brief asks for.
