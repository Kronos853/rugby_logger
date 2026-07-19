# match-team-statistics Specification

## Purpose
TBD - created by archiving change match-team-statistics. Update Purpose after archive.
## Requirements
### Requirement: Match Team Statistics Page
The system SHALL provide a read-only match team statistics page showing the match score and per-team metric counts for both home and away teams. Each displayed metric value SHALL equal the sum of all configured conditions for that metric.

#### Scenario: Open statistics from matches list
- **WHEN** the user opens a match’s statistics page from the matches list
- **THEN** the system displays the page without event-editing controls

#### Scenario: Score and two team columns
- **WHEN** the statistics page loads for a match
- **THEN** the match score is displayed
- **AND** each metric appears once in a comparison row: home value, metric name, away value
- **AND** the comparison table has no headers because team names are already shown in the score panel
- **AND** home and away values are centered in symmetric columns below their team names
- **AND** metric names are centered below the score

#### Scenario: Metric value is a count
- **WHEN** a metric is defined for the match’s sport template
- **THEN** each team column shows an integer count for that metric

#### Scenario: Metric value sums all conditions
- **WHEN** a metric contains multiple Action/Outcome/perspective conditions
- **THEN** each team value is the integer sum of the event counts matched by every condition

#### Scenario: Own condition
- **WHEN** a condition uses perspective `own`
- **THEN** the home value counts matching events attributed to the home team
- **AND** the away value counts matching events attributed to the away team

#### Scenario: Opponent condition
- **WHEN** a condition uses perspective `opponent`
- **THEN** the home value counts matching events attributed to the away team
- **AND** the away value counts matching events attributed to the home team

#### Scenario: Scrums won composition
- **WHEN** “Scrums won” contains `Scrum + Success + own` and `Scrum + Failure + opponent`
- **THEN** each team value equals its successful scrums plus the opposing team’s failed scrums

#### Scenario: Overlapping conditions are additive
- **WHEN** one event matches more than one condition in the same metric
- **THEN** it contributes once for every matching condition

#### Scenario: Whole-match scope
- **WHEN** metric counts are computed
- **THEN** they include all periods of the match (no period filter UI)

#### Scenario: Event attribution
- **WHEN** counting a metric condition
- **THEN** player events are attributed via `MatchLineup.TeamId` for that match and player
- **AND** events with `SubjectType='team'` are attributed via `Event.TeamId`
- **AND** player events with no matching `MatchLineup` row for that match are not counted

#### Scenario: Transfers do not change match statistics
- **WHEN** a player’s current `Player.TeamId` changes after the match was tagged
- **THEN** the match team statistics page counts remain based on the match lineup snapshot
- **AND** are unchanged by the transfer

#### Scenario: Outcome filter any
- **WHEN** a condition uses outcome filter `any`
- **THEN** all matching action events are counted regardless of Outcome

#### Scenario: Outcome filter Success or Failure
- **WHEN** a condition uses outcome filter `Success` or `Failure`
- **THEN** only events with that Outcome value are counted

#### Scenario: Zero counts visible
- **WHEN** a configured metric has zero matching events for a team
- **THEN** the metric still appears with value `0`

#### Scenario: No metrics configured
- **WHEN** the match’s sport template has no team-statistic metrics
- **THEN** the page still shows the score
- **AND** shows a message that metrics are not configured

#### Scenario: No player drill-down
- **WHEN** the user views the match team statistics page
- **THEN** the page does not offer player or comment drill-down controls

