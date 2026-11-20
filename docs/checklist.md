# fridged: build checklist

Work top to bottom. Each step ends with a commit. A step is only done when its "done when" line is true.

Commit style: `feat:`, `fix:`, `test:`, `docs:`, `chore:`. No AI references or co-author trailers.

---

## 0. Docs

- [x] Move `data-model.md` and `pages.md` into `docs/`
- [x] Rewrite `docs/README.md` as an index of the docs
- [x] Add `.gitignore` entries: `.venv/`, `node_modules/`, `__pycache__/`, `*.db`, `*.db-wal`, `*.db-shm`, `.env`
- [x] Commit: `docs: add v1 data model and pages`

**Done when:** `git status` is clean and the docs are on GitHub.

---

## 1. Backend skeleton

- [x] Check `python3 --version` on your Mac and plan for the version the Pi will have (check it later with `python3 --version` on the Pi)
- [x] Create `backend/` with `pyproject.toml`, `app/`, `tests/`
- [x] Create the virtual env: `python3 -m venv .venv` and `source .venv/bin/activate`
- [x] Install runtime deps: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic-settings`
- [x] Install dev deps: `pytest`, `httpx` (needed by FastAPI's test client), `ruff`
- [x] `app/main.py`: FastAPI app, `GET /api/health` returning `{"status": "ok"}`
- [x] `app/config.py`: settings from env vars (database path, timezone `Europe/Stockholm`)
- [x] `app/db.py`: engine and session factory. On every connection set `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`
- [x] `app/models.py`: `Product` and `Event`, with the CHECK constraints from `data-model.md`
- [x] Give all constraints names via a `MetaData(naming_convention=...)`, so Alembic can change them later
- [x] Initialise Alembic, point `env.py` at your models' metadata, enable `render_as_batch=True` (SQLite)
- [x] Generate the first migration, **read it**, apply it: `alembic upgrade head`
- [x] `tests/conftest.py`: fixture that gives each test a fresh database and overrides the FastAPI session dependency
- [x] First test: `/api/health` returns 200
- [x] Configure ruff in `pyproject.toml`, then `ruff check .` and `ruff format .` pass

**Done when:** `uvicorn app.main:app --reload` starts, `http://localhost:8000/docs` loads, `pytest` is green, `alembic upgrade head` creates both tables.

---

## 2. Scans: `POST /api/scans`

- [x] `app/barcodes.py`: `normalize_barcode()` (digits only, UPC-A to GTIN-13, EAN-8 unchanged, check-digit warning only)
- [x] Unit tests for normalization: spaces, 12 digits, 8 digits, bad check digit, non-digits
- [x] Pydantic schemas: `ScanRequest` (`barcode`, `mode`, `client_event_id`, `occurred_at`) and `ScanResponse` (`result`, product info, stock)
- [x] `app/services/scans.py`: the scan logic, separate from the route so it is easy to test
- [x] Stock query: `in` + `stocktake` minus `out`, non-reverted only
- [x] Do the stock check and the insert in **one transaction** (so two quick OUT scans cannot both succeed on the last item)
- [x] Idempotency: a repeated `client_event_id` returns `duplicate`. Also catch the unique-constraint error for the race where two identical requests arrive together
- [x] All results implemented: `stocked`, `stocktaken`, `used`, `new_item`, `not_in_stock`, `duplicate`
- [x] Unknown barcode + OUT creates the unknown product but records **no event**
- [x] Events store the product's current price as a snapshot (NULL while unknown)
- [x] One parametrized test per row of the scan-rules table in `data-model.md`
- [x] Extra tests: stock never goes negative, reverted events are ignored, duplicate does not change stock

**Done when:** every row of the scan-rules table has a passing test, and a `curl` scan works against the running server.

---

## 3. Read and edit endpoints

- [x] `GET /api/products` with filters `status`, `search`, `in_stock`; returns `stock`, `value_ore`, scan count, first-seen
- [x] `GET /api/products/{id}`
- [x] `PATCH /api/products/{id}`
  - [x] Handling an unknown item requires name, brand, price (422 otherwise)
  - [x] One transaction: set fields, `status='known'`, backfill `unit_price_ore` on `in`/`out` events where it is NULL
  - [x] Editing a known product's price changes only future events
