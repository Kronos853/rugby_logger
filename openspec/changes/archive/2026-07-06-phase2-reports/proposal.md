## Why

The system currently only exports raw events to CSV for external analysis. Users need built-in statistical reports to evaluate player and team performance directly in the app — without external tools. This is Phase 2 of the roadmap.

## What Changes

- **New `/reports` page** — generates team or individual statistical reports filtered by date range, with optional per-match breakdown
- **`ShowInReport` flag on categories and actions** — controls what appears in reports; defaults to `true`; zero-count actions are hidden from output
- **Report metric logic** — actions without outcome: count only; actions with outcome: total / success / failure / success %
- **Comment drill-down** — any action's stats can be expanded to show breakdown by comment text
- **Player page stats block** — last 5 matches the player participated in, same category/action structure as reports
- **Trend chart on player page** — simple visual chart (e.g. Chart.js) showing success % trend over those 5 matches
- **`PeriodCount` field on SportTemplate** — configures expected number of periods/halves per sport (e.g. Rugby-7 = 2, Hockey = 3)
- **Main navigation on tagging control panel** — consistent nav bar added so users can reach other pages without going back manually

## Capabilities

### New Capabilities

- `reporting`: Dedicated reports page — team/individual, date-range filter, per-match breakdown, category/action grouping, comment drill-down
- `player-stats`: Statistics block on player profile page — last 5 matches, category/action breakdown, success % trend chart

### Modified Capabilities

- `sport-templates`: New `ShowInReport` flag per category and action; new `PeriodCount` field per sport template
- `video-tagging`: Main navigation bar added to tagging control panel page

## Impact

- **DB schema**: `Category.ShowInReport` (BIT, default 1), `Action.ShowInReport` (BIT, default 1), `SportTemplate.PeriodCount` (INT, default 2) — requires migration
- **`backend/db.py`**: New migration adding the three columns; existing rows default to enabled/2
- **`backend/repository.py`**: New query functions for report aggregation (grouped by category/action, with outcome split, optionally per match)
- **`backend/app.py`**: New `/reports` route; updated `/directories/teams/<team_id>/players/<player_id>/edit` route to include stats; updated template detail routes to expose new flags
- **Templates**: New `reports.html`; updated `player_edit.html`, `template_detail.html`, `tagging_control.html`
- **Static**: Chart.js added (CDN) for player stats trend chart
- **No breaking changes** to existing event logging, CSV export, or match setup flows
