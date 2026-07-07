## ADDED Requirements

### Requirement: Player Drill-Down in Team Report
The system SHALL allow users to expand any action row in a **team** report to see a per-player (and team-attributed) breakdown of that action's metrics.

#### Scenario: Expand control visible on team report only
- **WHEN** a team report is displayed
- **THEN** each action row includes a control to expand player breakdown
- **AND** individual player reports do not show this control

#### Scenario: Loading player breakdown
- **WHEN** the user expands player breakdown for an action
- **THEN** the system loads (via HTMX) a sub-table listing each player who performed that action with the same metric format as the parent row (count or total/success/failure/%)

#### Scenario: Team-attributed events in breakdown
- **WHEN** some events for the action have `SubjectType='team'` for the reported team
- **THEN** those events appear as a separate row labeled with the team name in the player breakdown sub-table

#### Scenario: Breakdown respects report filters
- **WHEN** the user expands player breakdown
- **THEN** only events matching the current report filters (date range, tournament, and match when per-match breakdown is enabled) are included

#### Scenario: Collapsing player breakdown
- **WHEN** the user clicks the expand control again
- **THEN** the player sub-table is hidden

#### Scenario: Zero-count players hidden
- **WHEN** a player has no events for the selected action in the filtered period
- **THEN** that player does not appear in the breakdown sub-table
