## ADDED Requirements

### Requirement: ShowInReport Flag on Category
The system SHALL allow each category to be marked as included or excluded from reports.

#### Scenario: Default value for new category
- **WHEN** a new category is created
- **THEN** `ShowInReport` defaults to `true`

#### Scenario: Toggling ShowInReport on a category
- **WHEN** the user unchecks "Show in report" for a category in the template editor
- **THEN** `ShowInReport` is set to `false` for that category, and all its actions are excluded from any report output

### Requirement: ShowInReport Flag on Action
The system SHALL allow each action to be marked as included or excluded from reports.

#### Scenario: Default value for new action
- **WHEN** a new action is created
- **THEN** `ShowInReport` defaults to `true`

#### Scenario: Toggling ShowInReport on an action
- **WHEN** the user unchecks "Show in report" for an action in the template editor
- **THEN** `ShowInReport` is set to `false` for that action, and it is excluded from any report output regardless of category setting

### Requirement: Period Count on Sport Template
The system SHALL store the expected number of periods (halves, thirds, etc.) for each sport template.

#### Scenario: Default period count
- **WHEN** a sport template is created without specifying period count
- **THEN** `PeriodCount` defaults to 2

#### Scenario: Setting period count
- **WHEN** the user sets `PeriodCount` to 3 on a template (e.g., Hockey)
- **THEN** the value is saved and available for display in match setup and tagging UI

#### Scenario: Existing templates after migration
- **WHEN** the migration runs on an existing database
- **THEN** all existing sport templates receive `PeriodCount = 2` (preserving Rugby-7 behavior)
