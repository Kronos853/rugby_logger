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
