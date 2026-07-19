## Context

`TeamStatMetric` currently stores one `ActionId` and one `OutcomeFilter`; the match query joins each event directly to that row. The constructor edits those fields inline. The requested “Scrums won” behavior needs a metric to own multiple independent count conditions and needs each condition to choose whether events come from the team being calculated or its opponent.

Constraints:
- SQLite schema and migrations must remain synchronized with `docs/schema.sql`.
- SQL remains in `backend/repository.py`.
- Existing metric definitions and displayed counts must survive migration.
- MatchLineup remains the source of historical player-event team attribution.
- Match statistics must still be aggregated in one repository query per match.

## Goals / Non-Goals

**Goals:**
- Represent one metric as an ordered list of additive conditions.
- Give each condition an Action, Outcome filter, and `own`/`opponent` perspective.
- Calculate home and away values symmetrically from the same definitions.
- Preserve existing metrics as one-condition `own` metrics.
- Extend constructor CRUD and delete safety for normalized conditions.

**Non-Goals:**
- Subtraction, weights, formulas, percentages, or arbitrary expressions.
- References to other named metrics or nested composition.
- Deduplicating an event across overlapping conditions.
- Changing period reports, `ShowInReport`, or match-statistics layout.

## Decisions

### 1. Normalize conditions into `TeamStatMetricCondition`

`TeamStatMetric` retains identity, template, display name, and metric order. A child table stores:

- `TeamStatMetricId` — parent FK with cascade delete
- `ActionId` — source Action FK with cascade delete
- `OutcomeFilter` — `any | Success | Failure`
- `Perspective` — `own | opponent`
- `SortOrder` — deterministic constructor display order

This is preferred over JSON because SQLite can validate foreign keys, action deletion remains safe, and the aggregation query can join conditions directly. It is preferred over numbered columns because condition count is unbounded.

### 2. Migrate legacy columns into one child condition

The migration creates the child table, inserts one `own` condition for every existing metric using its current `ActionId`/`OutcomeFilter`, then rebuilds `TeamStatMetric` without those two columns. The application backup-before-DDL behavior provides rollback through database restore.

### 3. Relative opponent semantics

For a home value, an `opponent` condition counts attributed away events; for an away value it counts attributed home events. The repository query maps every matched attributed event to a target team:

- `own` → target team is the event’s attributed team
- `opponent` → target team is the other match team

This avoids fixed Home/Away semantics and lets one template work for both columns.

### 4. Additive join semantics

Each matching condition contributes its own count. If one event matches two overlapping conditions, the condition join yields two rows and the event contributes twice. Exact duplicate conditions are therefore allowed and intentionally additive.

The query continues to:
- attribute player events through `MatchLineup`
- use `Event.TeamId` for team events
- ignore orphan player events
- restrict attributed teams to the match’s home/away teams
- return zero for metric/team groups with no matches

### 5. Constructor edits metric and condition list separately

Creating a metric includes its first condition so persisted metrics are never intentionally empty. Existing metric rows edit the name and expose child condition controls for add/update/delete. Deleting the last condition through the constructor also deletes the parent metric.

Perspective is chosen with a checkbox labeled “Учитывать события противника”; unchecked stores `own`, checked stores `opponent`. Conditions keep insertion order; no condition ↑/↓ controls.

When an unused Action is deleted, only conditions referencing it cascade. Metrics retaining other conditions remain. Any metric left empty by an Action/Category cascade is removed to preserve the existing single-condition delete behavior.

## Risks / Trade-offs

- **SQLite table rebuild can lose data if interrupted** → existing pre-migration backup and transaction-based migration.
- **Overlapping conditions can surprise users with double counts** → constructor displays every condition explicitly; specs define additive behavior.
- **Opponent mapping could count unrelated teams** → query restricts attributed events to home/away before perspective mapping.
- **More constructor controls increase UI density** → keep the current dedicated page and group conditions beneath each metric.
- **Action deletion can partially change a composite metric** → cascade only the affected conditions and remove a metric only when no conditions remain.

## Migration Plan

1. Create `TeamStatMetricCondition` and indexes.
2. Copy every legacy metric’s Action/Outcome into one `own` condition.
3. Rebuild `TeamStatMetric` without legacy condition columns.
4. Update repository and constructor code to read only normalized conditions.
5. Verify migrated metrics produce the same values as before.
6. Roll back by restoring the automatic pre-migration database backup if needed.

## Open Questions

None. Composition source, operations, overlap semantics, and opponent relativity were confirmed during clarification.
