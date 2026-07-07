# Change: Player profile fields

## Why

Roster management needs more than a short tagging label: full name and date of birth are required for reports and squad administration.

## What Changes

- Extend `Player` table with `FullName` and `BirthDay`
- Add player profile edit page (`/directories/teams/<team_id>/players/<player_id>/edit`)
- Show full name and birth date in team roster table
- SQLite migration for existing databases (`ALTER TABLE`)

## Impact

- Affected specs: `team-management`
- Affected code: `backend/db.py`, `backend/repository.py`, `backend/app.py`, `templates/teams/`, `docs/schema.sql`
