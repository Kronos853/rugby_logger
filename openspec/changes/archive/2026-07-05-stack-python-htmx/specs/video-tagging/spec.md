## ADDED Requirements

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
