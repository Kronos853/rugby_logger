# reporting Specification

## Purpose
Built-in statistical reports for team and individual performance over a date range.

## Requirements

### Requirement: Reporting Page
The system SHALL provide a dedicated reports page accessible from the main navigation.

#### Scenario: Opening the reports page
- **WHEN** the user navigates to `/reports`
- **THEN** they see a form to select report type (team or individual), target (team or player), and date range

#### Scenario: Report form fields by type
- **WHEN** the user selects "Team" report type
- **THEN** the player selection field is hidden and the team selection field is shown

#### Scenario: Individual report form fields
- **WHEN** the user selects "Individual" report type
- **THEN** the team selection field is hidden and the player selection field is shown

### Requirement: Team Report
The system SHALL generate a team report that aggregates statistics for all players in a team plus team-attributed events.

#### Scenario: Generating a team report
- **WHEN** the user selects "Team" report type, chooses a team, sets a date range, and submits
- **THEN** the system displays statistics grouped by category and action, summing events from all players in that team plus `SubjectType='team'` events for that team within the date range

### Requirement: Individual Player Report
The system SHALL generate an individual report that aggregates statistics for a single player.

#### Scenario: Generating an individual report
- **WHEN** the user selects "Individual" report type, chooses a player, sets a date range, and submits
- **THEN** the system displays statistics grouped by category and action for that player's events within the date range

### Requirement: Report Filters by Date Range
The system SHALL allow users to filter a report by a date range.

#### Scenario: Date range filter applied
- **WHEN** the user sets a start date and end date before generating a report
- **THEN** only events from matches whose `MatchDate` falls within the range (inclusive) are included in the report

### Requirement: Tournament Filter on Reports Page
The system SHALL allow users to filter a report by tournament in addition to date range.

#### Scenario: Tournament filter shown in report form
- **WHEN** the user opens the reports page
- **THEN** a "Tournament" dropdown shows all tournaments (plus an "All tournaments" option)

#### Scenario: Filtering by tournament
- **WHEN** the user selects a specific tournament before generating a report
- **THEN** only events from matches linked to that tournament are included in the report output

#### Scenario: No tournament filter applied
- **WHEN** the user leaves "All tournaments" selected
- **THEN** events from all matches within the date range are included regardless of tournament

### Requirement: Per-Match Breakdown
The system SHALL allow users to view report results broken down by individual match.

#### Scenario: Enabling per-match breakdown
- **WHEN** the user enables the "by match" option before generating a report
- **THEN** the results are rendered as a list of match sections (match date, opponent), each with its own category/action statistics

#### Scenario: Per-match totals
- **WHEN** per-match breakdown is enabled
- **THEN** each match section shows the same metric format (count or total/success/failure/%) as the flat report

### Requirement: Report Structure — Category and Action Grouping
The system SHALL display report results grouped by category at the top level and action within each category.

#### Scenario: Report renders categories
- **WHEN** a report is generated
- **THEN** actions are shown under their respective category headers in sort order

#### Scenario: Only ShowInReport actions appear
- **WHEN** a report is generated
- **THEN** only categories and actions where `ShowInReport = true` are included in the output

#### Scenario: Zero-count rows hidden
- **WHEN** an action has `ShowInReport = true` but zero events in the selected period
- **THEN** that action row is not displayed in the report

### Requirement: Report Metrics by Outcome Type
The system SHALL display different metrics depending on whether an action tracks outcomes.

#### Scenario: Action without outcome
- **WHEN** an action has `HasOutcome = false`
- **THEN** the report shows a single count (number of events)

#### Scenario: Action with outcome
- **WHEN** an action has `HasOutcome = true`
- **THEN** the report shows: Total count, Success count, Failure count, and Success percentage (rounded to one decimal)

### Requirement: Comment Drill-Down
The system SHALL allow users to expand any action row to see a breakdown of events by comment text.

#### Scenario: Expanding comment detail
- **WHEN** the user clicks the expand control on an action row
- **THEN** the system loads (via HTMX) a sub-table listing each distinct comment and its event count (or outcome split if `HasOutcome = true`)

#### Scenario: Events with no comment
- **WHEN** some events for an action have no comment
- **THEN** those events are grouped under a "— no comment —" row in the drill-down

#### Scenario: Collapsing comment detail
- **WHEN** the user clicks the expand control again
- **THEN** the comment sub-table is hidden

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

### Requirement: Default Primary Team in Team Report
The system SHALL pre-select the configured primary team when opening the reports page with team report type.

#### Scenario: Primary team pre-selected
- **WHEN** the user opens the reports page, report type is "team", a primary team is configured in settings, and no team was submitted in the request
- **THEN** the team dropdown shows the primary team as selected

#### Scenario: User overrides primary team
- **WHEN** the user selects a different team in the report form and submits
- **THEN** the report is generated for the selected team, not the primary team default
