## 1. Schema and repository

- [x] 1.1 Add `TeamStatMetric` table to `docs/schema.sql` and migration in `backend/db.py`
- [x] 1.2 Add repository CRUD: list/create/update/delete/reorder metrics by template; validate action belongs to template
- [x] 1.3 Add single-query match team metric counts using MatchLineup attribution (ignore orphan player events)
- [x] 1.4 On action/category delete: block if used in match events; else cascade-delete dependent metrics

## 2. Template metric constructor UI

- [x] 2.1 Add dedicated page `/directories/templates/<id>/stat-metrics` with create/update/delete and ↑/↓ reorder
- [x] 2.2 Add link from template detail; keep `ShowInReport` UI unchanged

## 3. Match statistics page

- [x] 3.1 Add `GET /matches/<match_id>/statistics` route loading score + home/away metric rows
- [x] 3.2 Create read-only statistics template (score + two team columns; empty state when no metrics)
- [x] 3.3 Add Statistics link on matches list

## 4. Tests and docs

- [x] 4.1 Tests: metric CRUD, reorder, cascade vs block-on-events (isolated DB, `TEST_` data)
- [x] 4.2 Tests: counts with outcome filters, MatchLineup attribution, transfer regression, zeros
- [x] 4.3 Tests: statistics page score, empty-metrics message
- [x] 4.4 Update `docs/development-context.md` with routes and metric constructor notes
