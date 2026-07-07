## Context

`Match.Tournament` and `Squad.Tournament` are currently `TEXT NULL` columns — free-text, no validation, no FK. The app has one active tournament in the database. `Tournament` is used in CSV export filename generation and displayed in the match list and squad list. The stack is Flask + Jinja + HTMX; all SQL lives in `repository.py`.

## Goals / Non-Goals

**Goals:**
- Replace string tournament fields with a proper `Tournament` reference table (global, not sport-scoped)
- Inline creation: user can type a new tournament name and it gets created automatically on save
- Safe data migration that handles the existing single tournament without data loss
- Enable tournament as a filter dimension on the reports page

**Non-Goals:**
- Tournament scoped to sport template (deliberately excluded — adds complexity without enough benefit at this stage)
- Tournament detail page or tournament-level match list (can be added later)
- Tournament deletion or merge (out of scope for this change)
- Attaching additional metadata to tournaments (dates, location, notes) — keep it minimal

## Decisions

### Decision 1: Tournament is a global reference table (no SportTemplateId)

A tournament is independent of sport type. This keeps the Squad form simple (Squad has no SportTemplate link), avoids cross-table lookups, and is sufficient for filtering reports by tournament name.

**Alternative considered**: Scope Tournament to SportTemplate (one tournament per sport). Rejected — adds friction: Squad would need a hidden SportTemplateId field; dropdown logic becomes conditional; naming collisions across sports are not a real problem for a single-user local app.

### Decision 2: Inline creation via `get_or_create_tournament`

When a match or squad is saved, the route passes the tournament name string to `get_or_create_tournament(conn, name)` in `repository.py`. If a matching record exists, its ID is returned; otherwise a new row is inserted. Empty name returns `None` (no association).

UNIQUE constraint on `Tournament.Name` prevents duplicates.

### Decision 3: UI — datalist for autocomplete

Tournament input uses `<input list="tournaments-list">` + `<datalist>` populated with all existing tournament names. The user can pick from the list or type a new name. Works without JavaScript; fully compatible with HTMX forms.

### Decision 4: Migration drops old TEXT columns

SQLite 3.35+ supports `ALTER TABLE DROP COLUMN`. Steps:
1. Create `Tournament` table
2. Seed from distinct non-null values across both `Match.Tournament` and `Squad.Tournament`
3. Add `TournamentId INT NULL FK` to `Match` and `Squad`
4. `UPDATE` both tables using name-match subquery
5. Drop old `Tournament TEXT` columns

**Rollback**: Pre-migration backup created automatically by `ensure_db()`.

### Decision 5: CSV export uses JOIN result

`get_match` in `repository.py` is updated to `LEFT JOIN Tournament` and return `TournamentName`. `csv_export.py` already reads `match["Tournament"]` — field renamed to `TournamentName` in the dict, so one line changes in `csv_export.py`.

## Risks / Trade-offs

- **SQLite DROP COLUMN version**: Requires SQLite ≥ 3.35 (March 2021). Python 3.10+ ships with SQLite 3.39+. Add a version check as a guard in the migration.
- **Name uniqueness**: UNIQUE on `Tournament.Name` means "Cup 2025" in Rugby and "Cup 2025" in Hockey would share one row. Acceptable — this is a single-user local app and the user controls naming.
- **Reports filter scope**: Without sport scoping, the tournament dropdown on the reports page shows all tournaments. Acceptable for now; can be filtered by template in a future iteration.

## Migration Plan

1. Auto-backup triggers in `ensure_db()` (already implemented)
2. New migration in `backend/db.py`:
   ```sql
   CREATE TABLE Tournament (
     Id INTEGER PRIMARY KEY AUTOINCREMENT,
     Name TEXT NOT NULL UNIQUE,
     CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
   );
   INSERT OR IGNORE INTO Tournament (Name)
     SELECT DISTINCT Tournament FROM Match WHERE Tournament IS NOT NULL
     UNION
     SELECT DISTINCT Tournament FROM Squad WHERE Tournament IS NOT NULL;
   ALTER TABLE Match ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id);
   UPDATE Match SET TournamentId = (SELECT Id FROM Tournament WHERE Name = Match.Tournament)
     WHERE Tournament IS NOT NULL;
   ALTER TABLE Squad ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id);
   UPDATE Squad SET TournamentId = (SELECT Id FROM Tournament WHERE Name = Squad.Tournament)
     WHERE Tournament IS NOT NULL;
   ALTER TABLE Match DROP COLUMN Tournament;
   ALTER TABLE Squad DROP COLUMN Tournament;
   ```
3. Update `docs/schema.sql`
