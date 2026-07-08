## ADDED Requirements

### Requirement: Current Event Draft Panel
The tagging control panel SHALL display a sticky "ТЕКУЩЕЕ СОБЫТИЕ" block above the input steps showing draft mode, field summary, and match time context.

#### Scenario: Draft block visible on load
- **WHEN** the user opens the tagging control panel
- **THEN** the "ТЕКУЩЕЕ СОБЫТИЕ" block is visible at the top of the input column with summary chips for player, action, and outcome

#### Scenario: New event mode
- **WHEN** the user captures a new event via "НОВОЕ СОБЫТИЕ"
- **THEN** the draft block shows badge "НОВОЕ", the captured period and timestamp

#### Scenario: Edit event mode
- **WHEN** the user selects an existing event from the timeline
- **THEN** the draft block shows badge "РЕДАКТИРОВАНИЕ" and populates summary chips from the selected event
