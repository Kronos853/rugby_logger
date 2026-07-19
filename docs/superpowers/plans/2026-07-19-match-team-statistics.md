---
change: match-team-statistics
design-doc: docs/superpowers/specs/2026-07-19-match-team-statistics-design.md
base-ref: b992abed979657cd0e95a070f312532e1adf55bf
---

# Match Team Statistics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a read-only per-match team statistics page (score + home/away metric columns) and a template-scoped metric constructor on a dedicated page, with transfer-stable counts via `MatchLineup` attribution.

**Architecture:** Add a `TeamStatMetric` table scoped to `SportTemplate`. Repository functions in `backend/repository.py` handle metric CRUD, reorder, a single aggregating count query per match, and delete safety. Flask routes in `backend/app.py` serve `/directories/templates/<id>/stat-metrics` (constructor) and `GET /matches/<id>/statistics` (read-only page). Jinja templates under `templates/templates/` and `templates/matches/`; score reuses `calculate_match_score_for_match` and the existing `_score.html` partial pattern.

**Tech Stack:** Python 3, Flask, Jinja2, HTMX (existing), SQLite file DB (`backend/db.py`), unittest + Flask `test_client`, isolated temp DB via `SPORTS_LOGGER_DB` env var.

## Global Constraints

- SQL only in `backend/repository.py` — no raw SQL in routes, templates, or tests beyond `connect()` + repo calls.
- Schema sync: every DDL change in both `docs/schema.sql` and `backend/db.py` (`SCHEMA_SQL` + `_pending_migrations` / `_apply_migrations`); auto-backup runs before migrate via `ensure_db`.
- Tests use isolated SQLite (`tempfile` or `:memory:`); entities prefixed `TEST_`; never read or write `data/sports_logger.db`.
- Do not modify existing user records in production DB during manual checks.
- Constructor lives at `/directories/templates/<template_id>/stat-metrics` with ↑/↓ reorder; template detail only links there (no inline constructor).
- Match statistics at `GET /matches/<match_id>/statistics`; counts via one repository query; player events attributed through `MatchLineup.TeamId`; team events via `Event.TeamId`; orphan player events ignored; do not use `Player.TeamId` on this page.
- Block `delete_action` / `delete_category` when any related action appears in `Event`; otherwise cascade-delete dependent `TeamStatMetric` rows.
- Keep `/reports` and `ShowInReport` behavior unchanged.
- Outcome filter values: `any` | `Success` | `Failure`.

## File Structure

| File | Responsibility |
|------|----------------|
| `docs/schema.sql` | Logical `TeamStatMetric` table definition + index |
| `backend/db.py` | `SCHEMA_SQL` table + `_migrate_team_stat_metrics` |
| `backend/repository.py` | Metric CRUD, reorder, count query, delete safety helpers |
| `backend/app.py` | Constructor routes (GET/POST), statistics GET route, flash on delete block |
| `templates/templates/stat_metrics.html` | Dedicated metric constructor page (list, create, update, delete, ↑/↓) |
| `templates/templates/detail.html` | Navigation link to stat-metrics page only |
| `templates/matches/statistics.html` | Read-only score + two team columns + empty state |
| `templates/matches/index.html` | Statistics link per match row |
| `static/app.css` | `.match-statistics` two-column layout |
| `tests/test_team_stat_metrics.py` | Repository tests: schema, CRUD, reorder, delete safety, counts |
| `tests/test_match_statistics_page.py` | Flask page tests: link, score, zeros, empty metrics |
| `docs/development-context.md` | New routes and constructor notes |

---

### Task 1: TeamStatMetric schema and migration

**Files:**
- Modify: `docs/schema.sql` (after `CommentTemplate`, before `Tournament`)
- Modify: `backend/db.py` — `SCHEMA_SQL`, `_pending_migrations`, `_apply_migrations`, new `_migrate_team_stat_metrics`
- Test: `tests/test_team_stat_metrics.py`

**Interfaces:**
- Produces: SQLite table `TeamStatMetric(Id, SportTemplateId, Name, ActionId, OutcomeFilter, SortOrder)` with FK `SportTemplateId → SportTemplate ON DELETE CASCADE`, `ActionId → Action ON DELETE CASCADE`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_team_stat_metrics.py
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend.db import connect, ensure_db


class TeamStatMetricSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_team_stat_metric_table_exists_after_ensure_db(self) -> None:
        ensure_db(self.db_path)
        conn = connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='TeamStatMetric'"
            ).fetchone()
            self.assertIsNotNone(row)
            columns = {r[1] for r in conn.execute("PRAGMA table_info(TeamStatMetric)")}
            self.assertEqual(
                columns,
                {"Id", "SportTemplateId", "Name", "ActionId", "OutcomeFilter", "SortOrder"},
            )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricSchemaTests.test_team_stat_metric_table_exists_after_ensure_db -v`

Expected: FAIL — table `TeamStatMetric` not found.

- [ ] **Step 3: Write minimal implementation**

Add to `docs/schema.sql` (after `CommentTemplate` block):

```sql
CREATE TABLE TeamStatMetric (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SportTemplateId INT             NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
    Name            NVARCHAR(100)   NOT NULL,
    ActionId        INT             NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
    OutcomeFilter   VARCHAR(10)     NOT NULL DEFAULT 'any'
                    CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
    SortOrder       INT             NOT NULL DEFAULT 0
);

