## ADDED Requirements

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

### Requirement: Tagging Page Viewport Layout
The tagging control panel SHALL use a fixed-height viewport layout occupying the full browser window height.

#### Scenario: No page-level scroll
- **WHEN** the tagging control panel is open
- **THEN** the browser scrollbar for the page is not visible and page-level scroll does not occur

#### Scenario: Input column scrolls independently
- **WHEN** the input controls (players, actions, comments) exceed the available height
- **THEN** the input column scrolls vertically without affecting the timeline column

### Requirement: Toolbar Navigation and Actions
The tagging control panel SHALL provide a single toolbar row containing match context, the capture button, and a collapsed menu for secondary actions.

#### Scenario: Secondary actions in menu
- **WHEN** the user opens the toolbar menu
- **THEN** they can access: open video window, export CSV, import CSV, and navigate back to match setup

#### Scenario: Flash messages in toolbar
- **WHEN** a CSV import completes (success or error)
- **THEN** the result message is displayed in the toolbar area, not as a separate page section
