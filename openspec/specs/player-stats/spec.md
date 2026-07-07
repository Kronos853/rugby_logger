# player-stats Specification

## Purpose
Player profile statistics aggregated over recent match participation.

## Requirements

### Requirement: Player Statistics Block on Profile Page
The system SHALL display a statistics block on the player profile page showing the player's performance across their last 5 matches.

#### Scenario: Stats block visible on player page
- **WHEN** the user opens a player's profile page
- **THEN** a "Last 5 matches" statistics block is displayed below the player's personal details

#### Scenario: No matches yet
- **WHEN** the player has no matches in their lineup history
- **THEN** the stats block displays a "No match data yet" message instead of an empty table

### Requirement: Player Stats — Last 5 Match Selection
The system SHALL select the 5 most recent matches in which the player appeared in the lineup (`MatchLineup`).

#### Scenario: Correct match selection
- **WHEN** the player has appeared in more than 5 matches
- **THEN** only the 5 most recent matches (by `MatchDate`) are included in the stats block

#### Scenario: Fewer than 5 matches
- **WHEN** the player has appeared in fewer than 5 matches
- **THEN** all available matches are shown

### Requirement: Player Stats — Category and Action Structure
The system SHALL display player stats grouped by category and action, using the same structure as the reports page, respecting `ShowInReport` flags and hiding zero-count rows.

#### Scenario: Category/action grouping
- **WHEN** the stats block is rendered
- **THEN** actions are shown under category headers, only for `ShowInReport = true` categories and actions with at least one event

#### Scenario: Metric format matches report page
- **WHEN** an action has `HasOutcome = false`
- **THEN** only the count is shown in the stats block

#### Scenario: Outcome metrics in stats block
- **WHEN** an action has `HasOutcome = true`
- **THEN** total, success, failure, and success % are shown in the stats block
