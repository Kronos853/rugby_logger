## ADDED Requirements

### Requirement: Settings Page
The system SHALL provide a settings page accessible from the main navigation.

#### Scenario: Opening settings
- **WHEN** the user navigates to `/settings`
- **THEN** they see application preferences including primary team selection

### Requirement: Configure Primary Team
The system SHALL allow the user to designate one team as the primary (default) team for reporting.

#### Scenario: Saving primary team
- **WHEN** the user selects a team on the settings page and saves
- **THEN** the primary team is persisted in the database

#### Scenario: Clearing primary team
- **WHEN** the user selects "not set" and saves
- **THEN** no primary team is stored and reports do not pre-select a team

#### Scenario: Invalid team rejected
- **WHEN** the user submits a team id that does not exist
- **THEN** the system shows an error and does not save the setting
