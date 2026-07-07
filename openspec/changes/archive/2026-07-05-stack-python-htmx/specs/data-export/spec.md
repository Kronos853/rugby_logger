## ADDED Requirements

### Requirement: Import Match Events from CSV
The system SHALL allow users to import match events from a CSV file on the match tagging control panel.

#### Scenario: Importing from control panel
- **WHEN** the user clicks "Import from CSV" on the control panel for the current match
- **THEN** the system accepts a CSV file and creates Event rows for that match

#### Scenario: Standard import format
- **WHEN** a CSV file is imported
- **THEN** it MUST use the same columns as export: `Тайм`, `Время`, `Игрок/Команда`, `Категория`, `Действие`, `Результат`, `Комментарий`

#### Scenario: UTF-8 with BOM
- **WHEN** the CSV file includes a UTF-8 BOM (as produced by export)
- **THEN** the import parses the file correctly

### Requirement: CSV Import Validation
The system SHALL validate imported rows against the current match context before saving.

#### Scenario: Resolve subject by name
- **WHEN** a row names a player or team in `Игрок/Команда`
- **THEN** the system maps it to a player or team participating in the current match (lineup or roster)

#### Scenario: Resolve action by name
- **WHEN** a row names category and action
- **THEN** the system maps them to an Action from the match's sport template

#### Scenario: Reject invalid rows
- **WHEN** a row cannot be resolved (unknown player, team, or action)
- **THEN** the import is aborted with a clear error listing row numbers and no partial data is saved

### Requirement: CSV Import Conflict Handling
The system SHALL ask the user how to handle existing events before importing into a match that already has logged events.

#### Scenario: Replace existing events
- **WHEN** the match has events and the user chooses to replace
- **THEN** all existing events for that match are deleted and replaced by imported rows

#### Scenario: Append to existing events
- **WHEN** the match has events and the user chooses to append
- **THEN** imported rows are added without deleting existing events

#### Scenario: Empty match import
- **WHEN** the match has no events
- **THEN** imported rows are saved without an extra confirmation step

#### Scenario: UI refresh after import
- **WHEN** import completes successfully
- **THEN** the timeline and match score on the control panel update to reflect imported events
