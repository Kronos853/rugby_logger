## ADDED Requirements

### Requirement: Local Application Server
The system SHALL run as a local Python web server that serves all application pages and API endpoints from a single process.

#### Scenario: Starting the application
- **WHEN** the user runs the application start command
- **THEN** the Python server starts and listens on a fixed local address (default `http://127.0.0.1:5000`)

#### Scenario: Single origin for all pages
- **WHEN** the user navigates between directories, matches, tagging, and administration
- **THEN** all pages are served from the same origin so browser storage and window communication are consistent

### Requirement: SQLite File Database
The system SHALL persist all application data in a SQLite database stored as a file on the local filesystem.

#### Scenario: Database file location
- **WHEN** the server starts
- **THEN** it uses a SQLite file at a configured path (default `data/sports_logger.db`)

#### Scenario: Schema initialization
- **WHEN** the database file is new or missing tables
- **THEN** the server applies the schema from `docs/schema.sql` (or equivalent DDL)

#### Scenario: Data survives restart
- **WHEN** the user stops and restarts the application
- **THEN** all previously saved teams, matches, and events remain available

### Requirement: HTMX Server-Rendered UI
The system SHALL deliver the user interface as HTML templates with HTMX-driven partial updates instead of a client-side SPA framework.

#### Scenario: Partial page update
- **WHEN** the user performs an action that changes a list or form (e.g. add player to squad)
- **THEN** the server returns an HTML fragment and the client swaps it into the target element without a full page reload

#### Scenario: No frontend build step
- **WHEN** deploying or running the application for local use
- **THEN** no Node.js, Vite, or npm build is required for the UI

### Requirement: Static Assets for Tagging
The system SHALL serve CSS and a small JavaScript bundle for video synchronization separately from HTMX interactions.

#### Scenario: Video window script
- **WHEN** the video player page loads
- **THEN** it includes static JavaScript for local video file playback and BroadcastChannel sync
