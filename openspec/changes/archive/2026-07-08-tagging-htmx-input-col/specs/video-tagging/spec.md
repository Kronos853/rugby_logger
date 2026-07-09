## MODIFIED Requirements

### Requirement: Server-Side Event Draft
The system SHALL store in-progress tagging events in the database immediately upon timestamp capture, updating the same row as the user selects subject, action, outcome, and comment.

#### Scenario: Capture creates draft event
- **WHEN** the user clicks capture timestamp on the control panel
- **THEN** the server creates an Event row with match, period, and timestamp
- **AND** returns an HTMX partial update without a full page reload

#### Scenario: Incremental field updates
- **WHEN** the user selects a player, team, action, or outcome on the control panel
- **THEN** the server updates the selected draft event via HTMX
- **AND** returns updated UI fragments for the input column (selection state, draft panel, conditional steps), timeline, and score
- **AND** does not reload the toolbar or main navigation

#### Scenario: HTMX fallback to full page
- **WHEN** a tagging form is submitted without the HTMX request header
- **THEN** the server responds with a redirect to the control panel as before

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
- **AND** the user selects a timeline row (event) triggering an HTMX update
- **THEN** the timeline vertical scroll position is restored to the same position after the swap
- **AND** the user is not jumped to the top or bottom of the event list

#### Scenario: Timeline scroll position preserved on event update
- **WHEN** the user has scrolled the timeline to a position other than the default
- **AND** the user updates the selected event via input controls (player, action, outcome, comment)
- **THEN** the timeline vertical scroll position is restored after the HTMX swap

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
- **WHEN** the server signals a scroll focus target in the HTMX response
- **THEN** the input column scroll position is set to that step instead of restoring the previous scroll position

## ADDED Requirements

### Requirement: HTMX on Tagging Control Panel
The tagging control panel SHALL load the HTMX library and use partial HTML swaps for input and timeline updates instead of full page reloads on routine tagging actions.

#### Scenario: HTMX loaded on control panel
- **WHEN** the user opens the tagging control panel
- **THEN** the HTMX script is available on the page

#### Scenario: Input forms use HTMX
- **WHEN** the user submits a player, action, outcome, or comment form in the input column
- **THEN** the request is sent via HTMX partial update
- **AND** the toolbar video time label remains unchanged without re-render

#### Scenario: Capture uses HTMX
- **WHEN** the user clicks "НОВОЕ СОБЫТИЕ"
- **THEN** the capture request is sent via HTMX partial update
- **AND** the input column and timeline update without a full page reload

#### Scenario: Period switch uses HTMX
- **WHEN** the user changes the match period via the toolbar half selector
- **THEN** the update is sent via HTMX partial update without a full page reload
