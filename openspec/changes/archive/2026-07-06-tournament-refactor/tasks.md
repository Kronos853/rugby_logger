## 1. Database Migration

- [x] 1.1 Add migration in `backend/db.py`: create `Tournament (Id, Name UNIQUE, CreatedAt)` table
- [x] 1.2 Seed `Tournament` from all distinct non-null tournament strings across `Match` and `Squad` (`INSERT OR IGNORE`)
- [x] 1.3 `ALTER TABLE Match ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id)`
- [x] 1.4 `UPDATE Match SET TournamentId = (SELECT Id FROM Tournament WHERE Name = Match.Tournament) WHERE Tournament IS NOT NULL`
- [x] 1.5 `ALTER TABLE Squad ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id)`
- [x] 1.6 `UPDATE Squad SET TournamentId = (SELECT Id FROM Tournament WHERE Name = Squad.Tournament) WHERE Tournament IS NOT NULL`
- [x] 1.7 `ALTER TABLE Match DROP COLUMN Tournament` (add SQLite ≥ 3.35 version guard)
- [x] 1.8 `ALTER TABLE Squad DROP COLUMN Tournament` (same guard)
- [x] 1.9 Update `docs/schema.sql` to add `Tournament` table and update `Match`, `Squad` columns

## 2. Repository Layer

- [x] 2.1 Add `get_tournaments(conn) -> list` to `repository.py` — returns all tournaments sorted by name
- [x] 2.2 Add `get_or_create_tournament(conn, name: str) -> int | None` — returns existing ID or inserts new row; returns `None` for empty/None name
- [x] 2.3 Update `create_match` to accept `tournament_name`, call `get_or_create_tournament`, store `TournamentId`
- [x] 2.4 Update `update_match_details` similarly
- [x] 2.5 Update `create_squad` to accept `tournament_name`, call `get_or_create_tournament`
- [x] 2.6 Update `update_squad` similarly
- [x] 2.7 Update `get_match` to `LEFT JOIN Tournament` and expose `TournamentName` field
- [x] 2.8 Update `get_matches` list query to `LEFT JOIN Tournament` for match list display
- [x] 2.9 Update `get_squads` list query to `LEFT JOIN Tournament` for squad list display

## 3. Application Routes

- [x] 3.1 Update match creation route in `app.py`: call `get_tournaments`, pass list to template
- [x] 3.2 Update match setup route: call `get_tournaments`, pass list to template
- [x] 3.3 Update squad creation route: call `get_tournaments`, pass list to template
- [x] 3.4 Update squad update route similarly

## 4. Templates

- [x] 4.1 Replace `<input name="tournament">` with datalist pattern in `templates/matches/index.html` (create form)
- [x] 4.2 Replace `<input name="tournament">` with datalist pattern in `templates/matches/setup.html` (edit form)
- [x] 4.3 Replace `<input name="tournament">` with datalist pattern in `templates/squads/index.html` (both create and edit forms)
- [x] 4.4 Update `templates/matches/index.html` list display: use `m.TournamentName`
- [x] 4.5 Update `templates/squads/index.html` list display: use `squad.TournamentName`

## 5. CSV Export Fix

- [x] 5.1 Update `backend/csv_export.py`: replace `match["Tournament"]` with `match["TournamentName"]`

## 6. Reports Integration (apply after phase2-reports)

- [ ] 6.1 Add optional `tournament_id` filter to `get_report_data` in `repository.py`
- [ ] 6.2 Update `/reports` route to pass `get_tournaments()` result to form
- [ ] 6.3 Add tournament `<select>` (with "All tournaments" default) to `templates/reports.html`
