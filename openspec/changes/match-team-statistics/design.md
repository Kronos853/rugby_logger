## Context

Flask + Jinja + HTMX app with SQLite. Match list lives at `/matches`; tagging and period reports already exist. Period reports use `ShowInReport` and `HasOutcome` for action columns — that model cannot express named outcome-filtered metrics. `MatchLineup` stores a per-match team/player snapshot suitable for transfer-stable attribution.

Constraints: SQL only in `repository.py`; sync `docs/schema.sql` with `backend/db.py` migrations; auto-backup before DDL; never test against `data/sports_logger.db`.

## Goals / Non-Goals

**Goals:**
- Read-only match statistics page with score + comparison rows (home value | metric | away value)
- Template-scoped metric definitions on a dedicated constructor page
- Transfer-stable counts via MatchLineup attribution
- Empty-metric and zero-value behaviors as agreed

**Non-Goals:**
- Formula / percentage metrics, multi-action composition
- Per-period tabs, player drill-down on this page
- Changing `/reports` semantics or `ShowInReport`
- Editing events from the statistics page

## Decisions

### 1. Table `TeamStatMetric`
Template-scoped: Name, ActionId, OutcomeFilter (`any`|`Success`|`Failure`), SortOrder.

### 2. Separate constructor page
`/directories/templates/<id>/stat-metrics` with ↑/↓ reorder; template detail only links there.

### 3. Single aggregating count query
One repository query per match returns all metric×team counts.

### 4. MatchLineup attribution
Player events → `MatchLineup.TeamId` for that match; team events → `Event.TeamId`; no lineup row → ignore. Transfers must not change match page stats.

### 5. Delete safety
Block Action/Category delete when used in match events; otherwise cascade-delete dependent metrics.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Orphan CSV-imported player events | Ignored on this page (accepted) |
| Complex count SQL | Covered by focused repository tests |
| `/reports` still uses Player.TeamId | Explicitly out of scope |

## Migration Plan

1. Add `TeamStatMetric` migration + schema sync
2. Constructor page + match statistics page + list link
3. Tests + docs
4. Rollback via backup restore if needed

## Open Questions

None — resolved in design brainstorming.
