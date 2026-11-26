"""
Database connection and session

Creates the SQLAlchemy engine (home base/gateway to the database)
(manages two critical components bhts - Dialect and Connection Pool
(how to speak to the database, and database connections))

Used by "Routes" (via get_db), tests (to create their own temporary database)'

SQLite ignores FKs unless PRAGMA foreign_keys=ON.
Creating the engine does not open the database. The file is created on the first real connection
So importing this module is fine.

"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def make_engine(url: str) -> Engine:
    """Create a database engine. Tests call this with their own temporary database
    An enfine is a longlived object for one DB, it knows the URL and keeps a pool of connections
    that sessions borrow.

    No connection is opened until it is first used
    """

    is_sqlite = url.startswith("sqlite")

    # FastAPI runs normal (non-async) endpoitns in a thread pool
    # so SQLite must be allowed to hand a connection between threads.
    engine = create_engine(url, connect_args={"check_same_thread": False} if is_sqlite else {})

    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _record) -> None:
            """Apply SQLite settings to a newly created connection

            Runs once per new raw connection (not each time one is borrowed from the pool).
            foreign_keys and busy_timeout belong to the connection, so they must be set every time
            """

            # Runs on every new connection. Settings are per connection
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")  # readers don't block the writer
            cursor.execute("PRAGMA foreign_keys=ON")  # SQLite ignores foreign keys by default
            cursor.execute("PRAGMA busy_timeout=5000")  # wait up to 5 seconds when locked (5000ms)
            cursor.close()

    return engine


# The real engine used by the running app
engine = make_engine(settings.database_url)

# A factory that creates sessions (a session = one unit of work with the database)
# expire_on_commit=False keeps objects usable after commits
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency where each request gets its own session, always closed afterwards
    Endpoints use it with `db: Session = Depends(get_db)``
    Tests replace it with a session on a temporary db
    """

    with SessionLocal() as session:
        yield session


# Use "db: DbSession" in a route to get a database session
# It is shorted for "db: Session = Depends(get_db)"
DbSession = Annotated[Session, Depends(get_db)]
