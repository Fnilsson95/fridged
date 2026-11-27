# fridged backend

FastAPI + SQLAlchemy + SQLite. All business rules live here; the website and
the device only talk to this API.

## Requirements

- Python 3.11+ (`python3 --version`)

## First-time setup

```bash
cd backend
uv sync # creates .venv and installs the exact locked versions
source .venv/bin/activate
alembic upgrade head          # creates fridged.db with the tables
```

## Every new terminal

```bash
cd backend
source .venv/bin/activate     # the prompt should start with (.venv)
```

## Run the API

```bash
uvicorn app.main:app --reload
```

- Health check: http://localhost:8000/api/health
- Interactive docs: http://localhost:8000/docs
- Reach it from your phone on the home network: add `--host 0.0.0.0` and use the Mac's IP.
- Stop with Ctrl+C.

## Tests

```bash
pytest                  # all tests
pytest -x               # stop at the first failure
pytest -k unknown       # only tests with "unknown" in the name
```

## Lint and format

```bash
ruff check . --fix
ruff format .
```

Run both before every commit.

## Database and migrations

```bash
alembic revision --autogenerate -m "describe the change"   # then READ the new file
alembic upgrade head        # apply all migrations
alembic downgrade -1        # undo the last one
alembic current             # which migration the database is on
alembic history             # list of migrations

sqlite3 fridged.db ".schema"                          # show the tables
sqlite3 fridged.db "SELECT * FROM products;"          # look at data
```

Reset the development database (deletes all data):

```bash
rm -f fridged.db fridged.db-wal fridged.db-shm
alembic upgrade head
```

## Configuration

Environment variables (or a local `.env`, not committed):

| Variable               | Default                  |
| ---------------------- | ------------------------ |
| `FRIDGED_DATABASE_URL` | `sqlite:///./fridged.db` |
| `FRIDGED_TIMEZONE`     | `Europe/Stockholm`       |

Always start uvicorn, alembic and sqlite3 from `backend/`, since the default
database path is relative.

## Layout

Each Python file starts with a docstring describing its purpose, who uses it
and its gotchas. Hover over a name in VS Code to read it.

| Path                     | What it is                                                      |
| ------------------------ | --------------------------------------------------------------- |
| `pyproject.toml`         | Package name, dependencies, pytest and ruff settings            |
| `app/__init__.py`        | Marks `app/` as a Python package                                |
| `app/main.py`            | Creates the FastAPI app and registers the routes                |
| `app/config.py`          | Settings, read from `FRIDGED_*` environment variables or `.env` |
| `app/db.py`              | Engine, SQLite settings, and one session per request (`get_db`) |
| `app/models.py`          | The `products` and `events` tables and their rules              |
| `alembic.ini`            | Alembic config (generated, rarely edited)                       |
| `alembic/env.py`         | Connects Alembic to the models and the app's database URL       |
| `alembic/script.py.mako` | Template for new migration files (generated)                    |
| `alembic/versions/`      | Migrations, one file per schema change                          |
| `tests/conftest.py`      | Fixtures: temporary database, session, test client              |
| `tests/test_health.py`   | Health endpoint test                                            |
| `tests/test_models.py`   | Tests for the database rules                                    |

## Troubleshooting

| Symptom                                 | Fix                                                           |
| --------------------------------------- | ------------------------------------------------------------- |
| `command not found: alembic` / `pytest` | Activate the venv                                             |
| `No module named 'app'`                 | Run from `backend/`; reinstall with `pip install -e ".[dev]"` |
| `no such table`                         | Run `alembic upgrade head` from `backend/`                    |
