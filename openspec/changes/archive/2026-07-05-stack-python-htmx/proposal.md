## Why

The browser MVP (React + Vite + sql.js) solved core workflows but introduced operational pain: data tied to IndexedDB per browser origin/port, WASM load complexity, and a heavy frontend toolchain for a single-user local tool. Moving to a **Python backend with SQLite on disk** and **HTMX server-rendered UI** gives one persistent database file, simpler deployment, and aligns with the legacy HTML prototype UX—without losing the relational model already defined in `docs/schema.sql`.

## What Changes

- **BREAKING**: Replace React + Vite + sql.js frontend with **Flask + Jinja2 + HTMX** (Alpine.js on tagging control panel only).
- **BREAKING**: Remove in-browser IndexedDB persistence; SQLite lives as a **file on disk** (`data/sports_logger.db`).
- Add **Python backend**: repository layer ported from `src/db/repository.ts`, seed, CSV export, match score logic.
- Reimplement all user-facing pages as **server-rendered HTML** with HTMX partial swaps for CRUD and tagging timeline updates.
- Keep **two-monitor video workflow**: control + video pages, `BroadcastChannel` in small static `tagging.js` (no React).
- Preserve all **functional requirements** from archived MVP specs (templates, teams, squads, matches, tagging, CSV, score, admin backup).
- Add **CSV import** on the match tagging control panel (symmetric to existing CSV export; same column format).
- Add **database import** from `.db` file on the administration page (export already specified in MVP).
- **Backup** React MVP snapshot to `legacy/react-mvp/` before replacing active stack.

## Capabilities

### New Capabilities

- `local-server`: Python Flask application, SQLite file storage, startup script, HTMX/Jinja UI delivery, static assets.

### Modified Capabilities

- `administration`: Add import/restore of full SQLite `.db` backup (export behavior unchanged).
- `data-export`: Add CSV import for match events on the tagging control panel (validation, replace/append).
- `video-tagging`: Clarify server-side draft event handling and HTMX + JS split for two-window sync (implementation pattern, same user-visible behavior).

## Impact

- **Removed dependencies (target state)**: React, React Router, Vite, sql.js, npm build for production UI.
- **Added dependencies**: Python 3.11+, Flask, (optional) python-dotenv; HTMX and Alpine via CDN in templates.
- **Code layout**: new `backend/` (or project root Python package) + `templates/` + `static/`; existing `docs/schema.sql` and `openspec/specs/*` remain source of truth for behavior.
- **Deployment**: `python app.py` or `start.bat` launches server and opens browser at fixed URL (e.g. `http://127.0.0.1:5000`).
- **Migration**: Existing browser `.db` exports from MVP admin page can be imported into file-based SQLite.
