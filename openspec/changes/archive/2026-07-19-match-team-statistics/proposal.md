## Why

Operators can tag match events and run period reports, but there is no read-only per-match team comparison page with a score and a fixed set of team metrics. Existing `ShowInReport` only controls visibility of whole actions (with Success/Failure columns), so it cannot express named metrics such as “Tackles” = Tackle+Success and “Missed tackles” = Tackle+Failure. Operators need a simple metric constructor for that mapping.

## What Changes

- Add a **Statistics** entry on the matches list that opens a read-only match team-statistics page
- Show the match score and **two team columns** (home / away) with the same ordered metric list
- Introduce **template-scoped team-statistic metric definitions**: display name, source action, outcome filter (`any` | `Success` | `Failure`), and sort order; each metric renders as an integer count
- Count events attributed to the team via its players **and** `SubjectType='team'` events for that team, for the **whole match** only
- If no metrics are configured for the match’s sport template, still open the page with the score and an empty-state message
- Always show configured metrics, including zero values
- Keep existing `/reports` and `ShowInReport` behavior unchanged for period reports

**Out of scope (this change):** formula/% metrics, multi-action composition, per-period tabs, player breakdown on this page, editing events from the statistics page

**Kept as one change (not split):** the page and the metric constructor are delivered together; a page without configurable metrics would not meet the product goal.

## Capabilities

### New Capabilities

- `match-team-statistics`: read-only per-match team statistics page, metric definition model, and count aggregation for home/away teams

### Modified Capabilities

- `sport-templates`: CRUD UI on the template detail page for team-statistic metric definitions
- `team-management`: matches list exposes a Statistics navigation option per match

## Impact

- `backend/app.py` — new match statistics route; template metric CRUD routes
- `backend/db.py` / `docs/schema.sql` — new metric-definition table + migration (auto-backup on DDL)
- `backend/repository.py` — metric CRUD + match team metric counts
- `templates/matches/` — list link + new statistics page
- `templates/templates/detail.html` — metric constructor section
- `static/app.css` — layout for two team columns
- `tests/` — isolated DB tests with `TEST_` data only
- Specs: new `match-team-statistics`; deltas for `sport-templates` and `team-management`
