## MODIFIED Requirements

### Requirement: Export Database File
The system SHALL allow users to download the full SQLite database as a `.db` file containing all application data.

#### Scenario: Downloading database backup
- **WHEN** the user clicks "Download database" on the administration page
- **THEN** the system copies the on-disk SQLite database file and sends it as a download to the user's device

#### Scenario: Backup file format
- **WHEN** the database file is downloaded
- **THEN** it is a valid SQLite binary file openable by standard SQLite tools (e.g. DB Browser for SQLite)

#### Scenario: Backup filename
- **WHEN** the download starts without a custom name
- **THEN** the default filename includes the application name and current date (e.g. `SportsVideoLogger_2026-07-03.db`)

## ADDED Requirements

### Requirement: Import Database File
The system SHALL allow users to restore application data by uploading a previously exported SQLite `.db` file.

#### Scenario: Uploading a backup
- **WHEN** the user selects a valid `.db` file and confirms import on the administration page
- **THEN** the system replaces the current database file with the uploaded backup (after creating a safety copy of the current file)

#### Scenario: Reject invalid file
- **WHEN** the uploaded file is not a valid SQLite database
- **THEN** the system shows an error and does not replace the current database

#### Scenario: Application reload after import
- **WHEN** import completes successfully
- **THEN** the user is informed to reload the application and sees data from the imported backup
