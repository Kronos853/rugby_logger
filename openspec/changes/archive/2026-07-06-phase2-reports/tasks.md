## 1. Database Migration

- [x] 1.1 Add migration in `backend/db.py`: `ALTER TABLE Category ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1`
- [x] 1.2 Add migration in `backend/db.py`: `ALTER TABLE Action ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1`
- [x] 1.3 Add migration in `backend/db.py`: `ALTER TABLE SportTemplate ADD COLUMN PeriodCount INTEGER NOT NULL DEFAULT 2`
- [x] 1.4 Update `docs/schema.sql` to reflect the three new columns

## 2. Sport Template Editor — New Fields

- [x] 2.1 Update `repository.py`: `get_template`, `create_category`, `update_category` to include `ShowInReport`
- [x] 2.2 Update `repository.py`: `create_action`, `update_action` to include `ShowInReport`
- [x] 2.3 Update `repository.py`: `get_template` / `update_template` to include `PeriodCount`
- [x] 2.4 Add checkbox "Show in report" to category rows in `templates/template_detail.html`
- [x] 2.5 Add checkbox "Show in report" to action rows in `templates/template_detail.html`
- [x] 2.6 Add "Number of periods" input field to sport template edit form
- [x] 2.7 Add HTMX handlers in `backend/app.py` for toggling `ShowInReport` on category and action (inline, no full page reload)

## 3. Report Repository Queries

- [x] 3.1 Add `get_report_data(subject_type, subject_id, date_from, date_to, by_match=False)` to `repository.py` — returns aggregated rows grouped by `CategoryId`, `ActionId` (and optionally `MatchId`)
- [x] 3.2 Add `get_report_comment_detail(action_id, subject_type, subject_id, date_from, date_to, match_id=None)` to `repository.py` — returns event counts grouped by `Comment`
- [x] 3.3 Ensure both queries filter by `Category.ShowInReport = 1` and `Action.ShowInReport = 1` and exclude zero-count rows

## 4. Reports Page

- [x] 4.1 Add `/reports` route to `backend/app.py` (GET: show form; POST: generate and render report)
- [x] 4.2 Add `/reports/comment-detail` partial route for HTMX drill-down (returns HTML fragment)
- [x] 4.3 Create `templates/reports.html` — report form (type, team/player selector, date range, by-match toggle)
- [x] 4.4 Create `templates/_report_results.html` partial — renders category/action table with metric columns
- [x] 4.5 Create `templates/_report_comment_detail.html` partial — renders comment breakdown sub-table
- [x] 4.6 Add "Reports" link to main navigation in `templates/base.html` (or equivalent nav partial)

## 5. Player Statistics Block

- [x] 5.1 Add `get_player_last5_stats(player_id)` to `repository.py` — last 5 matches from `MatchLineup`, returns same aggregated structure as report query
- [x] 5.2 Update `/directories/teams/<team_id>/players/<player_id>/edit` route in `app.py` to fetch and pass stats data
- [x] 5.3 Add stats block section to `templates/player_edit.html` — category/action table (reuse `_report_results.html` partial or inline equivalent)
- [x] 5.4 ~~Add Chart.js CDN~~ — removed: aggregate chart not informative (deferred)
- [x] 5.5 ~~Success % trend chart~~ — removed (deferred)

## 6. Tagging Control Panel — Navigation

- [x] 6.1 Add main navigation bar to `templates/tagging_control.html`
- [x] 6.2 Adjust viewport height CSS in `static/tagging.css` to account for the nav bar height (e.g., `calc(100vh - nav_height - toolbar_height)`)
- [x] 6.3 Verify fixed-height layout still works (no page scroll, independent column scroll) after nav addition

## 7. Follow-up fixes

- [x] 7.1 Comment drill-down toggle: collapse on second click (`static/reports.js`)
- [x] 7.2 Settings page `/settings` with primary team (`AppSetting` table)
- [x] 7.3 Auto-select primary team in reports form (GET, team report type)
- [x] 7.4 Specs: `application-settings`, reporting collapse + primary team default
