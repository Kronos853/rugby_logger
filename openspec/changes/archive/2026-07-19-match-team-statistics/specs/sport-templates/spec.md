## ADDED Requirements

### Requirement: Team Statistic Metric Definitions
The system SHALL allow defining ordered team-statistic metrics on a sport template via a dedicated configuration page, each with a display name, source action, and outcome filter.

#### Scenario: Open metric constructor from template
- **WHEN** the user opens the sport template detail page
- **THEN** they can navigate to a separate team-statistic metrics page for that template

#### Scenario: Create a metric
- **WHEN** the user adds a team-statistic metric on the metrics page with a name, action, and outcome filter (`any`, `Success`, or `Failure`)
- **THEN** the metric is stored for that sport template

#### Scenario: Outcome-specific named metrics
- **WHEN** the user creates two metrics for the same action with filters `Success` and `Failure` and distinct names
- **THEN** both metrics are stored and available for match team statistics

#### Scenario: Metric ordering
- **WHEN** metrics are defined with sort order
- **THEN** the match statistics page lists them in that order

#### Scenario: Reorder metrics with up/down controls
- **WHEN** the user moves a metric up or down on the metrics page
- **THEN** its sort order is swapped with the adjacent metric
- **AND** the new order is persisted

#### Scenario: Delete or update a metric
- **WHEN** the user updates or deletes a team-statistic metric on the metrics page
- **THEN** the change is persisted and reflected on subsequent match statistics views

#### Scenario: Action must belong to template
- **WHEN** the user creates a metric
- **THEN** the selected action MUST belong to a category of the same sport template

#### Scenario: Cascade metrics when unused action is deleted
- **WHEN** the user deletes an action that is not referenced by any match events
- **THEN** team-statistic metrics that reference that action are also deleted

#### Scenario: Block action delete when used in matches
- **WHEN** the user attempts to delete an action that appears in match events
- **THEN** the delete is rejected and match event data is left unchanged
