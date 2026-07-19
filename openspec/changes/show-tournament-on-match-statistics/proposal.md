## Why

The match statistics page shows the score and team metrics but omits the tournament context already assigned to the match. Showing the tournament name above the score makes the page immediately identifiable.

## What Changes

- Display the match tournament name centered directly above the score on the match statistics page.
- Omit the tournament heading when the match has no tournament.
- Add an isolated page regression test for the tournament heading.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `match-team-statistics`: The statistics page also presents the match tournament above the score when available.

## Impact

- `templates/matches/statistics.html`
- `static/app.css`
- `tests/test_match_statistics_page.py`
- No database, repository, route, or API changes; `repo.get_match()` already returns `TournamentName`.
