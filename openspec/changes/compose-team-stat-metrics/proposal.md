## Why

Team statistic metrics currently count exactly one Action/Outcome condition for the team being calculated. This cannot represent domain metrics such as “Scrums won”, which must add the team’s successful scrums to the opponent’s failed scrums.

## What Changes

- Allow each team statistic metric to contain one or more additive conditions.
- Define every condition by Action, Outcome filter (`any`, `Success`, or `Failure`), and perspective (`own` or `opponent`).
- Evaluate `opponent` relative to the team whose value is being calculated: away for home, home for away.
- Sum every matching condition independently; an event matching multiple conditions contributes once to each matching condition.
- Extend the metric constructor to add, edit, and remove conditions while retaining metric ordering.
- Migrate every existing metric to one equivalent `own` condition without changing its displayed values.
- Keep subtraction, coefficients, nested named metrics, formulas/percentages, period filters, and `/reports` behavior out of scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `match-team-statistics`: Team values are calculated as sums of own/opponent Action/Outcome conditions.
- `sport-templates`: The team-statistic metric constructor manages multiple conditions per metric.

## Impact

- `backend/db.py` and `docs/schema.sql`: introduce normalized metric-condition storage and migrate existing definitions.
- `backend/repository.py`: condition CRUD, validation, delete safety, and composite aggregation.
- `backend/app.py` and `templates/templates/stat_metrics.html`: constructor routes and UI for condition lists.
- `tests/test_team_stat_metrics.py` and page tests: migration, CRUD, own/opponent aggregation, overlap, and regression coverage.
- `docs/development-context.md`: document composite metric semantics.
