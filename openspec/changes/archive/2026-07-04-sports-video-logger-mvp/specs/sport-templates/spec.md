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
