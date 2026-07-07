## ADDED Requirements

### Requirement: Export Match Events to CSV
The system SHALL allow users to export all logged events for a specific match to a CSV file.

#### Scenario: Exporting match data
- **WHEN** the user clicks the "Export to CSV" button for a match
- **THEN** the system generates and downloads a CSV file containing all match events

### Requirement: Standardized CSV Format
The system SHALL format the exported CSV with specific, standardized columns to ensure compatibility with external AI processing tools.

#### Scenario: Verifying CSV columns
- **WHEN** the CSV file is generated
- **THEN** it contains exactly these columns: `Тайм`, `Время`, `Игрок/Команда`, `Категория`, `Действие`, `Результат`, `Комментарий`
