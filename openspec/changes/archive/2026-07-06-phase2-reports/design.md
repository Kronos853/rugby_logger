## Context

The app collects match events in SQLite via `backend/repository.py`. Each `Event` row stores `PlayerId` or `TeamId`, `ActionId`, `Outcome` (Success/Failure/NULL), and an optional `Comment`. The `Action` table has a `HasOutcome` flag. There is no reporting layer yet — users export CSV and analyze externally. The stack is Flask + Jinja + HTMX with no JavaScript framework.

## Goals / Non-Goals

**Goals:**
- Dedicated `/reports` page with team and individual modes, date-range filter, optional per-match breakdown
- Category/action grouping; correct metric display based on `HasOutcome`
- Comment drill-down for any action (toggled via HTMX)
- `ShowInReport` flag on `Category` and `Action` to exclude noise actions from reports
- `PeriodCount` on `SportTemplate` to support multi-period sports (Hockey = 3, Rugby = 2)
- Player profile stats block: last 5 matches + success % trend chart (Chart.js CDN)
- Main nav bar on the tagging control panel

**Non-Goals:**
- AI analysis (separate phase)
- PDF/Excel export of reports
- Custom date grouping (weekly, monthly aggregations)
- Real-time report updates during live tagging

## Decisions

### Decision 1: Report aggregation in SQL, not Python

All report math (COUNT, SUM CASE WHEN outcome=Success) runs in a single SQL query in `repository.py`, grouped by `CategoryId`, `ActionId`. Python receives flat rows and assembles the display structure in `app.py`.

**Alternative**: Fetch raw events and aggregate in Python. Rejected — slower for large match sets and the SQL approach is already the project pattern.

### Decision 2: Per-match breakdown as a separate query path

When the user enables "by match" view, the repository runs the same aggregation query but adds `MatchId` to the GROUP BY. The Jinja template renders a repeating section per match. No separate endpoint needed — same `/reports` route, different query branch.

**Alternative**: Client-side pivot with JavaScript. Rejected — keep server-side rendering consistent with the rest of the app.

### Decision 3: Comment drill-down via HTMX partial

The comment breakdown is loaded on demand when the user clicks a toggle on an action row. A dedicated partial route (`/reports/comment-detail`) returns an HTML fragment. This avoids loading all comment data upfront when most rows won't be expanded.

### Decision 4: `ShowInReport` defaults to `true`

Migration sets `ShowInReport = 1` for all existing rows. Users then uncheck noisy/technical actions in the template editor. Zero-count actions are always hidden from rendered reports regardless of the flag.

### Decision 5: Chart.js via CDN for player stats trend

Chart.js is loaded from CDN only on the player profile page. A simple bar/line chart shows success % across the last 5 matches per action (or the most relevant category). No server-side chart generation.

**Alternative**: CSS-only progress bars. Accepted as a fallback if Chart.js introduces issues, but Chart.js is preferred for meaningful trend visualization.

### Decision 6: `PeriodCount` on `SportTemplate`, not on `Match`

The number of periods is a sport-level configuration (Rugby = 2, Hockey = 3), not per-match. Matches inherit it from their template. Match setup UI can display the correct period labels.

### Decision 7: Navigation bar on tagging control panel

The tagging page uses a fixed-height viewport layout (no page scroll). A compact top nav bar is added — same `<nav>` partial used across other pages — but pinned above the existing toolbar row. The viewport layout is adjusted to account for the added height.

## Risks / Trade-offs

- **Large event datasets**: Aggregation queries across many matches may be slow with no index on `Event.ActionId` + `Event.Outcome`. → Mitigation: The schema already has `IX_Event_ActionId`. Add a composite index on `(MatchId, ActionId, Outcome)` in the migration if needed.
- **Chart.js CDN availability**: Offline-first users may not load the chart. → Mitigation: Degrade gracefully — table always renders; chart is additive. Consider bundling locally in a later pass.
- **`PeriodCount` mismatch**: Existing Rugby-7 matches were always 2 periods; defaulting to 2 is safe. Other sports added in future must set their own count. → No risk for current data.
- **Tagging page layout shift**: Adding a nav bar to the fixed-height tagging layout may clip the input area on smaller screens. → Mitigation: Make nav collapsible or use a slim nav height consistent with the existing toolbar row.

## Migration Plan

1. Auto-backup triggers in `ensure_db()` before any DDL (already implemented)
2. New migration in `backend/db.py`:
   - `ALTER TABLE Category ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1`
   - `ALTER TABLE Action ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1`
   - `ALTER TABLE SportTemplate ADD COLUMN PeriodCount INTEGER NOT NULL DEFAULT 2`
3. Update `docs/schema.sql` to reflect new columns
4. No data rollback needed — columns are additive with safe defaults

## Open Questions

- Should `PeriodCount` affect the period selector in the tagging UI (e.g., show 1/2/3 buttons dynamically), or is that a separate task for a future change?
- Should the trend chart on the player page show all `ShowInReport` actions, or only the most-used ones to keep the chart readable?
