## 1. Python project scaffold

- [x] 1.1 Add `requirements.txt` (Flask, python-dotenv)
- [x] 1.2 Create `backend/db.py` — SQLite connection, schema init from `docs/schema.sql`
- [x] 1.3 Create `backend/app.py` — Flask app factory, static/templates paths, run on `127.0.0.1:5000`
- [x] 1.4 Add `data/.gitkeep` and gitignore for `data/*.db`
- [x] 1.5 Create `templates/base.html` with HTMX + Alpine CDN and navigation

## 2. Repository layer (port from TypeScript)

- [x] 2.1 Port `repository.ts` → `backend/repository.py` (parameterized SQL)
- [x] 2.2 Port `seed.py` — Rugby-7 auto-seed when empty
- [x] 2.3 Port `match_score.py` from `match-score.ts`
- [x] 2.4 Port `csv_export.py` from `csv-export.ts`
- [x] 2.5 Implement `csv_import.py` — parse standard columns, resolve names, replace/append

## 3. Directories (HTMX pages)

- [x] 3.1 Templates + routes: sport templates list and detail (categories, actions, rename)
- [x] 3.2 Templates + routes: teams and players
- [x] 3.3 Templates + routes: squads (edit name/tournament, lineup)
- [x] 3.4 HTMX partials for inline add/delete/update

## 4. Matches

- [x] 4.1 Matches list with auto-score display
- [x] 4.2 Match create form
- [x] 4.3 Match setup — apply squad to lineup, role toggles
- [x] 4.4 Score partial template (`_score.html`)

## 5. Video tagging

- [x] 5.1 Port `static/tagging.css` from MVP
- [x] 5.2 Create `static/tagging.js` — BroadcastChannel, video File API, seek
- [x] 5.3 Control panel template — players, actions, outcome, comments (HTMX)
- [x] 5.4 Video player template (second window)
- [x] 5.5 Draft event flow: capture → HTMX updates → timeline/score partials
- [x] 5.6 Bold scoring rows in timeline partial
- [x] 5.7 CSV import on control panel (upload form, replace/append confirm, timeline/score refresh)

## 6. Administration

- [x] 6.1 Export `.db` file download route
- [x] 6.2 Import `.db` upload with validation and safety backup
- [x] 6.3 Administration page template

## 7. Startup and docs

- [x] 7.1 Update `start.bat` / `scripts/start.ps1` for Python server
- [x] 7.2 Update README and `docs/development-context.md` for new stack
- [x] 7.3 Manual parity checklist against `openspec/specs/`

## 8. Verification

- [ ] 8.1 Two-window tagging workflow end-to-end test
- [x] 8.2 Restart server — data persists from `data/sports_logger.db`
- [ ] 8.3 Import MVP-exported `.db` and verify data
