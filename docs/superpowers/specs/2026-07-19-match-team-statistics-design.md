---
comet_change: match-team-statistics
role: technical-design
canonical_spec: openspec
---

# Match Team Statistics — Technical Design

## Overview

Add a read-only per-match team statistics page (score + home/away metric columns) and a template-scoped metric constructor on a dedicated page. Each metric maps a display name to one Action and an outcome filter, producing an integer count. Player events are attributed through `MatchLineup` so transfers cannot rewrite historical match stats.

## Architecture

```
Matches list ──► GET /matches/<id>/statistics
                      │
                      ├─ calculate_match_score_for_match()
                      └─ repo.get_match_team_stat_counts(match_id)
                            │
                            └─ TeamStatMetric × Event × MatchLineup (one query)

Template detail ──► link ──► GET/POST /directories/templates/<id>/stat-metrics
                                      │
                                      └─ TeamStatMetric CRUD + ↑/↓ reorder
```

SQL remains only in `backend/repository.py`. Flask routes in `backend/app.py`. Jinja templates under `templates/matches/` and `templates/templates/`.

## Data model

### Table `TeamStatMetric`

| Column | Type | Notes |
|--------|------|-------|
| Id | INTEGER PK | |
| SportTemplateId | FK → SportTemplate | CASCADE on template delete (template already blocked if used by matches) |
| Name | TEXT NOT NULL | Display label |
| ActionId | FK → Action | ON DELETE CASCADE (app also cascades explicitly on safe action delete) |
| OutcomeFilter | TEXT | `any` \| `Success` \| `Failure` |
| SortOrder | INTEGER NOT NULL DEFAULT 0 | |

Sync: `docs/schema.sql` + migration in `backend/db.py` (auto-backup before DDL).

## Count query (single round-trip)

For a match M with home/away team IDs H, A and metrics of M’s sport template:

1. Attribute each player event to `MatchLineup.TeamId` where `MatchLineup.MatchId = M` and `MatchLineup.PlayerId = Event.PlayerId`.
2. Attribute team-subject events via `Event.TeamId`.
3. Drop player events with no lineup row for M.
4. Apply metric `ActionId` + `OutcomeFilter` (`any` = no outcome predicate).
5. `GROUP BY` metric Id and attributed team Id; return counts for H and A (missing groups → 0 in app layer).

Do **not** use `Player.TeamId` on this page.

## UI

### Constructor page

Route: `/directories/templates/<template_id>/stat-metrics`

- List metrics ordered by SortOrder
- Create form: name, action (template actions only), outcome filter
- Update / delete per row
- ↑ / ↓ swap SortOrder with neighbor
- Template detail: navigation link only (no inline constructor)

### Match statistics page

Route: `GET /matches/<match_id>/statistics`

- Score via existing score helpers / partial patterns
- One comparison table: home value | metric name | away value (same metric order)
- No table headers; team names remain only in the score panel
- Full-width table aligned with the score panel: symmetric home/away value columns under team names and metric names centered under the score
- Always show configured metrics including 0
- If no metrics: score + empty-state message
- No player/comment drill-downs
- Matches list: Statistics link per match

## Delete safety

Primary data = match events.

- Before `delete_action` / `delete_category`: if any related action appears in `Event`, raise user-visible error.
- If unused: delete action/category and cascade-delete `TeamStatMetric` rows for those actions.
- Metrics alone do not block action deletion.

## Testing strategy

- Temp/in-memory SQLite; `TEST_` prefixed entities; never `data/sports_logger.db`
- Metric CRUD + reorder swap
- Cascade delete when action unused; block when events exist
- Outcome filters; MatchLineup attribution; orphan events ignored
- Transfer after tagging does not change match page counts
- Page: score, zeros, empty-metrics message

## Spec / tasks alignment

Canonical requirements live in OpenSpec delta specs under `openspec/changes/match-team-statistics/specs/`. This document deepens implementation; it does not replace those specs.

## Out of scope

- Formula / multi-action metrics
- Per-period tabs
- Changing `/reports` team attribution
- Player drill-down on the match statistics page
