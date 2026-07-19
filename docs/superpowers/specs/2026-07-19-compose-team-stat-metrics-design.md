---
comet_change: compose-team-stat-metrics
role: technical-design
canonical_spec: openspec
archived-with: 2026-07-19-compose-team-stat-metrics
status: final
---

# Compose Team Stat Metrics — Technical Design

## Overview

Extend team-statistic metrics so each metric is an ordered sum of one or more Action + Outcome + perspective conditions. Perspective `opponent` attributes matching events to the other match team relative to the column being calculated. Existing single-condition metrics migrate to one equivalent `own` condition without changing displayed values.

## Architecture

```
Template detail ──► /directories/templates/<id>/stat-metrics
                         │
                         ├─ TeamStatMetric (name, sort)
                         └─ TeamStatMetricCondition[] (action, outcome, perspective)

Match statistics ──► get_match_team_stat_counts(match_id)
                         │
                         ├─ attribute events (MatchLineup / Event.TeamId)
                         ├─ join conditions (Action + OutcomeFilter)
                         └─ map own/opponent → target team; SUM counts
```

SQL stays in `backend/repository.py`. Schema changes sync `docs/schema.sql` and `backend/db.py`.

## Data model

### `TeamStatMetric` (parent, rebuilt)

| Column | Notes |
|--------|-------|
| Id | PK |
| SportTemplateId | FK → SportTemplate |
| Name | Display label |
| SortOrder | Metric order on match page / constructor |

Legacy `ActionId` and `OutcomeFilter` are removed after migration.

### `TeamStatMetricCondition` (new child)

| Column | Notes |
|--------|-------|
| Id | PK |
| TeamStatMetricId | FK → TeamStatMetric, ON DELETE CASCADE |
| ActionId | FK → Action, ON DELETE CASCADE |
| OutcomeFilter | `any` \| `Success` \| `Failure` |
| Perspective | `own` \| `opponent` |
| SortOrder | Insertion order in constructor (no ↑/↓ UI) |

Indexes: `(TeamStatMetricId, SortOrder)`, `(ActionId)` for cascade lookups.

### Migration

1. Create `TeamStatMetricCondition`.
2. For each existing `TeamStatMetric`, insert one row: same `ActionId`/`OutcomeFilter`, `Perspective='own'`, `SortOrder=0`.
3. Rebuild `TeamStatMetric` without `ActionId`/`OutcomeFilter` inside a transaction.
4. Rely on existing `ensure_db` → `backup_database_file` for rollback via DB restore.

## Aggregation

One query per match. Keep the current `attributed` CTE (player via `MatchLineup`, team via `Event.TeamId`, orphans dropped, only home/away team IDs).

Join attributed events to conditions:

- `ActionId` match
- `OutcomeFilter = 'any'` OR `Outcome = OutcomeFilter`
- Attributed team ∈ {home, away}

Map to **target** team for the count:

- `own` → `TargetTeamId = AttributedTeamId`
- `opponent` → `TargetTeamId = other of {home, away}`

`GROUP BY MetricId, TargetTeamId` with `COUNT(*)`. Overlapping conditions produce multiple join rows for the same event (additive by design). Missing groups → `0` in the app layer.

Example “Scrums won” for home: home Scrum+Success + away Scrum+Failure.

## Repository API

- `create_team_stat_metric(template_id, name, action_id, outcome_filter, perspective)` — inserts parent + first condition; never leave an empty metric.
- `update_team_stat_metric(metric_id, name)` — name only.
- Condition CRUD: `list` / `create` / `update` / `delete` under a metric, with template-scoped action validation and `VALID_OUTCOME_FILTERS` / `VALID_PERSPECTIVES`.
- `delete_team_stat_condition`: if it was the last condition, also delete the parent metric.
- Metric ↑/↓ unchanged; conditions keep insertion `SortOrder` only.
- Action/Category safe delete: block when events exist; otherwise cascade conditions; delete any metric left with zero conditions.

## Constructor UI

Page: `/directories/templates/<template_id>/stat-metrics`

- Create form: name + first condition (action, outcome, checkbox **«Учитывать события противника»**; unchecked = `own`).
- Each metric row: rename/delete/↑/↓; nested condition list with add/edit/delete.
- No condition reorder controls.
- Match statistics page layout unchanged; only count semantics deepen.

## Risks

- SQLite parent rebuild — transactional migration + pre-DDL backup.
- Additive overlaps may surprise users — conditions listed explicitly in constructor.
- Partial Action cascade — remove orphaned empty metrics after condition cascade.

## Testing strategy

Isolated SQLite (`:memory:` / temp file); `TEST_` entities; never `data/sports_logger.db`.

- Migration: legacy values equal post-migration one-`own`-condition values.
- Condition CRUD; last-condition delete removes metric.
- Own/opponent symmetry; Scrums-won composition; overlap double-count; zeros; orphans; transfer stability.
- Constructor and match-statistics page regressions.

## Spec alignment

Canonical requirements: OpenSpec deltas under `openspec/changes/compose-team-stat-metrics/specs/`. Spec patch: deleting the last condition auto-deletes the parent metric (not reject).

## Out of scope

Subtraction, weights, formulas, nested named metrics, period filters, `/reports` changes, condition ↑/↓.
