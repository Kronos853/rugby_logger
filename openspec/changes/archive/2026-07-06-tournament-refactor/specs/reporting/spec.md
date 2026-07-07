## ADDED Requirements

### Requirement: Tournament Filter on Reports Page
The system SHALL allow users to filter a report by tournament in addition to date range.

#### Scenario: Tournament filter shown in report form
- **WHEN** the user opens the reports page
- **THEN** a "Tournament" dropdown shows all tournaments for the selected sport template (plus an "All tournaments" option)

#### Scenario: Filtering by tournament
- **WHEN** the user selects a specific tournament before generating a report
- **THEN** only events from matches linked to that tournament are included in the report output

#### Scenario: No tournament filter applied
- **WHEN** the user leaves "All tournaments" selected
- **THEN** events from all matches within the date range are included regardless of tournament
