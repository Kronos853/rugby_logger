## Context

`repo.get_match()` already joins `Tournament` and exposes `TournamentName` to the statistics route as part of `match`. The statistics template currently starts with the page title and then includes the shared score partial.

## Goals / Non-Goals

**Goals:**
- Render the available tournament name centered immediately above the score.
- Preserve the page when a match has no tournament.

**Non-Goals:**
- Changing tournament storage, match queries, score calculation, or the shared score partial.
- Showing tournament information on other pages.

## Decisions

- Add a conditional heading in `templates/matches/statistics.html` before the score include. This uses the data already supplied by the route and keeps the shared score partial unchanged.
- Add a page-specific CSS class in `static/app.css` for centered, secondary typography.
- Cover both presence and placement relative to the score with the existing isolated Flask page tests.

## Risks / Trade-offs

- [Tournament names may be long] → Use normal wrapping and centered text rather than forcing a single line.
- [Matches without a tournament could show an empty heading] → Render the heading only when `TournamentName` is truthy.
