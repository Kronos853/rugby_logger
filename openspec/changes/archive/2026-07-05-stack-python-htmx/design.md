## Context

Sports Video Logger MVP is implemented as a React + Vite SPA with sql.js (SQLite WASM) persisted to IndexedDB. All product requirements are captured in `openspec/specs/`. The team wants a simpler local stack: **Python + SQLite file + HTMX**, avoiding npm build tooling and browser storage quirks.

Legacy HTML prototypes (`control_panel.html`, `video_screen.html`) and the React MVP define the target UX. `docs/schema.sql` remains the logical schema.

## Goals / Non-Goals

**Goals:**

- Run as a **local Flask app** with SQLite database as a **single file on disk**.
- Replace React pages with **Jinja2 templates + HTMX** partial updates.
- Port repository, seed, CSV export/import, and match-score logic to Python.
- Preserve two-monitor tagging (control + video) using **BroadcastChannel** in static JS.
- Fixed localhost URL so data always loads from the same DB file.
- Support **import/export** of `.db` backups on administration page.

**Non-Goals:**

- Cloud hosting, multi-user auth, or Postgres (future phase).
- Rewriting product requirements — behavior stays per existing specs unless explicitly delta'd.
- Removing React MVP code in this change (cleanup follows parity verification).
- Mobile/responsive redesign.

## Decisions

1. **Web framework: Flask**
   - *Rationale*: Simple server-rendered HTML + HTMX; minimal boilerplate for single-user local app.
   - *Alternatives rejected*: FastAPI (better for JSON-first APIs; HTMX is HTML-first), Django (heavier than needed).

2. **Database: SQLite file via stdlib `sqlite3`**
   - *Rationale*: Same schema as MVP; file is backupable/copyable; no IndexedDB/origin issues.
   - *Path*: `data/sports_logger.db` (configurable via env).
   - *Alternatives rejected*: sql.js in browser (current pain), Postgres (needs server setup).

3. **Frontend: Jinja2 + HTMX (+ Alpine.js on control panel only)**
   - *Rationale*: HTMX handles CRUD partials and timeline/score swaps; Alpine handles selected-button UI state; avoids React/Vite.
   - *CDN*: htmx.org, Alpine 3.x — no frontend build step.
   - *Alternatives rejected*: React SPA (current complexity), pure MPA + fetch (more manual DOM).

4. **Video sync: static `tagging.js` + BroadcastChannel**
   - *Rationale*: Proven in MVP; HTMX cannot drive `<video>` or cross-window media sync.
   - *Scope*: pause, time update, seek, spacebar toggle — client-only.

5. **Draft events: server-side row in `Event` table**
   - *Rationale*: Same as MVP — create event on capture with timestamp, then HTMX PATCH-style posts fill player/action/outcome.
   - *Session*: Flask session stores `selected_event_id` per match control page (single user, single tab assumed).

6. **Project layout**

   ```
   backend/
     app.py              # Flask factory / routes
     repository.py       # SQL access (from repository.ts)
     seed.py, match_score.py, csv_export.py, csv_import.py
     db.py               # connection, init schema
   templates/            # Jinja + HTMX
   static/               # app.css, tagging.css, tagging.js
   data/                 # sports_logger.db (gitignored)
   requirements.txt
   ```

7. **CSV import (match tagging)**
   - Same columns as export (`docs/development-context.md`).
   - Parse UTF-8 BOM; resolve player/team/action by name against current match + template.
   - If match already has events: user chooses **replace** or **append**; invalid rows abort entire import.
   - Control panel: file upload via HTMX multipart form; refresh timeline + score partials.

8. **Migration from React MVP**
   - Snapshot preserved in `legacy/react-mvp/` (React + Vite + sql.js).
   - Phase A: Python backend + parity pages.
   - Phase B: Import `.db` from browser MVP export via administration.
   - Phase C: Remove active `src/` React app after user sign-off (separate cleanup change).

9. **Startup**
   - `python -m backend.app` or `start.bat` → Flask on `127.0.0.1:5000`, optional browser open.
   - Replace Node `npm run dev` as primary dev entry in README.

## Risks / Trade-offs

- **[Risk] Full UI rewrite** → Mitigation: phased tasks; reuse CSS from MVP; legacy HTML as reference.
- **[Risk] HTMX latency on rapid tagging clicks** → Mitigation: acceptable for post-match; optimistic UI via Alpine where needed.
- **[Risk] Flask session lost on server restart** → Mitigation: draft event still in DB; re-select from timeline.
- **[Risk] Two codebases during migration** → Mitigation: time-box React removal; document `stack-python-htmx` as active change.
- **[Risk] Schema drift Python vs TS** → Mitigation: single `docs/schema.sql`; Python applies on init.

## Migration Plan

1. Scaffold Flask + SQLite file + schema init + Rugby-7 seed.
2. Implement directories and matches (HTMX).
3. Implement tagging control + video pages (HTMX + tagging.js).
4. Port admin export/import.
5. Manual parity test against `openspec/specs/`.
6. Update README and `start.bat` for Python.
7. (Follow-up) Archive React `src/` after acceptance.

## Open Questions

- Confirm Flask vs FastAPI before implementation (proposal assumes Flask).
- Whether Alpine.js is required on control panel or pure HTMX + CSS `.selected` is enough.
- Auto-open browser on start — default yes for Windows `start.bat`?
