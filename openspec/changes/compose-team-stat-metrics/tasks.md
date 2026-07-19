## 1. Data model and migration

- [x] 1.1 Add `TeamStatMetricCondition` to `docs/schema.sql` and `backend/db.py`, and rebuild `TeamStatMetric` without legacy condition columns
- [x] 1.2 Migrate each existing metric to one equivalent `own` condition and add isolated migration regression tests

## 2. Repository behavior

- [x] 2.1 Refactor metric CRUD and add condition list/create/update/delete APIs with template/action validation
- [x] 2.2 Preserve metric ordering and deterministic condition insertion order, including auto-delete of a metric when its last condition is removed
- [x] 2.3 Replace match aggregation with one composite own/opponent query and test sums, overlap, zeros, orphans, and transfer stability
- [x] 2.4 Update Action/Category delete safety to cascade affected conditions, preserve non-empty metrics, and remove empty metrics

## 3. Metric constructor

- [x] 3.1 Update constructor routes to create a metric with its first condition and manage condition CRUD
- [x] 3.2 Update the constructor template to display grouped conditions and choose Action, Outcome, and opponent via the “Учитывать события противника” checkbox

## 4. Verification and documentation

- [x] 4.1 Add page tests for multi-condition constructor controls and preserve match-statistics rendering regressions
- [x] 4.2 Run the full isolated test suite and update `docs/development-context.md` with composite metric semantics
