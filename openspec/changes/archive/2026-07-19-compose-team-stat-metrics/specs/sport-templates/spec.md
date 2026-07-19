## MODIFIED Requirements

### Requirement: Team Statistic Metric Definitions
The system SHALL allow defining ordered team-statistic metrics on a sport template via a dedicated configuration page. Each metric SHALL have a display name and one or more additive conditions; each condition SHALL select a source action, outcome filter (`any`, `Success`, or `Failure`), and perspective (`own` or `opponent`).

#### Scenario: Open metric constructor from template
- **WHEN** the user opens the sport template detail page
- **THEN** they can navigate to a separate team-statistic metrics page for that template

#### Scenario: Create a metric
- **WHEN** the user adds a team-statistic metric on the metrics page with a name, action, outcome filter (`any`, `Success`, or `Failure`), and perspective
- **THEN** the metric and its first condition are stored for that sport template

#### Scenario: Create a metric with its first condition
- **WHEN** the user creates a team-statistic metric with a name, action, outcome filter, and perspective
- **THEN** the metric and its first condition are stored for that sport template

#### Scenario: Outcome-specific named metrics
- **WHEN** the user creates two metrics for the same action with filters `Success` and `Failure` and distinct names
- **THEN** both metrics are stored and available for match team statistics

#### Scenario: Add multiple conditions
- **WHEN** the user adds more conditions to an existing metric
- **THEN** every condition is stored under that metric
- **AND** all conditions are available to match team statistics

#### Scenario: Own and opponent perspectives
- **WHEN** the user configures a condition
- **THEN** they can choose whether opponent events are counted via the checkbox “Учитывать события противника”
- **AND** unchecked stores perspective `own`
- **AND** checked stores perspective `opponent`

#### Scenario: Condition ordering
- **WHEN** a metric has multiple conditions
- **THEN** the constructor displays them in insertion order
- **AND** does not offer condition up/down controls

#### Scenario: Visual metric grouping
- **WHEN** the constructor page lists metrics
- **THEN** each metric is rendered as its own visually separated block
- **AND** the metric name is typographically dominant over its condition rows
- **AND** destructive and reorder controls are visually subdued relative to primary actions

#### Scenario: Metric ordering
- **WHEN** metrics are defined with sort order
- **THEN** the match statistics page lists them in that order

#### Scenario: Reorder metrics with up/down controls
- **WHEN** the user moves a metric up or down on the metrics page
- **THEN** its sort order is swapped with the adjacent metric
- **AND** the new order is persisted

#### Scenario: Update a condition
- **WHEN** the user changes a condition’s action, outcome filter, or perspective
- **THEN** the change is persisted and reflected on subsequent match statistics views

#### Scenario: Delete a condition
- **WHEN** the user deletes a condition from a metric that has other conditions
- **THEN** only that condition is removed
- **AND** the metric remains configured

#### Scenario: Deleting the last condition deletes the metric
- **WHEN** the user deletes the only remaining condition through condition controls
- **THEN** that condition is removed
- **AND** the parent metric is also deleted

#### Scenario: Delete or update a metric
- **WHEN** the user updates or deletes a team-statistic metric on the metrics page
- **THEN** the change is persisted and reflected on subsequent match statistics views

#### Scenario: Delete or rename a metric
- **WHEN** the user deletes or renames a team-statistic metric
- **THEN** the change is persisted and reflected on subsequent match statistics views

#### Scenario: Action must belong to template
- **WHEN** the user creates or updates a condition
- **THEN** the selected action MUST belong to a category of the same sport template

#### Scenario: Existing metric migration
- **WHEN** the database migration processes an existing single-condition metric
- **THEN** it creates one equivalent condition with perspective `own`
- **AND** the metric’s match-statistics values remain unchanged

#### Scenario: Cascade metrics when unused action is deleted
- **WHEN** the user deletes an action that is not referenced by any match events
- **THEN** conditions that reference that action are deleted
- **AND** metrics left with no remaining conditions are also deleted

#### Scenario: Cascade one condition when unused action is deleted
- **WHEN** the user deletes an action that is not referenced by any match events
- **THEN** conditions that reference that action are deleted
- **AND** metrics with other conditions remain

#### Scenario: Remove metric left empty by action deletion
- **WHEN** deleting an unused action removes the final condition of a metric
- **THEN** that empty metric is also deleted

#### Scenario: Block action delete when used in matches
- **WHEN** the user attempts to delete an action that appears in match events
- **THEN** the delete is rejected and match event data is left unchanged
