## ADDED Requirements

### Requirement: Tagging Step Scroll Focus
The tagging control panel SHALL automatically scroll the input column to the next workflow step after capture or field update, so the operator does not need to manually scroll the left panel.

#### Scenario: Focus after new event capture
- **WHEN** the user captures a new event via "НОВОЕ СОБЫТИЕ"
- **THEN** the input column scrolls to the player/team selection step

#### Scenario: Focus after player selection
- **WHEN** the user selects a player or team for the current event
- **THEN** the input column scrolls to the action selection step

#### Scenario: Focus after action with outcome
- **WHEN** the user selects an action that requires an outcome
- **THEN** the input column scrolls to the outcome controls

#### Scenario: Focus after action without outcome
- **WHEN** the user selects an action that does not require an outcome
- **THEN** the input column scrolls to the comment section

#### Scenario: Focus after outcome
- **WHEN** the user sets an outcome (Success, Failure, or none)
- **THEN** the input column scrolls to the comment section

#### Scenario: Timeline select incomplete event
- **WHEN** the user selects an incomplete event from the timeline
- **THEN** the input column scrolls to the first missing required step

#### Scenario: Scroll focus overrides scroll restore
- **WHEN** the server signals a scroll focus target for the current page load
- **THEN** the input column scroll position is set to that step instead of restoring the previous scroll position from session storage
