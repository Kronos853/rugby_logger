## Why

Tournaments are currently stored as free-text strings in `Match.Tournament` and `Squad.Tournament`. This makes it impossible to filter reports by tournament, group matches under a named tournament, or ensure consistent naming. Converting to a proper reference table unlocks tournament-level reporting in Phase 2.

## What Changes

- **New `Tournament` table** — `(Id, Name, CreatedAt)`, global reference (not scoped to a sport template)
- **`Match.TournamentId`** replaces `Match.Tournament TEXT` — FK to `Tournament`
- **`Squad.TournamentId`** replaces `Squad.Tournament TEXT` — FK to `Tournament`
- **Inline tournament creation** — when creating or editing a match/squad, user picks an existing tournament from a dropdown or types a new name to create it on the fly
- **Data migration** — existing `Tournament` text values are extracted, deduplicated, inserted into the new table, and matched back to their rows; the old text columns are dropped
- **Reporting filter** — the `/reports` page gains a "Tournament" filter in addition to date range

## Capabilities

### New Capabilities

- `tournament-management`: CRUD for the `Tournament` reference table, inline creation from match/squad forms, filtered by sport template

### Modified Capabilities

- `sport-templates`: no changes required — Tournament is now a standalone reference table, independent of sport type
- `reporting`: Report filter gains an optional tournament selector (delta spec needed — adds new filter requirement)

## Impact

- **DB schema**: New `Tournament` table; `Match` and `Squad` lose `Tournament TEXT`, gain `TournamentId INT NULL FK`
- **`backend/db.py`**: Migration creates `Tournament` table, adds FK columns, migrates string data, drops old columns
- **`backend/repository.py`**: All match/squad create/update functions updated; new `get_tournaments_for_template`, `get_or_create_tournament` functions
- **`backend/app.py`**: Match create/setup routes pass tournament dropdown data; squad routes same
- **Templates**: `matches/index.html`, `matches/setup.html`, `squads/index.html` — text inputs replaced with `<select>` + optional new-entry field
- **`backend/csv_export.py`**: Tournament name fetched from new table for filename generation
- **`phase2-reports`**: The reporting filter for tournament is a downstream addition; the reporting change depends on this refactor being applied first