CREATE INDEX IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId);
CREATE INDEX IX_TeamStatMetric_ActionId ON TeamStatMetric(ActionId);
```

Add to `backend/db.py` `SCHEMA_SQL` (after `CommentTemplate`, before `Team`):

```python
CREATE TABLE IF NOT EXISTS TeamStatMetric (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
  OutcomeFilter TEXT NOT NULL DEFAULT 'any' CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
  SortOrder INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId);
CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_ActionId ON TeamStatMetric(ActionId);
```

Update `_pending_migrations`:

```python
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "TeamStatMetric" not in tables:
        return True
    # ... keep existing checks ...
```

Add migration function and call it from `_apply_migrations`:

```python
def _migrate_team_stat_metrics(conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "TeamStatMetric" in tables:
        return
    conn.execute(
        """
        CREATE TABLE TeamStatMetric (
          Id INTEGER PRIMARY KEY AUTOINCREMENT,
          SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
          Name TEXT NOT NULL,
          ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
          OutcomeFilter TEXT NOT NULL DEFAULT 'any' CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
          SortOrder INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_ActionId ON TeamStatMetric(ActionId)"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricSchemaTests.test_team_stat_metric_table_exists_after_ensure_db -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/schema.sql backend/db.py tests/test_team_stat_metrics.py
git commit -m "feat: add TeamStatMetric table and migration"
```

---

### Task 2: Repository — metric CRUD and template action validation

**Files:**
- Modify: `backend/repository.py`
- Test: `tests/test_team_stat_metrics.py`

**Interfaces:**
- Consumes: `TeamStatMetric` table (Task 1)
- Produces:
  - `list_team_stat_metrics(conn, template_id: int) -> list[sqlite3.Row]`
  - `create_team_stat_metric(conn, template_id: int, name: str, action_id: int, outcome_filter: str) -> int`
  - `update_team_stat_metric(conn, metric_id: int, name: str, action_id: int, outcome_filter: str) -> None`
  - `delete_team_stat_metric(conn, metric_id: int) -> None`
  - `action_belongs_to_template(conn, template_id: int, action_id: int) -> bool`
  - `get_team_stat_metric(conn, metric_id: int) -> sqlite3.Row | None`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_team_stat_metrics.py`:

```python
from backend import repository as repo
from backend.seed import ensure_seeded


class TeamStatMetricCrudTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        ensure_db(self.db_path)
        conn = connect(self.db_path)
        try:
            ensure_seeded(conn)
            template = repo.get_sport_template_by_name(conn, "Регби-7")
            assert template is not None
            self.template_id = int(template["Id"])
            categories = repo.list_categories_by_template(conn, self.template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            actions = repo.list_actions_by_category(conn, int(handling["Id"]))
            self.action_id = int(actions[0]["Id"])
        finally:
            conn.close()

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_create_and_list_metrics_ordered_by_sort_order(self) -> None:
        conn = connect(self.db_path)
        try:
            first_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Passes", self.action_id, "Success"
            )
            second_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_All passes", self.action_id, "any"
            )
            rows = repo.list_team_stat_metrics(conn, self.template_id)
            self.assertEqual([int(r["Id"]) for r in rows], [first_id, second_id])
            self.assertEqual(rows[0]["Name"], "TEST_Passes")
            self.assertEqual(rows[0]["OutcomeFilter"], "Success")
        finally:
            conn.close()

    def test_create_rejects_action_from_other_template(self) -> None:
        conn = connect(self.db_path)
        try:
            other_template_id = repo.create_sport_template(conn, "TEST_OtherSport")
            other_cat_id = repo.create_category(conn, other_template_id, "TEST_Cat", 0)
            other_action_id = repo.create_action(conn, other_cat_id, "TEST_Action", True, 0, "handling")
            with self.assertRaises(ValueError):
                repo.create_team_stat_metric(
                    conn, self.template_id, "TEST_Bad", other_action_id, "any"
                )
        finally:
            conn.close()

    def test_update_and_delete_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Old", self.action_id, "any"
            )
            repo.update_team_stat_metric(
                conn, metric_id, "TEST_New", self.action_id, "Failure"
            )
            row = repo.get_team_stat_metric(conn, metric_id)
            assert row is not None
            self.assertEqual(row["Name"], "TEST_New")
            self.assertEqual(row["OutcomeFilter"], "Failure")
            repo.delete_team_stat_metric(conn, metric_id)
            self.assertIsNone(repo.get_team_stat_metric(conn, metric_id))
        finally:
            conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests -v`

Expected: FAIL — `AttributeError: module 'backend.repository' has no attribute 'create_team_stat_metric'`

- [ ] **Step 3: Write minimal implementation**

Add to `backend/repository.py`:

```python
VALID_OUTCOME_FILTERS = frozenset({"any", "Success", "Failure"})


def action_belongs_to_template(conn: sqlite3.Connection, template_id: int, action_id: int) -> bool:
    row = _row(
        conn,
        """
        SELECT 1
        FROM Action a
        INNER JOIN Category c ON c.Id = a.CategoryId
        WHERE a.Id = ? AND c.SportTemplateId = ?
        """,
        (action_id, template_id),
    )
    return row is not None


def list_team_stat_metrics(conn: sqlite3.Connection, template_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn,
        "SELECT * FROM TeamStatMetric WHERE SportTemplateId = ? ORDER BY SortOrder, Id",
        (template_id,),
    )


def get_team_stat_metric(conn: sqlite3.Connection, metric_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM TeamStatMetric WHERE Id = ?", (metric_id,))


def create_team_stat_metric(
    conn: sqlite3.Connection,
    template_id: int,
    name: str,
    action_id: int,
    outcome_filter: str,
) -> int:
    if outcome_filter not in VALID_OUTCOME_FILTERS:
        raise ValueError("Недопустимый фильтр исхода.")
    if not action_belongs_to_template(conn, template_id, action_id):
        raise ValueError("Действие не принадлежит этому шаблону.")
    sort_order = len(list_team_stat_metrics(conn, template_id))
    return _insert(
        conn,
        """INSERT INTO TeamStatMetric (SportTemplateId, Name, ActionId, OutcomeFilter, SortOrder)
           VALUES (?, ?, ?, ?, ?)""",
        (template_id, name.strip(), action_id, outcome_filter, sort_order),
    )


def update_team_stat_metric(
    conn: sqlite3.Connection,
    metric_id: int,
    name: str,
    action_id: int,
    outcome_filter: str,
) -> None:
    metric = get_team_stat_metric(conn, metric_id)
    if not metric:
        raise ValueError("Метрика не найдена.")
    if outcome_filter not in VALID_OUTCOME_FILTERS:
        raise ValueError("Недопустимый фильтр исхода.")
    template_id = int(metric["SportTemplateId"])
    if not action_belongs_to_template(conn, template_id, action_id):
        raise ValueError("Действие не принадлежит этому шаблону.")
    _run(
        conn,
        """UPDATE TeamStatMetric SET Name = ?, ActionId = ?, OutcomeFilter = ? WHERE Id = ?""",
        (name.strip(), action_id, outcome_filter, metric_id),
    )


def delete_team_stat_metric(conn: sqlite3.Connection, metric_id: int) -> None:
    _run(conn, "DELETE FROM TeamStatMetric WHERE Id = ?", (metric_id,))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: add TeamStatMetric repository CRUD"
```

---

### Task 3: Repository — reorder metrics (↑/↓ swap)

**Files:**
- Modify: `backend/repository.py`
- Test: `tests/test_team_stat_metrics.py`

**Interfaces:**
- Consumes: `list_team_stat_metrics`, `get_team_stat_metric` (Task 2)
- Produces: `swap_team_stat_metric_order(conn, template_id: int, metric_id: int, direction: str) -> None` where `direction` is `'up'` or `'down'`

- [ ] **Step 1: Write the failing test**

```python
    def test_swap_metric_order_up_and_down(self) -> None:
        conn = connect(self.db_path)
        try:
            first_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_First", self.action_id, "any"
            )
            second_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Second", self.action_id, "any"
            )
            repo.swap_team_stat_metric_order(conn, self.template_id, second_id, "up")
            rows = repo.list_team_stat_metrics(conn, self.template_id)
            self.assertEqual([int(r["Id"]) for r in rows], [second_id, first_id])
            repo.swap_team_stat_metric_order(conn, self.template_id, second_id, "down")
            rows = repo.list_team_stat_metrics(conn, self.template_id)
            self.assertEqual([int(r["Id"]) for r in rows], [first_id, second_id])
        finally:
            conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests.test_swap_metric_order_up_and_down -v`

Expected: FAIL — `swap_team_stat_metric_order` not defined

- [ ] **Step 3: Write minimal implementation**

```python
def swap_team_stat_metric_order(
    conn: sqlite3.Connection,
    template_id: int,
    metric_id: int,
    direction: str,
) -> None:
    metrics = list_team_stat_metrics(conn, template_id)
    ids = [int(m["Id"]) for m in metrics]
    if metric_id not in ids:
        raise ValueError("Метрика не найдена.")
    idx = ids.index(metric_id)
    if direction == "up":
        if idx == 0:
            return
        neighbor_idx = idx - 1
    elif direction == "down":
        if idx == len(ids) - 1:
            return
        neighbor_idx = idx + 1
    else:
        raise ValueError("Недопустимое направление.")
    current = metrics[idx]
    neighbor = metrics[neighbor_idx]
    _run(
        conn,
        "UPDATE TeamStatMetric SET SortOrder = ? WHERE Id = ?",
        (int(neighbor["SortOrder"]), int(current["Id"])),
    )
    _run(
        conn,
        "UPDATE TeamStatMetric SET SortOrder = ? WHERE Id = ?",
        (int(current["SortOrder"]), int(neighbor["Id"])),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests.test_swap_metric_order_up_and_down -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: swap TeamStatMetric sort order"
```

---

### Task 4: Repository — single-query match team stat counts

**Files:**
- Modify: `backend/repository.py`
- Test: `tests/test_team_stat_metrics.py`

**Interfaces:**
- Consumes: metric CRUD (Task 2), `add_match_lineup_row`, `create_event`, `get_match` (existing)
- Produces: `get_match_team_stat_counts(conn, match_id: int) -> list[dict[str, Any]]` returning ordered rows:
  `{"metric_id": int, "name": str, "sort_order": int, "home_count": int, "away_count": int}`

- [ ] **Step 1: Write the failing tests**

Add helper and tests to `tests/test_team_stat_metrics.py`:

```python
class TeamStatMetricCountTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        ensure_db(self.db_path)
        conn = connect(self.db_path)
        try:
            ensure_seeded(conn)
            template = repo.get_sport_template_by_name(conn, "Регби-7")
            assert template is not None
            self.template_id = int(template["Id"])
            self.home_id = repo.create_team(conn, "TEST_Home")
            self.away_id = repo.create_team(conn, "TEST_Away")
            self.player_home = repo.create_player(conn, self.home_id, "TEST_HomePlayer", None)
            self.player_away = repo.create_player(conn, self.away_id, "TEST_AwayPlayer", None)
            self.match_id = repo.create_match(
                conn, self.template_id, self.home_id, self.away_id, "2026-01-15", None, None, None
            )
            repo.add_match_lineup_row(
                conn, self.match_id, self.home_id, self.player_home, None, "starter", 0
            )
            repo.add_match_lineup_row(
                conn, self.match_id, self.away_id, self.player_away, None, "starter", 0
            )
            categories = repo.list_categories_by_template(conn, self.template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            self.action_id = int(
                repo.list_actions_by_category(conn, int(handling["Id"]))[0]["Id"]
            )
            self.metric_success_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Pass OK", self.action_id, "Success"
            )
            self.metric_any_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_All passes", self.action_id, "any"
            )
        finally:
            conn.close()

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_outcome_filters_and_zeros(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Failure",
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "team",
                team_id=self.away_id, action_id=self.action_id, outcome="Success",
            )
            rows = repo.get_match_team_stat_counts(conn, self.match_id)
            by_id = {r["metric_id"]: r for r in rows}
            self.assertEqual(by_id[self.metric_success_id]["home_count"], 1)
            self.assertEqual(by_id[self.metric_success_id]["away_count"], 1)
            self.assertEqual(by_id[self.metric_any_id]["home_count"], 2)
            self.assertEqual(by_id[self.metric_any_id]["away_count"], 1)
        finally:
            conn.close()

    def test_orphan_player_event_ignored(self) -> None:
        conn = connect(self.db_path)
        try:
            orphan_id = repo.create_player(conn, self.home_id, "TEST_Orphan", None)
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=orphan_id, action_id=self.action_id, outcome="Success",
            )
            rows = repo.get_match_team_stat_counts(conn, self.match_id)
            self.assertTrue(all(r["home_count"] == 0 and r["away_count"] == 0 for r in rows))
        finally:
            conn.close()

    def test_transfer_does_not_change_counts(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            before = repo.get_match_team_stat_counts(conn, self.match_id)
            repo.update_player(conn, self.player_home, self.away_id, "TEST_HomePlayer", None)
            after = repo.get_match_team_stat_counts(conn, self.match_id)
            self.assertEqual(before, after)
        finally:
            conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCountTests -v`

Expected: FAIL — `get_match_team_stat_counts` not defined

- [ ] **Step 3: Write minimal implementation**

```python
def get_match_team_stat_counts(conn: sqlite3.Connection, match_id: int) -> list[dict[str, Any]]:
    match = get_match(conn, match_id)
    if not match:
        return []
    template_id = int(match["SportTemplateId"])
    home_team_id = int(match["HomeTeamId"])
    away_team_id = int(match["AwayTeamId"])
    metrics = list_team_stat_metrics(conn, template_id)
    if not metrics:
        return []

    count_rows = _rows(
        conn,
        """
        WITH attributed AS (
          SELECT
            e.ActionId,
            e.Outcome,
            CASE
              WHEN e.SubjectType = 'team' THEN e.TeamId
              ELSE ml.TeamId
            END AS TeamId
          FROM Event e
          LEFT JOIN MatchLineup ml
            ON ml.MatchId = e.MatchId AND ml.PlayerId = e.PlayerId
          WHERE e.MatchId = ?
        )
        SELECT
          tsm.Id AS MetricId,
          a.TeamId,
          COUNT(*) AS Cnt
        FROM TeamStatMetric tsm
        INNER JOIN attributed a ON a.ActionId = tsm.ActionId
          AND a.TeamId IS NOT NULL
          AND (
            tsm.OutcomeFilter = 'any'
            OR a.Outcome = tsm.OutcomeFilter
          )
        WHERE tsm.SportTemplateId = ?
          AND a.TeamId IN (?, ?)
        GROUP BY tsm.Id, a.TeamId
        """,
        (match_id, template_id, home_team_id, away_team_id),
    )

    counts: dict[tuple[int, int], int] = {}
    for row in count_rows:
        counts[(int(row["MetricId"]), int(row["TeamId"]))] = int(row["Cnt"])

    result: list[dict[str, Any]] = []
    for metric in metrics:
        metric_id = int(metric["Id"])
        result.append(
            {
                "metric_id": metric_id,
                "name": str(metric["Name"]),
                "sort_order": int(metric["SortOrder"]),
                "home_count": counts.get((metric_id, home_team_id), 0),
                "away_count": counts.get((metric_id, away_team_id), 0),
            }
        )
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCountTests -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: aggregate match team stat counts via MatchLineup"
```

---

### Task 5: Repository — delete safety (block vs cascade metrics)

**Files:**
- Modify: `backend/repository.py` — replace `delete_action`, `delete_category` bodies; add helpers
- Test: `tests/test_team_stat_metrics.py`

**Interfaces:**
- Consumes: `create_team_stat_metric`, `create_event` (Tasks 2, 4)
- Produces:
  - `count_events_by_action(conn, action_id: int) -> int`
  - `delete_team_stat_metrics_by_action(conn, action_id: int) -> None`
  - `delete_team_stat_metrics_by_category(conn, category_id: int) -> None`
  - Modified `delete_action` / `delete_category` raise `ValueError("Действие используется в событиях матчей.")` or category equivalent when blocked

- [ ] **Step 1: Write the failing tests**

```python
class TeamStatMetricDeleteSafetyTests(unittest.TestCase):
    # reuse setUp pattern from TeamStatMetricCountTests (copy minimal seed)

    def test_cascade_metrics_when_action_unused(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_M", self.action_id, "any"
            )
            repo.delete_action(conn, self.action_id)
            self.assertIsNone(repo.get_team_stat_metric(conn, metric_id))
        finally:
            conn.close()

    def test_block_action_delete_when_used_in_events(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.create_team_stat_metric(conn, self.template_id, "TEST_M", self.action_id, "any")
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            with self.assertRaises(ValueError):
                repo.delete_action(conn, self.action_id)
            self.assertIsNotNone(repo.get_action(conn, self.action_id))
        finally:
            conn.close()

    def test_block_category_delete_when_action_used_in_events(self) -> None:
        conn = connect(self.db_path)
        try:
            action = repo.get_action(conn, self.action_id)
            assert action is not None
            category_id = int(action["CategoryId"])
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            with self.assertRaises(ValueError):
                repo.delete_category(conn, category_id)
        finally:
            conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricDeleteSafetyTests -v`

Expected: FAIL — delete not blocked / metrics not cascaded

- [ ] **Step 3: Write minimal implementation**

```python
def count_events_by_action(conn: sqlite3.Connection, action_id: int) -> int:
    row = _row(conn, "SELECT COUNT(*) AS c FROM Event WHERE ActionId = ?", (action_id,))
    return int(row["c"]) if row else 0


def delete_team_stat_metrics_by_action(conn: sqlite3.Connection, action_id: int) -> None:
    _run(conn, "DELETE FROM TeamStatMetric WHERE ActionId = ?", (action_id,))


def delete_team_stat_metrics_by_category(conn: sqlite3.Connection, category_id: int) -> None:
    _run(
        conn,
        """
        DELETE FROM TeamStatMetric
        WHERE ActionId IN (SELECT Id FROM Action WHERE CategoryId = ?)
        """,
        (category_id,),
    )


def delete_action(conn: sqlite3.Connection, action_id: int) -> None:
    if count_events_by_action(conn, action_id) > 0:
        raise ValueError("Действие используется в событиях матчей.")
    delete_team_stat_metrics_by_action(conn, action_id)
    _run(conn, "DELETE FROM Action WHERE Id = ?", (action_id,))


def delete_category(conn: sqlite3.Connection, category_id: int) -> None:
    actions = list_actions_by_category(conn, category_id)
    for action in actions:
        if count_events_by_action(conn, int(action["Id"])) > 0:
            raise ValueError("Категория содержит действия, используемые в событиях матчей.")
    delete_team_stat_metrics_by_category(conn, category_id)
    _run(conn, "DELETE FROM Category WHERE Id = ?", (category_id,))
```

Update `backend/app.py` delete routes to catch `ValueError` and `flash(str(exc), "error")` (mirror `templates_delete` pattern):

```python
    @app.post("/directories/templates/<int:template_id>/categories/<int:category_id>/delete")
    def template_delete_category(template_id: int, category_id: int):
        try:
            with db() as conn:
                repo.delete_category(conn, category_id)
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/delete")
    def template_delete_action(template_id: int, action_id: int):
        try:
            with db() as conn:
                repo.delete_action(conn, action_id)
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("template_detail", template_id=template_id))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricDeleteSafetyTests -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/repository.py backend/app.py tests/test_team_stat_metrics.py
git commit -m "feat: block action/category delete when used in events"
```

---

### Task 6: Metric constructor page (routes + template)

**Files:**
- Create: `templates/templates/stat_metrics.html`
- Modify: `backend/app.py`
- Test: manual via Task 8 page tests; optional smoke in `tests/test_match_statistics_page.py`

**Interfaces:**
- Consumes: all repository metric functions (Tasks 2–3)
- Produces Flask routes:
  - `GET /directories/templates/<int:template_id>/stat-metrics` → `template_stat_metrics`
  - `POST .../stat-metrics/create` → `template_stat_metrics_create`
  - `POST .../stat-metrics/<int:metric_id>/update` → `template_stat_metrics_update`
  - `POST .../stat-metrics/<int:metric_id>/delete` → `template_stat_metrics_delete`
  - `POST .../stat-metrics/<int:metric_id>/move-up` → `template_stat_metrics_move_up`
  - `POST .../stat-metrics/<int:metric_id>/move-down` → `template_stat_metrics_move_down`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_match_statistics_page.py`:

```python
class StatMetricsConstructorPageTests(unittest.TestCase):
    # setUp: temp db, ensure_seeded, get rugby template_id

    def test_stat_metrics_page_renders_create_form(self) -> None:
        resp = self.client.get(f"/directories/templates/{self.template_id}/stat-metrics")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Командные метрики", html)
        self.assertIn('name="outcomeFilter"', html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_stat_metrics_page_renders_create_form -v`

Expected: FAIL — 404

- [ ] **Step 3: Write minimal implementation**

Add routes to `backend/app.py` (after `template_detail`):

```python
    @app.get("/directories/templates/<int:template_id>/stat-metrics")
    def template_stat_metrics(template_id: int):
        with db() as conn:
            template = repo.get_sport_template(conn, template_id)
            if not template:
                return redirect(url_for("templates_page"))
            metrics = repo.list_team_stat_metrics(conn, template_id)
            categories = repo.list_categories_by_template(conn, template_id)
            actions = []
            for cat in categories:
                for action in repo.list_actions_by_category(conn, int(cat["Id"])):
                    actions.append(action)
        return render_template(
            "templates/stat_metrics.html",
            template=template,
            metrics=metrics,
            actions=actions,
        )

    @app.post("/directories/templates/<int:template_id>/stat-metrics/create")
    def template_stat_metrics_create(template_id: int):
        name = request.form.get("name", "").strip()
        action_id = request.form.get("actionId", type=int)
        outcome_filter = request.form.get("outcomeFilter", "any")
        if name and action_id:
            try:
                with db() as conn:
                    repo.create_team_stat_metric(conn, template_id, name, action_id, outcome_filter)
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/update")
    def template_stat_metrics_update(template_id: int, metric_id: int):
        name = request.form.get("name", "").strip()
        action_id = request.form.get("actionId", type=int)
        outcome_filter = request.form.get("outcomeFilter", "any")
        if name and action_id:
            try:
                with db() as conn:
                    repo.update_team_stat_metric(conn, metric_id, name, action_id, outcome_filter)
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/delete")
    def template_stat_metrics_delete(template_id: int, metric_id: int):
        with db() as conn:
            repo.delete_team_stat_metric(conn, metric_id)
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/move-up")
    def template_stat_metrics_move_up(template_id: int, metric_id: int):
        with db() as conn:
            repo.swap_team_stat_metric_order(conn, template_id, metric_id, "up")
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/move-down")
    def template_stat_metrics_move_down(template_id: int, metric_id: int):
        with db() as conn:
            repo.swap_team_stat_metric_order(conn, template_id, metric_id, "down")
        return redirect(url_for("template_stat_metrics", template_id=template_id))
```

Create `templates/templates/stat_metrics.html`:

```html
{% extends "base.html" %}
{% block content %}
<p><a href="{{ url_for('template_detail', template_id=template.Id) }}">← {{ template.Name }}</a></p>
<h1 class="page-title">Командные метрики: {{ template.Name }}</h1>

<div class="card">
  <h3>Новая метрика</h3>
  <form class="form-row" method="post" action="{{ url_for('template_stat_metrics_create', template_id=template.Id) }}">
    <input name="name" placeholder="Название метрики" required />
    <select name="actionId" required>
      <option value="">Действие</option>
      {% for action in actions %}
      <option value="{{ action.Id }}">{{ action.Name }}</option>
      {% endfor %}
    </select>
    <select name="outcomeFilter">
      <option value="any">Любой исход</option>
      <option value="Success">Успех</option>
      <option value="Failure">Неудача</option>
    </select>
    <button class="btn btn-primary" type="submit">Добавить</button>
  </form>
</div>

<div class="card">
  <table class="data-table">
    <thead><tr><th>Название</th><th>Действие</th><th>Исход</th><th></th></tr></thead>
    <tbody>
      {% for m in metrics %}
      <tr>
        <td colspan="4">
          <form class="form-row" method="post" action="{{ url_for('template_stat_metrics_update', template_id=template.Id, metric_id=m.Id) }}">
            <input name="name" value="{{ m.Name }}" />
            <select name="actionId">
              {% for action in actions %}
              <option value="{{ action.Id }}" {% if action.Id == m.ActionId %}selected{% endif %}>{{ action.Name }}</option>
              {% endfor %}
            </select>
            <select name="outcomeFilter">
              <option value="any" {% if m.OutcomeFilter == 'any' %}selected{% endif %}>Любой</option>
              <option value="Success" {% if m.OutcomeFilter == 'Success' %}selected{% endif %}>Успех</option>
              <option value="Failure" {% if m.OutcomeFilter == 'Failure' %}selected{% endif %}>Неудача</option>
            </select>
            <button class="btn btn-primary" type="submit">Сохранить</button>
          </form>
          <form method="post" action="{{ url_for('template_stat_metrics_move_up', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
            <button class="btn" type="submit">↑</button>
          </form>
          <form method="post" action="{{ url_for('template_stat_metrics_move_down', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
            <button class="btn" type="submit">↓</button>
          </form>
          <form method="post" action="{{ url_for('template_stat_metrics_delete', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
            <button class="btn btn-danger" type="submit">Удалить</button>
          </form>
        </td>
      </tr>
      {% else %}
      <tr><td colspan="4">Метрики не настроены.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_stat_metrics_page_renders_create_form -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app.py templates/templates/stat_metrics.html tests/test_match_statistics_page.py
git commit -m "feat: add team stat metric constructor page"
```

---

### Task 7: Template detail navigation link

**Files:**
- Modify: `templates/templates/detail.html` (link only — no inline constructor)

- [ ] **Step 1: Write the failing test**

```python
    def test_template_detail_links_to_stat_metrics(self) -> None:
        resp = self.client.get(f"/directories/templates/{self.template_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("/stat-metrics", html)
        self.assertIn("Командные метрики", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_template_detail_links_to_stat_metrics -v`

Expected: FAIL — link absent

- [ ] **Step 3: Write minimal implementation**

Add after the page title in `templates/templates/detail.html`:

```html
<p>
  <a href="{{ url_for('template_stat_metrics', template_id=template.Id) }}">Командные метрики</a>
</p>
```

Do not add metric CRUD to `detail.html`; leave `ShowInReport` checkboxes unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_template_detail_links_to_stat_metrics -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/templates/detail.html tests/test_match_statistics_page.py
git commit -m "feat: link template detail to stat metrics page"
```

---

### Task 8: Match statistics page (route + template + score)

**Files:**
- Create: `templates/matches/statistics.html`
- Modify: `backend/app.py`, `static/app.css`

**Interfaces:**
- Consumes: `calculate_match_score_for_match`, `get_match_team_stat_counts`, `get_match`, `list_teams`
- Produces: `GET /matches/<int:match_id>/statistics` → `match_statistics`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_match_statistics_page.py`:

```python
class MatchStatisticsPageTests(unittest.TestCase):
    def setUp(self) -> None:
        # temp db, seed match with lineup + metrics + events (reuse TeamStatMetricCountTests seed)
        ...

    def test_statistics_page_shows_score_and_counts(self) -> None:
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("match-score", html)
        self.assertIn("TEST_Pass OK", html)
        self.assertIn("match-statistics", html)
        self.assertNotIn("Разметка", html)  # no edit controls

    def test_empty_metrics_shows_message(self) -> None:
        conn = connect(self.db_path)
        try:
            conn.execute("DELETE FROM TeamStatMetric")
            conn.commit()
        finally:
            conn.close()
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        html = resp.get_data(as_text=True)
        self.assertIn("match-score", html)
        self.assertIn("Метрики не настроены", html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests -v`

Expected: FAIL — 404

- [ ] **Step 3: Write minimal implementation**

Route in `backend/app.py`:

```python
    @app.get("/matches/<int:match_id>/statistics")
    def match_statistics(match_id: int):
        with db() as conn:
            match = repo.get_match(conn, match_id)
            if not match:
                return redirect(url_for("matches_page"))
            teams = repo.list_teams(conn)
            score = calculate_match_score_for_match(conn, match_id)
            metric_rows = repo.get_match_team_stat_counts(conn, match_id)
        return render_template(
            "matches/statistics.html",
            match=match,
            teams=teams,
            score=score,
            metric_rows=metric_rows,
        )
```

Create `templates/matches/statistics.html`:

```html
{% extends "base.html" %}
{% block content %}
<p><a href="{{ url_for('matches_page') }}">← Матчи</a></p>
<h1 class="page-title">Статистика матча</h1>

{% include "tagging/_score.html" %}

{% if metric_rows %}
<div class="card match-statistics">
  <div class="match-statistics__col">
    <h3>{{ (teams | selectattr("Id", "equalto", match.HomeTeamId) | list | first).Name }}</h3>
    <table class="data-table">
      <thead><tr><th>Метрика</th><th>Значение</th></tr></thead>
      <tbody>
        {% for row in metric_rows %}
        <tr><td>{{ row.name }}</td><td>{{ row.home_count }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="match-statistics__col">
    <h3>{{ (teams | selectattr("Id", "equalto", match.AwayTeamId) | list | first).Name }}</h3>
    <table class="data-table">
      <thead><tr><th>Метрика</th><th>Значение</th></tr></thead>
      <tbody>
        {% for row in metric_rows %}
        <tr><td>{{ row.name }}</td><td>{{ row.away_count }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% else %}
<div class="card"><p>Метрики не настроены для шаблона этого матча.</p></div>
{% endif %}
{% endblock %}
```

Add to `static/app.css`:

```css
.match-statistics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.match-statistics__col h3 {
  margin-top: 0;
}

@media (max-width: 900px) {
  .match-statistics {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests -v`

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app.py templates/matches/statistics.html static/app.css tests/test_match_statistics_page.py
git commit -m "feat: add read-only match team statistics page"
```

---

### Task 9: Matches list Statistics link

**Files:**
- Modify: `templates/matches/index.html`
- Test: `tests/test_match_statistics_page.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_matches_list_has_statistics_link(self) -> None:
        resp = self.client.get("/matches")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn(f"/matches/{self.match_id}/statistics", html)
        self.assertIn("Статистика", html)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests.test_matches_list_has_statistics_link -v`

Expected: FAIL — link absent

- [ ] **Step 3: Write minimal implementation**

In `templates/matches/index.html`, add to the actions column:

```html
<a href="{{ url_for('match_statistics', match_id=m.Id) }}">Статистика</a> |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests.test_matches_list_has_statistics_link -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add templates/matches/index.html tests/test_match_statistics_page.py
git commit -m "feat: add Statistics link on matches list"
```

---

### Task 10: Full test suite and documentation

**Files:**
- Modify: `docs/development-context.md`
- Test: all new test modules

- [ ] **Step 1: Run full test suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS (existing + new)

- [ ] **Step 2: Update development-context.md**

Add under routes section:

```markdown
| GET | `/directories/templates/<id>/stat-metrics` | Конструктор командных метрик шаблона (↑/↓, CRUD) |
| GET | `/matches/<id>/statistics` | Read-only статистика матча (счёт + метрики home/away) |
```

Add note: match statistics attribute player events via `MatchLineup`; `/reports` unchanged.

- [ ] **Step 3: Commit**

```bash
git add docs/development-context.md
git commit -m "docs: document match team statistics routes"
```

---

## Self-Review Checklist

| Spec requirement | Task |
|------------------|------|
| TeamStatMetric table + migration | Task 1 |
| Metric CRUD + template action validation | Task 2 |
| ↑/↓ reorder on constructor page | Tasks 3, 6 |
| Separate constructor page + detail link | Tasks 6, 7 |
| GET /matches/<id>/statistics | Task 8 |
| MatchLineup attribution, single count query | Task 4 |
| Outcome filters any/Success/Failure | Task 4 |
| Zero counts visible | Task 4 (always emit all metrics) |
| Empty metrics message | Task 8 |
| Block action/category delete if used in events | Task 5 |
| Cascade metrics when action unused | Task 5 |
| Statistics link on matches list | Task 9 |
| Isolated TEST_ tests, not production DB | All test tasks |
| SQL only in repository.py | Global constraint |
| No player drill-down on statistics page | Task 8 template |
| ShowInReport unchanged | Task 7 (link only) |

**Placeholder scan:** none — all steps include concrete code, paths, and commands.

**Type consistency:** `get_match_team_stat_counts` return shape used consistently in route and template (`metric_id`, `name`, `home_count`, `away_count`).