- [ ] `GET /api/events` with filters `type`, `product_id` and cursor pagination
- [ ] `POST /api/events/{id}/revert` (sets `reverted_at`; refuses if the revert would make stock negative, or decide the rule and document it)
- [ ] `GET /api/summary?period=week|month`: spent, used, gap, change vs previous period
- [ ] `GET /api/summary/weekly?weeks=12`
- [ ] Reporting periods computed in `Europe/Stockholm` with `zoneinfo`; test a week that crosses the DST change
- [ ] Tests with hand-calculated numbers for spent/used/gap
- [ ] Test the price backfill and that old totals do not change after a price change

**Done when:** all endpoints are visible in `/docs`, and the totals tests match numbers you calculated by hand.

---

## 4. Fake data

- [ ] `tools/fake_scan.py`: posts a week of realistic scans (generates UUIDs and timestamps)
- [ ] Includes known and unknown items, an OUT with no stock, a duplicate, an undo
- [ ] Option to wipe and reseed the dev database

**Done when:** one command gives you a database that makes every page look realistic.

---

## 5. Frontend on the real API

- [ ] Run the backend and `npm run dev`; verify the `/api` proxy works
- [ ] `npm install -D openapi-typescript --legacy-peer-deps`
- [ ] Add an npm script that generates `src/api/schema.d.ts` from `http://localhost:8000/openapi.json`
- [ ] `src/api/client.ts`: a small typed `fetch` wrapper
- [ ] `src/lib/formatMoney.ts`: öre to `12,50 kr`, plus input parser for `12,50` / `12.50`; unit tests
- [ ] Data hooks, one per need: `useSummary`, `useProducts`, `useProduct`, `useEvents`, `useUpdateProduct`, `useRevertEvent`
- [ ] Mutations invalidate the right queries (after saving an unknown item, refresh Unknown, Stock, Home)
- [ ] Home, Stock, Unknown, History, Product pages (one commit each)
- [ ] Remove the `shopping` stub and the Shop tab; rename Prices tab to Unknown
- [ ] Empty, loading and error states on every page
- [ ] Confirm dialogs before undo, tap targets at least 44 px, check it in the phone-sized browser view
- [ ] `npm run lint` and `npm run build` pass

**Done when:** with the fake data loaded, you can handle an unknown item, see totals change, and undo an event, all from the phone-sized view.

---

## 6. Raspberry Pi (when hardware arrives)

- [ ] Flash Raspberry Pi OS Lite 64-bit with the imager: hostname `fridge`, SSH key, Wi-Fi, `Europe/Stockholm`
- [ ] SSH in, update the system, check `python3 --version`
- [ ] Copy or clone the repo, create the venv, install the backend
- [ ] Run migrations on the Pi, run the backend with a systemd service
- [ ] Open the website from your phone on the home network
- [ ] Wire the parts one at a time, testing each with a tiny script: LED, buzzer, buttons, LCD (see `wiring.md`; GPIO is 3.3 V only)
- [ ] Check libgpiod version (`gpiodetect`) before writing GPIO code
- [ ] Scanner: read the USB scanner with evdev, grab the device, add udev/group permissions
- [ ] Daemon: command cards, modes with timeouts, POST to the backend, offline queue, feedback on LED/buzzer/LCD
- [ ] Daemon systemd service with restart on failure
- [ ] Print the command cards with `tools/make_cards.py`

**Done when:** scanning a real barcode in the kitchen shows up on the website, and it still works after unplugging and replugging the Pi.

---

## 7. Later (not v1)

- [ ] Expiry dates and days in fridge (`stock_items`)
- [ ] Shopping list and `min_stock`
- [ ] Price history
- [ ] Email reports (`report_runs`)
- [ ] Open Food Facts "Look up" button on the Unknown form
- [ ] Backups (copy the SQLite file with `sqlite3 .backup`, on a timer)
