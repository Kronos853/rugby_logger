## MODIFIED Requirements

### Requirement: Team Report
The system SHALL generate a team report that aggregates statistics for all players in a team plus team-attributed events.

#### Scenario: Generating a team report
- **WHEN** the user selects "Team" report type, chooses a team, sets a date range, and submits
- **THEN** the system displays statistics grouped by category and action, summing events from all players in that team plus `SubjectType='team'` events for that team within the date range

#### Scenario: Team report split layout
- **WHEN** a team report is generated
- **THEN** results are shown in a two-column layout: a left column for the team report (~65% width) and a right column for the player panel (~35% width)
- **AND** the right column initially shows placeholder copy instructing the user to select an action

#### Scenario: Individual report without split
- **WHEN** the user generates an individual player report
- **THEN** results are shown in a single full-width column without the player panel

### Requirement: Player Drill-Down in Team Report
The system SHALL allow users to expand any action row in a **team** report to see a per-player (and team-attributed) breakdown of that action's metrics.

#### Scenario: Expand control visible on team report only
- **WHEN** a team report is displayed
- **THEN** each action row includes a control to expand player breakdown
- **AND** individual player reports do not show this control

#### Scenario: Player breakdown opens in panel
- **WHEN** the user activates the player breakdown control on an action row in a team report
- **THEN** the system loads (via HTMX) the per-player breakdown for that action into the player panel on the right
- **AND** the breakdown is not rendered as an inline sub-table below the action row

#### Scenario: Active action indication
- **WHEN** an action row's player breakdown is shown in the player panel
- **THEN** that action row is visually indicated as active in the team report table

#### Scenario: Player breakdown is read-only
- **WHEN** the player breakdown is displayed in the player panel
- **THEN** player rows show metrics for the selected action only
- **AND** player rows do not navigate to or load a full individual player report in the panel

#### Scenario: Team-attributed events in breakdown
- **WHEN** some events for the action have `SubjectType='team'` for the reported team
- **THEN** those events appear as a separate row labeled with the team name in the player breakdown

#### Scenario: Breakdown respects report filters
- **WHEN** the user expands player breakdown for an action
- **THEN** only events matching the current report filters (date range, tournament, and match when per-match breakdown is enabled) are included

#### Scenario: Collapsing player breakdown
- **WHEN** the user activates the player breakdown control again on the same action row, or selects another action
- **THEN** the player panel is cleared or updated accordingly
- **AND** no inline sub-table remains below the action row

#### Scenario: Zero-count players hidden
- **WHEN** a player has no events for the selected action in the filtered period
- **THEN** that player does not appear in the breakdown

## REMOVED Requirements

_(none — inline player breakdown scenarios merged into panel-based scenarios above)_
