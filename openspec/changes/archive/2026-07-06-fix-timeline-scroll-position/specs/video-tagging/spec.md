## MODIFIED Requirements

### Requirement: Timeline Always Visible During Tagging
The system SHALL display the event timeline simultaneously with the input controls on the tagging control panel, without requiring page scroll.

#### Scenario: Timeline visible on load
- **WHEN** the user opens the tagging control panel
- **THEN** the event timeline is visible on screen alongside the input controls without scrolling

#### Scenario: Timeline visible after tagging an event
- **WHEN** the user captures and tags an event (player, action, outcome)
- **THEN** the timeline remains in view without the user needing to scroll

#### Scenario: Timeline scrollable independently
- **WHEN** the timeline contains more events than fit vertically
- **THEN** the user can scroll the timeline area independently without affecting the input controls

#### Scenario: Timeline columns scrollable horizontally
- **WHEN** the timeline columns do not fit in the available width
- **THEN** the user can scroll the timeline horizontally to access all columns
- **AND** the input controls remain unaffected

#### Scenario: Timeline scroll position preserved on row select
- **WHEN** the user has scrolled the timeline to a position other than the default
- **AND** the user selects a timeline row (event) triggering a page reload
- **THEN** the timeline vertical scroll position is restored to the same position after reload
- **AND** the user is not jumped to the top or bottom of the event list

#### Scenario: Timeline scroll position preserved on event update
- **WHEN** the user has scrolled the timeline to a position other than the default
- **AND** the user updates the selected event via input controls (player, action, outcome, comment)
- **THEN** the timeline vertical scroll position is restored after the page reload
