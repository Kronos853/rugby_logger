## ADDED Requirements

### Requirement: Define Sport Templates
The system SHALL allow the definition of sport templates that contain categories, actions, and comment presets.

#### Scenario: Creating a new sport template
- **WHEN** the user creates a new sport template
- **THEN** the system saves the template with a unique name (e.g., "Rugby-7")

### Requirement: Define Categories and Actions
The system SHALL allow adding categories to a sport template, and actions to those categories.

#### Scenario: Adding an action to a category
- **WHEN** the user adds an action (e.g., "Pass") to a category (e.g., "Handling")
- **THEN** the action is associated with the category and available when logging events

### Requirement: Define Action Outcomes and Comments
The system SHALL allow configuring whether an action tracks outcomes (Success/Failure) and defining preset comment buttons for the action.

#### Scenario: Configuring action details
- **WHEN** the user configures an action
- **THEN** they can enable outcome tracking and add preset comments (e.g., "Short pass", "In contact")

### Requirement: Rename Actions
The system SHALL allow users to rename an existing action in a sport template.

#### Scenario: Renaming an action
- **WHEN** the user edits an action name in the template detail page and saves
- **THEN** the new name is persisted and reflected in tagging and CSV export

### Requirement: Rename Categories
The system SHALL allow users to rename an existing category in a sport template.

#### Scenario: Renaming a category
- **WHEN** the user edits a category name in the template detail page and saves
- **THEN** the new name is persisted and reflected in tagging and CSV export

### Requirement: Move Action Between Categories
The system SHALL allow users to move an action from one category to another within the same sport template.

#### Scenario: Changing action category
- **WHEN** the user selects a different category for an action in the template detail page
- **THEN** the action is moved to that category and appears under it in the template editor and tagging UI

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
