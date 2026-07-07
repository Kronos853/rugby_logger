## ADDED Requirements

### Requirement: Two-Screen Synchronization
The system SHALL synchronize video playback state and timestamps between the video player window and the control panel window.

#### Scenario: Pausing video from control panel
- **WHEN** the user clicks "Capture Timestamp" in the control panel
- **THEN** the video player window pauses and sends the current timestamp (in seconds) to the control panel

### Requirement: Log Match Events
The system SHALL allow users to log an event by selecting a subject (player or team), an action (from the sport template), an optional outcome, and a comment.

#### Scenario: Logging a player action
- **WHEN** the user selects a player, an action, an outcome, and clicks save
- **THEN** the event is saved to the database with the captured video timestamp and current match period

#### Scenario: Logging a team action
- **WHEN** the user selects a team (instead of a specific player) and logs an action
- **THEN** the event is saved and attributed to the team as a whole

### Requirement: Add Comments to Events
The system SHALL allow users to add comments to an event using preset buttons or manual text entry.

#### Scenario: Using a preset comment
- **WHEN** the user clicks a preset comment button associated with the selected action
- **THEN** the comment text is appended to the event's comment field

### Requirement: Click-to-Seek
The system SHALL allow users to click on a logged event in the timeline to seek the video to that event's timestamp.

#### Scenario: Seeking video from timeline
- **WHEN** the user clicks on an event row in the control panel timeline
- **THEN** the video player window seeks to the event's timestamp

### Requirement: Display Live Match Score
The system SHALL compute and display the current match score from logged events on the tagging control panel, match setup page, and matches list.

#### Scenario: Score updates after scoring event
- **WHEN** the user logs a try or a successful conversion (player or team subject)
- **THEN** the displayed score increases by the configured points (try: 5, conversion: 2 unless Failure)

#### Scenario: Team attribution for player events
- **WHEN** a scoring event is logged with a player as subject
- **THEN** points are attributed to that player's team in the match (lineup first, roster fallback)

#### Scenario: Team attribution for team events
- **WHEN** a scoring event is logged with a team as subject
- **THEN** points are attributed to the selected home or away team

### Requirement: Highlight Scoring Events in Timeline
The system SHALL visually emphasize timeline rows that represent scoring events.

#### Scenario: Bold scoring rows
- **WHEN** an event in the timeline is a try or a conversion that counts toward the score
- **THEN** that row is displayed in bold in the control panel timeline

### Requirement: Server-Side Event Draft
The system SHALL store in-progress tagging events in the database immediately upon timestamp capture, updating the same row as the user selects subject, action, outcome, and comment.

#### Scenario: Capture creates draft event
- **WHEN** the user clicks capture timestamp on the control panel
- **THEN** the server creates an Event row with match, period, and timestamp and returns updated timeline HTML

#### Scenario: Incremental field updates
- **WHEN** the user selects a player, team, action, or outcome on the control panel
- **THEN** the server updates the selected draft event via HTMX and returns updated UI fragments (timeline, score, selection state)

### Requirement: Client-Side Video Synchronization
The system SHALL use browser JavaScript (not HTMX) for video file playback and cross-window synchronization between the control panel and video player pages.

#### Scenario: Video file selection
- **WHEN** the user opens the video page and selects a local video file
- **THEN** playback is handled in the browser without uploading the video to the server

#### Scenario: BroadcastChannel sync
- **WHEN** the control panel sends pause, seek, or time-update messages
- **THEN** the video page responds via BroadcastChannel using static client JavaScript

### Requirement: CSV Import on Control Panel
The system SHALL expose CSV import alongside CSV export on the match tagging control panel.

#### Scenario: Import button placement
- **WHEN** the user opens the control panel for a match
- **THEN** an "Import from CSV" control is available next to "Export to CSV"

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

### Requirement: Main Navigation on Tagging Control Panel
The system SHALL display the main navigation bar on the tagging control panel page, consistent with all other pages.

#### Scenario: Navigation bar visible on tagging page
- **WHEN** the user opens the tagging control panel (`/tagging/<match_id>/control`)
- **THEN** the main navigation bar is visible at the top of the page, providing links to other sections (Home, Directories, Matches, Reports, Settings, Admin)

#### Scenario: Layout not broken by navigation bar
- **WHEN** the navigation bar is added to the tagging control panel
- **THEN** the fixed-height viewport layout remains intact — the tagging toolbar and split-pane content area still fill the remaining screen height without causing page-level scroll

#### Scenario: Navigation accessible without leaving match
- **WHEN** the user clicks a navigation link on the tagging control panel
- **THEN** they are taken to the corresponding page (standard browser navigation)
