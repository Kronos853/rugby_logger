## Why

There is a need for a fast, reliable tool to log sports team statistics from video recordings post-match. The current prototype relies on a fragile `localStorage` connection between two browser windows and lacks data persistence. We need a robust MVP that stores data locally, supports multiple teams, and allows exporting events to CSV for analysis and AI processing.

## What Changes

- Migrate persistence from Dexie/IndexedDB to **SQLite WASM (sql.js)** with a SQL repository layer.
- Build a reliable two-screen interface (video player on screen 2, control panel on screen 1) with synchronized state.
- Create a universal sport template system (starting with Rugby-7) to define categories, actions, and comment presets.
- Implement a CSV export feature with a fixed column format for external AI processing.
- Support "virtual teams" (teams without players) for logging team-wide or unassigned actions.
- **Auto-calculate match score** from logged events (Rugby-7: try = 5, conversion without Failure = 2).
- Allow **renaming actions** in sport templates and **editing squad name/tournament** when managing squads.
- Provide **Windows launch scripts** (`start.bat`) and developer context docs.
- Add an **administration page** with **full database export** to `.db` file.

## Capabilities

### New Capabilities
- `sport-templates`: Define categories, actions, and comment presets for different sports (e.g., Rugby-7); rename actions.
- `team-management`: Manage teams (with or without players), players, saved squads (with edit name/tournament), and match metadata (date, tournament, periods).
- `video-tagging`: Two-screen interface for logging events (player/team, action, outcome, comment) tied to video timestamps (seconds), click-to-seek, **live score display**, **bold scoring events in timeline**.
- `data-export`: Export match events to a standardized CSV format (`Тайм, Время, Игрок/Команда, Категория, Действие, Результат, Комментарий`).
- `administration`: Local maintenance UI; **download full SQLite `.db` backup** of all data.

### Modified Capabilities
- (None - this is a new project foundation)

## Impact

- Replaces the existing `control_panel.html` and `video_screen.html` prototypes with a structured, database-backed application.
- Establishes the core data model (MVP / Phase 1) required before building built-in reports and AI chat features (Phase 2).
- Requires **SQLite WASM (sql.js)** with schema from `docs/schema.sql`, persisted via IndexedDB blob storage.
- Score logic centralized in `src/lib/match-score.ts` (not persisted in `Match.scoreHome/scoreAway` — computed from events).
