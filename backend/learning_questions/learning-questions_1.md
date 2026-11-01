# fridged backend: learning questions

How to use this file:

1. Write or type the file yourself first (don't just paste it).
2. Answer the questions for that file **in your own words**, without looking at the code or docs. Short answers are fine.
3. Then check with the docs or the code, correct yourself, and ask about anything that's still unclear.
4. Write the header comment for the file (see the last section), and tick the file off in the tracker.

Question types: **What** (what does it do), **Why** (why is it done this way), **What if** (predict what happens, then try it).

Come back to the older sections now and then and answer a few again without looking. That's what makes it stick.

---

## Progress tracker

| File / topic | Written by me | Questions answered | Header comment | Broke it on purpose |
|---|---|---|---|---|
| `pyproject.toml` | [ ] | [ ] | [ ] | [ ] |
| `app/main.py` | [ ] | [ ] | [ ] | [ ] |
| `app/config.py` | [ ] | [ ] | [ ] | [ ] |
| `app/db.py` | [ ] | [ ] | [ ] | [ ] |
| `app/models.py` | [ ] | [ ] | [ ] | [ ] |
| Alembic (`env.py`, migration) | [ ] | [ ] | [ ] | [ ] |
| `tests/conftest.py` | [ ] | [ ] | [ ] | [ ] |
| `tests/test_*.py` | [ ] | [ ] | [ ] | [ ] |
| Tools (venv, ruff, git) | [ ] | [ ] | n/a | [ ] |
| Big picture | n/a | [ ] | n/a | n/a |

---

## 1. `pyproject.toml`

1. **What:** What is this file for, and which tools read it? (Name at least three.)

   **Answer:**

2. **What:** What is the difference between `dependencies` and `[project.optional-dependencies]`? How do you install each?

   **Answer:**

3. **What:** In `pip install -e ".[dev]"`, what does each part mean: `-e`, `.`, `[dev]`?

   **Answer:**

4. **Why:** Why does editable mode (`-e`) matter for `from app.db import get_db` working in tests and Alembic?

   **Answer:**

5. **Why:** `httpx` is listed under dev, but you never import it yourself. Why is it needed?

   **Answer:**

6. **What if:** What would break if you removed `[tool.setuptools.packages.find]`?

   **Answer:**

7. **What:** What does `sqlalchemy>=2.0` mean, compared with just `sqlalchemy`? Why pin a minimum here?

   **Answer:**

8. **Why:** Why do we declare `requires-python = ">=3.11"`, and why check the Pi's version before raising it?

   **Answer:**

9. **What:** What is the `[build-system]` section for? What is setuptools doing for you?

   **Answer:**

10. **What if:** You run `pip install -e ".[dev]"` without activating the venv. Where do the packages end up, and what symptom would you see later?

    **Answer:**

11. **What:** What is the `*.egg-info` folder, and why shouldn't it be committed?

    **Answer:**

12. **What:** What does `select = ["E", "F", "I", "UP", "B"]` control, and which tool reads it?

    **Answer:**

---

## 2. `app/main.py`

1. **What:** In `uvicorn app.main:app --reload`, what does each part mean: `app.main`, `:app`, `--reload`?

   **Answer:**

2. **What:** What does the `@app.get("/api/health")` decorator do to the function underneath it?

   **Answer:**

3. **Why:** Why are we using a plain `def` endpoint and not `async def` with SQLAlchemy and SQLite?

   **Answer:**

4. **What:** Where does the `/docs` page come from? Who generates it, and from what?

   **Answer:**

5. **Why:** Why does the return type annotation (`-> dict[str, str]`) matter in FastAPI?

   **Answer:**

6. **What if:** What error do you get if the variable is called `application` instead of `app`? (You've seen this one.) How would you diagnose it from the message?

   **Answer:**

7. **Why:** Why shouldn't `--reload` be used on the Pi in production?

   **Answer:**

8. **Why:** Why is the health route under `/api/...`? (Think about the frontend proxy and how the backend later serves the built frontend.)

   **Answer:**

---

## 3. `app/config.py`

1. **What:** What does `env_prefix="FRIDGED_"` do? Write the shell command that starts the app with a different database file.

   **Answer:**

2. **Why:** Why keep settings in one place instead of writing the database path directly in `db.py`?

   **Answer:**

3. **What:** What does `extra="ignore"` do, and what could go wrong without it?

   **Answer:**

4. **What:** When is `settings = Settings()` executed? What does that imply when you import `app.config` from several files?

   **Answer:**

5. **Why:** The default URL is `sqlite:///./fridged.db`. Why is a relative path a gotcha? What symptom would you see if you start Alembic from a different folder than uvicorn?

   **Answer:**

6. **Why:** Everything is stored in UTC. So why does `Settings` have a `timezone` field?

   **Answer:**

7. **What if:** What happens if you set `FRIDGED_DATABASE_URL` in your shell and also have a different value in `.env`? Which wins?

   **Answer:**

---

## 4. `app/db.py`

1. **What:** What is the difference between an *engine* and a *session*?

   **Answer:**

2. **Why:** Why `check_same_thread=False` for SQLite with FastAPI?

   **Answer:**

3. **What:** Explain each PRAGMA in your own words: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`.

   **Answer:**

4. **Why:** Why are the PRAGMAs set in a `connect` event listener, and not once at startup?

   **Answer:**

5. **What if:** Remove `PRAGMA foreign_keys=ON`. Which of your tests fails, and why? Predict first, then try it.

   **Answer:**

6. **What:** What does `get_db` do, line by line? What does `yield` do here, and why `with`?

   **Answer:**

7. **Why:** Why is `make_engine` a function instead of just creating one engine at module level?

   **Answer:**

8. **What:** What does `expire_on_commit=False` change? What would you see without it after `db.commit()`?

   **Answer:**

9. **What:** What does `Depends(get_db)` do when an endpoint uses it? When is the session closed?

   **Answer:**

---

## 5. `app/models.py`

1. **Why:** What is the naming convention for? What would go wrong later, with Alembic and SQLite, if constraints had no names?

   **Answer:**

2. **What:** What is the difference between `Mapped[str]` and `Mapped[str | None]` in the database?

   **Answer:**

3. **Why:** Why is money stored as integer öre and not as a decimal or float?

   **Answer:**

4. **Why:** Why is the barcode stored as text and not as an integer?

   **Answer:**

5. **Why:** Why are timestamps stored as UTC ISO strings? What does `timespec="milliseconds"` give you?

   **Answer:**

6. **What:** What is the difference between `default=` and `server_default=` on `status`? Why do we have both?

   **Answer:**

7. **What:** When does `onupdate=utc_now_iso` on `updated_at` run, and when would it **not** run?

   **Answer:**

8. **Why:** Explain the `known_requires_info` constraint in plain language. Why put it in the database and not only in Python code?

   **Answer:**

9. **What:** What is `unique=True` protecting on `barcode`, and what is it protecting on `client_event_id`?

   **Answer:**

10. **Why:** Why are events never edited or deleted? What does `reverted_at` do instead?

    **Answer:**

11. **Why:** Why is there an index on `(product_id, occurred_at)` and one on `(type, occurred_at)`? Which future queries use each?

    **Answer:**

12. **Why:** Why does `Event` have no `stock` or `quantity` column? How will stock be calculated?

    **Answer:**

13. **Why:** `unit_price_ore` is stored on the event, not looked up from the product. What problem does that prevent?

    **Answer:**

14. **What:** What does `Base.metadata` contain, and which other tool reads it?

    **Answer:**

---

## 6. Alembic

1. **Why:** Why use migrations instead of `Base.metadata.create_all()` for the real database?

   **Answer:**

2. **What:** What does `--autogenerate` compare, and what does it produce?

   **Answer:**

3. **Why:** Why must you always read the generated migration before applying it?

   **Answer:**

4. **What:** What does `render_as_batch=True` do, and why does SQLite need it?

   **Answer:**

5. **What:** What do these commands do: `alembic upgrade head`, `alembic downgrade -1`, `alembic current`, `alembic history`?

   **Answer:**

6. **What:** What is the `alembic_version` table?

   **Answer:**

7. **Why:** Why does `env.py` take the database URL from `settings` instead of using the one in `alembic.ini`?

   **Answer:**

8. **What if:** You add a column to `Product` but forget to create a migration. What happens when you run the app against an existing `fridged.db`? What happens in the tests?

   **Answer:**

9. **Why:** The tests build tables with `create_all`, not with Alembic. What is the upside, and what risk does that leave? How could you test for it later?

   **Answer:**

10. **What if:** You edit an already-applied migration file. Why is that a bad idea, and what should you do instead?

    **Answer:**

---

## 7. `tests/conftest.py`

1. **What:** What is a fixture? What is the default lifetime (scope) of a fixture?

   **Answer:**

2. **What:** What is `tmp_path`, and why is it used for the test database?

   **Answer:**

3. **Why:** Why does each test get its own fresh database?

   **Answer:**

4. **What:** What is `app.dependency_overrides`? What does the `client` fixture replace, and with what?

   **Answer:**

5. **Why:** Why `app.dependency_overrides.clear()` after the test?

   **Answer:**

6. **What:** What does `TestClient` do, and why doesn't it need a running uvicorn server?

   **Answer:**

7. **Why:** Why does the `engine` fixture call `engine.dispose()` at the end?

   **Answer:**

8. **What:** What does `yield` do inside a fixture? What runs before it and what after?

   **Answer:**

---

## 8. `tests/test_health.py` and `tests/test_models.py`

1. **Why:** What does `test_health` prove, beyond the endpoint returning 200? (Think about everything it needs to be working.)

   **Answer:**

2. **What:** In `test_known_product_requires_name_brand_and_price`, which exact field is missing, and which constraint fires?

   **Answer:**

3. **Why:** Why is `pytest.raises(IntegrityError)` placed around `db.commit()` and not around `db.add(...)`?

   **Answer:**

4. **What:** `test_event_requires_an_existing_product` passes a `product_id` that doesn't exist. What else does this test prove about your setup?

   **Answer:**

5. **Write:** Add a fourth model test yourself: a product with `current_price_ore=-1` must be rejected. Write it before running anything, and paste it here.

   **Answer / code:**

6. **Write:** Add a test that two products with the same barcode are rejected.

   **Answer / code:**

7. **What:** Name one thing about the model rules that these three tests do **not** cover yet.

   **Answer:**

---

## 9. Tools

### Virtual environment
1. **What:** What is a venv, and why do we use one?

   **Answer:**

2. **What:** How can you tell it's active? How do you activate it in a new terminal?

   **Answer:**

3. **What:** What does the editor's "selected interpreter" have to do with the venv? What did you see when it was wrong?

   **Answer:**

### Ruff and pytest
4. **What:** What is the difference between `ruff check` and `ruff format`?

   **Answer:**

5. **What:** How do you run one single test, and how do you stop at the first failing test?

   **Answer:**

### Git
6. **Why:** Which generated files must **not** be committed (name four), and which generated files **should** be (name two)?

   **Answer:**

7. **Why:** Why two separate commits for step 1 (skeleton, then Alembic)?

   **Answer:**

---

## 10. Big picture

1. **Explain:** Describe in 5 to 6 steps what happens when the browser calls `GET /api/health`, from the browser to the response. Name the files involved.

   **Answer:**

2. **Explain:** Why do we have only `products` and `events` in v1, and no `stock` column? How is stock calculated?

   **Answer:**

3. **Explain:** Why do all business rules live in the backend, and what does the device daemon do instead?

   **Answer:**

4. **Explain:** What is the difference between an *unknown* and a *known* product, and what happens to earlier events when an unknown item is handled?

   **Answer:**

5. **Explain:** What does idempotent mean, and how does `client_event_id` make scanning idempotent?

   **Answer:**

6. **Explain:** Why is an OUT scan of a product with no stock recorded as no event?

   **Answer:**

7. **Draw:** Sketch the folder structure from memory and write one line for what each file does.

   **Answer:**

---

## 11. Break it on purpose

Do these on a throwaway branch (`git switch -c experiment`). Write your prediction first, then run, then write what happened. Undo with `git restore .` or `git switch -`.

| # | Change | Prediction | What happened | Why |
|---|---|---|---|---|
| 1 | Rename `app` to `application` in `main.py`, start uvicorn | | | |
| 2 | Remove `PRAGMA foreign_keys=ON` in `db.py`, run `pytest` | | | |
| 3 | Delete `name="known_requires_info"` from the constraint and run `alembic revision --autogenerate` | | | |
| 4 | Run `alembic upgrade head` from the repo root instead of `backend/` | | | |
| 5 | Deactivate the venv (`deactivate`), then run `pytest` | | | |
| 6 | Add a typo in a `pyproject.toml` dependency name and run the install | | | |
| 7 | Change `status` default to `"known"` and run the tests | | | |
| 8 | Remove `app.dependency_overrides.clear()` and run a test that uses the real DB after one that uses `client` | | | |
| 9 | Remove `render_as_batch=True`, then try to add a CHECK constraint to an existing table via a migration | | | |

---

## 12. Your own header comments

For each file, write 3 to 4 lines at the top in your own words. A good header answers:

1. **What** is this file for?
2. **Who** uses it? (Which files or tools depend on it?)
3. **One gotcha** to remember.

Template:

```python
# <filename>
# Purpose: ...
# Used by: ...
# Watch out: ...
```

Write yours here first, then paste it into the file after review:

**`pyproject.toml`:**

**`app/main.py`:**

**`app/config.py`:**

**`app/db.py`:**

**`app/models.py`:**

**`alembic/env.py`:**

**`tests/conftest.py`:**

---

## 13. Warm-ups for the next session (answer without looking)

1. What does `pip install -e ".[dev]"` do?
2. What are the three SQLite PRAGMAs we set, and why?
3. Why is money stored as integer öre?
4. What does `Depends(get_db)` give an endpoint?
5. Why do constraints have names?
6. What does `alembic upgrade head` do?
7. What does a fixture's `yield` do?
8. What makes an event idempotent?
