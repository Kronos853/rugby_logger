## ADDED Requirements

### Requirement: Administration Page
The system SHALL provide an administration page accessible from the main navigation for local database maintenance operations.

#### Scenario: Opening administration
- **WHEN** the user navigates to the administration page
- **THEN** they see options for database backup (and future maintenance actions)

### Requirement: Export Database File
The system SHALL allow users to download the full SQLite database as a `.db` file containing all application data.

#### Scenario: Downloading database backup
- **WHEN** the user clicks "Download database" on the administration page
- **THEN** the system persists the current in-memory database state and downloads a `.db` file to the user's device

#### Scenario: Backup file format
- **WHEN** the database file is downloaded
- **THEN** it is a valid SQLite binary file openable by standard SQLite tools (e.g. DB Browser for SQLite)

#### Scenario: Backup filename
- **WHEN** the download starts without a custom name
- **THEN** the default filename includes the application name and current date (e.g. `SportsVideoLogger_2026-07-03.db`)
