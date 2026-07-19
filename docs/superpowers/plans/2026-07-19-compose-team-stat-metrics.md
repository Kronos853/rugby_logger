---
change: compose-team-stat-metrics
design-doc: docs/superpowers/specs/2026-07-19-compose-team-stat-metrics-design.md
base-ref: e18fdc90aa312992ba38c350b9fb863654c963f5
---

# Compose Team Stat Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend template team-statistic metrics so each metric is an ordered sum of Action + Outcome + perspective (`own`/`opponent`) conditions, with legacy single-condition metrics migrated unchanged and match statistics computed from one composite repository query.

**Architecture:** Normalize conditions into `TeamStatMetricCondition` (child of slimmed `TeamStatMetric`). A transactional migration copies legacy `ActionId`/`OutcomeFilter` into one `own` condition per metric, then rebuilds the parent table without legacy columns. Repository functions in `backend/repository.py` handle metric + condition CRUD, last-condition auto-deletes parent metric, and a single `get_match_team_stat_counts` query joins attributed events to all conditions with additive own/opponent target-team mapping. Flask routes and `templates/templates/stat_metrics.html` expose nested condition CRUD and the checkbox «Учитывать события противника».

**Tech Stack:** Python 3, Flask, Jinja2, HTMX (existing), SQLite file DB (`backend/db.py`), unittest + Flask `test_client`, isolated temp DB via `SPORTS_LOGGER_DB` env var.

## Global Constraints

- SQL only in `backend/repository.py` — no raw SQL in routes, templates, or tests beyond `connect()` + repo calls.
- Schema sync: every DDL change in both `docs/schema.sql` and `backend/db.py` (`SCHEMA_SQL` + `_pending_migrations` / `_apply_migrations`); auto-backup runs before migrate via `ensure_db`.
- Tests use isolated SQLite (`tempfile` or `:memory:`); entities prefixed `TEST_`; never read or write `data/sports_logger.db`.
- Do not modify existing user records in production DB during manual checks.
- Russian UI strings where existing UI is Russian; English for this plan artifact.
- Outcome filter values: `any` | `Success` | `Failure`. Perspective values: `own` | `opponent`.
- Match statistics page layout unchanged; only count semantics deepen.
- `/reports` and `ShowInReport` behavior unchanged.
- Deleting the last condition through constructor controls auto-deletes the parent metric (not reject).
- Overlapping conditions are additive (one event may count multiple times).

## File Structure

| File | Responsibility |
|------|----------------|
| `docs/schema.sql` | `TeamStatMetric` (name + sort only) + `TeamStatMetricCondition` table + indexes |
| `backend/db.py` | Updated `SCHEMA_SQL`, `_pending_migrations`, `_migrate_team_stat_metric_conditions` |
| `backend/repository.py` | Metric/condition CRUD, composite count query, action/category delete safety |
| `backend/app.py` | Constructor routes for metric + condition CRUD |
| `templates/templates/stat_metrics.html` | Grouped conditions, opponent checkbox, metric name-only edit |
| `tests/test_team_stat_metrics.py` | Schema, migration, CRUD, aggregation, delete safety |
| `tests/test_match_statistics_page.py` | Constructor page + statistics page regressions |
| `docs/development-context.md` | Composite metric semantics note |

---

### Task 1: TeamStatMetricCondition schema and slim TeamStatMetric

**Files:**
- Modify: `docs/schema.sql` — replace `TeamStatMetric` definition; add `TeamStatMetricCondition`; update indexes
- Modify: `backend/db.py` — `SCHEMA_SQL` (lines ~46–56), `_pending_migrations`
- Test: `tests/test_team_stat_metrics.py` — update `TeamStatMetricSchemaTests`

**Interfaces:**
- Produces fresh-install tables:
  - `TeamStatMetric(Id, SportTemplateId, Name, SortOrder)`
  - `TeamStatMetricCondition(Id, TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)`

- [x] **Step 1: Write the failing test**

Replace `test_team_stat_metric_table_exists_after_ensure_db` in `tests/test_team_stat_metrics.py`:

```python
    def test_team_stat_metric_tables_exist_after_ensure_db(self) -> None:
        ensure_db(self.db_path)
        conn = connect(self.db_path)
        try:
            metric_row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='TeamStatMetric'"
            ).fetchone()
            condition_row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='TeamStatMetricCondition'"
            ).fetchone()
            self.assertIsNotNone(metric_row)
            self.assertIsNotNone(condition_row)
            metric_columns = {r[1] for r in conn.execute("PRAGMA table_info(TeamStatMetric)")}
            condition_columns = {
                r[1] for r in conn.execute("PRAGMA table_info(TeamStatMetricCondition)")
            }
            self.assertEqual(metric_columns, {"Id", "SportTemplateId", "Name", "SortOrder"})
            self.assertEqual(
                condition_columns,
                {
                    "Id",
                    "TeamStatMetricId",
                    "ActionId",
                    "OutcomeFilter",
                    "Perspective",
                    "SortOrder",
                },
            )
        finally:
            conn.close()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricSchemaTests.test_team_stat_metric_tables_exist_after_ensure_db -v`

Expected: FAIL — `TeamStatMetricCondition` table not found; `TeamStatMetric` still has `ActionId`/`OutcomeFilter`.

- [x] **Step 3: Write minimal implementation**

Replace `TeamStatMetric` in `docs/schema.sql`:

```sql
CREATE TABLE TeamStatMetric (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SportTemplateId INT             NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
    Name            NVARCHAR(100)   NOT NULL,
    SortOrder       INT             NOT NULL DEFAULT 0
);

CREATE TABLE TeamStatMetricCondition (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    TeamStatMetricId INT            NOT NULL REFERENCES TeamStatMetric(Id) ON DELETE CASCADE,
    ActionId        INT             NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
    OutcomeFilter   VARCHAR(10)     NOT NULL DEFAULT 'any'
                    CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
    Perspective     VARCHAR(10)     NOT NULL DEFAULT 'own'
                    CHECK (Perspective IN ('own', 'opponent')),
    SortOrder       INT             NOT NULL DEFAULT 0
);
```

Replace indexes at bottom of `docs/schema.sql`:

```sql
CREATE INDEX IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId);
CREATE INDEX IX_TeamStatMetricCondition_MetricSort ON TeamStatMetricCondition(TeamStatMetricId, SortOrder);
CREATE INDEX IX_TeamStatMetricCondition_ActionId ON TeamStatMetricCondition(ActionId);
```

Update `backend/db.py` `SCHEMA_SQL` — replace the `TeamStatMetric` block:

```python
CREATE TABLE IF NOT EXISTS TeamStatMetric (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  SortOrder INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS TeamStatMetricCondition (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  TeamStatMetricId INTEGER NOT NULL REFERENCES TeamStatMetric(Id) ON DELETE CASCADE,
  ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
  OutcomeFilter TEXT NOT NULL DEFAULT 'any' CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
  Perspective TEXT NOT NULL DEFAULT 'own' CHECK (Perspective IN ('own', 'opponent')),
  SortOrder INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId);
CREATE INDEX IF NOT EXISTS IX_TeamStatMetricCondition_MetricSort ON TeamStatMetricCondition(TeamStatMetricId, SortOrder);
CREATE INDEX IF NOT EXISTS IX_TeamStatMetricCondition_ActionId ON TeamStatMetricCondition(ActionId);
```

Extend `_pending_migrations` (after existing `TeamStatMetric` check):

```python
    if "TeamStatMetricCondition" not in tables:
        return True
    metric_columns = {row[1] for row in conn.execute("PRAGMA table_info(TeamStatMetric)")}
    if "ActionId" in metric_columns:
        return True
```

- [x] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricSchemaTests.test_team_stat_metric_tables_exist_after_ensure_db -v`

Expected: PASS on a fresh temp DB (migration task adds legacy upgrade path).

- [x] **Step 5: Commit**

```bash
git add docs/schema.sql backend/db.py tests/test_team_stat_metrics.py
git commit -m "feat: add TeamStatMetricCondition schema for fresh installs"
```

---

### Task 2: Legacy migration and count-preservation regression

**Files:**
- Modify: `backend/db.py` — add `_migrate_team_stat_metric_conditions`, call from `_apply_migrations`
- Test: `tests/test_team_stat_metrics.py` — add `TeamStatMetricMigrationTests`

**Interfaces:**
- Consumes: legacy `TeamStatMetric` with `ActionId`/`OutcomeFilter` (pre-change DBs)
- Produces: migrated DB with conditions + rebuilt parent; `_pending_migrations` returns False after migration

- [x] **Step 1: Write the failing test**

Add to `tests/test_team_stat_metrics.py`:

```python
class TeamStatMetricMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _seed_legacy_metric_db(self) -> tuple[int, int, int, int]:
        conn = connect(self.db_path)
        try:
            conn.executescript(
                """
                CREATE TABLE SportTemplate (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  Name TEXT NOT NULL UNIQUE,
                  PeriodCount INTEGER NOT NULL DEFAULT 2
                );
                CREATE TABLE Category (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
                  Name TEXT NOT NULL,
                  SortOrder INTEGER NOT NULL DEFAULT 0,
                  ShowInReport INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE Action (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  CategoryId INTEGER NOT NULL REFERENCES Category(Id) ON DELETE CASCADE,
                  Name TEXT NOT NULL,
                  HasOutcome INTEGER NOT NULL DEFAULT 1,
                  SortOrder INTEGER NOT NULL DEFAULT 0,
                  ColorClass TEXT NOT NULL DEFAULT 'handling',
                  ShowInReport INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE Team (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  Name TEXT NOT NULL,
                  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE Player (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  TeamId INTEGER NOT NULL REFERENCES Team(Id) ON DELETE CASCADE,
                  Name TEXT NOT NULL,
                  FullName TEXT,
                  BirthDay TEXT,
                  IsActive INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE Match (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id),
                  HomeTeamId INTEGER NOT NULL REFERENCES Team(Id),
                  AwayTeamId INTEGER NOT NULL REFERENCES Team(Id),
                  MatchDate TEXT,
                  HomeSquadId INTEGER,
                  AwaySquadId INTEGER,
                  TournamentId INTEGER
                );
                CREATE TABLE MatchLineup (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  MatchId INTEGER NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
                  TeamId INTEGER NOT NULL REFERENCES Team(Id),
                  PlayerId INTEGER NOT NULL REFERENCES Player(Id),
                  Position TEXT,
                  LineupRole TEXT NOT NULL DEFAULT 'starter',
                  SortOrder INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE Event (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  MatchId INTEGER NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
                  Period INTEGER NOT NULL,
                  Timestamp REAL NOT NULL,
                  SubjectType TEXT NOT NULL,
                  PlayerId INTEGER REFERENCES Player(Id),
                  TeamId INTEGER REFERENCES Team(Id),
                  ActionId INTEGER NOT NULL REFERENCES Action(Id),
                  Outcome TEXT,
                  Comment TEXT
                );
                CREATE TABLE TeamStatMetric (
                  Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
                  Name TEXT NOT NULL,
                  ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
                  OutcomeFilter TEXT NOT NULL DEFAULT 'any'
                    CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
                  SortOrder INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            template_id = conn.execute(
                "INSERT INTO SportTemplate (Name) VALUES ('TEST_Legacy')"
            ).lastrowid
            category_id = conn.execute(
                "INSERT INTO Category (SportTemplateId, Name, SortOrder) VALUES (?, 'TEST_Cat', 0)",
                (template_id,),
            ).lastrowid
            action_id = conn.execute(
                "INSERT INTO Action (CategoryId, Name, HasOutcome, SortOrder, ColorClass) VALUES (?, 'TEST_Pass', 1, 0, 'handling')",
                (category_id,),
            ).lastrowid
            home_id = conn.execute(
                "INSERT INTO Team (Name) VALUES ('TEST_Home')"
            ).lastrowid
            away_id = conn.execute(
                "INSERT INTO Team (Name) VALUES ('TEST_Away')"
            ).lastrowid
            player_id = conn.execute(
                "INSERT INTO Player (TeamId, Name) VALUES (?, 'TEST_Player')",
                (home_id,),
            ).lastrowid
            match_id = conn.execute(
                """INSERT INTO Match (SportTemplateId, HomeTeamId, AwayTeamId, MatchDate)
                   VALUES (?, ?, ?, '2026-01-01')""",
                (template_id, home_id, away_id),
            ).lastrowid
            conn.execute(
                """INSERT INTO MatchLineup (MatchId, TeamId, PlayerId, LineupRole, SortOrder)
                   VALUES (?, ?, ?, 'starter', 0)""",
                (match_id, home_id, player_id),
            )
            metric_id = conn.execute(
                """INSERT INTO TeamStatMetric (SportTemplateId, Name, ActionId, OutcomeFilter, SortOrder)
                   VALUES (?, 'TEST_LegacyMetric', ?, 'Success', 0)""",
                (template_id, action_id),
            ).lastrowid
            conn.execute(
                """INSERT INTO Event (MatchId, Period, Timestamp, SubjectType, PlayerId, ActionId, Outcome)
                   VALUES (?, 1, 0, 'player', ?, ?, 'Success')""",
                (match_id, player_id, action_id),
            )
            conn.commit()
            return int(template_id), int(metric_id), int(match_id), int(action_id)
        finally:
            conn.close()

    def test_legacy_metric_migrates_to_own_condition_with_same_counts(self) -> None:
        template_id, metric_id, match_id, action_id = self._seed_legacy_metric_db()
        ensure_db(self.db_path)
        conn = connect(self.db_path)
        try:
            metric_columns = {r[1] for r in conn.execute("PRAGMA table_info(TeamStatMetric)")}
            self.assertNotIn("ActionId", metric_columns)
            conditions = conn.execute(
                """SELECT ActionId, OutcomeFilter, Perspective, SortOrder
                   FROM TeamStatMetricCondition WHERE TeamStatMetricId = ?""",
                (metric_id,),
            ).fetchall()
            self.assertEqual(len(conditions), 1)
            self.assertEqual(int(conditions[0][0]), action_id)
            self.assertEqual(conditions[0][1], "Success")
            self.assertEqual(conditions[0][2], "own")
            self.assertEqual(int(conditions[0][3]), 0)
        finally:
            conn.close()
        # Counts checked after repository refactor in Task 5; here verify row exists post-migration.
        conn = connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT Name FROM TeamStatMetric WHERE Id = ?", (metric_id,)
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "TEST_LegacyMetric")
        finally:
            conn.close()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricMigrationTests.test_legacy_metric_migrates_to_own_condition_with_same_counts -v`

Expected: FAIL — `ActionId` still on `TeamStatMetric`; no `TeamStatMetricCondition` rows.

- [x] **Step 3: Write minimal implementation**

Add to `backend/db.py`:

```python
def _migrate_team_stat_metric_conditions(conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "TeamStatMetric" not in tables:
        return
    metric_columns = {row[1] for row in conn.execute("PRAGMA table_info(TeamStatMetric)")}
    if "ActionId" not in metric_columns:
        return

    conn.execute(
        """
        CREATE TABLE TeamStatMetricCondition (
          Id INTEGER PRIMARY KEY AUTOINCREMENT,
          TeamStatMetricId INTEGER NOT NULL REFERENCES TeamStatMetric(Id) ON DELETE CASCADE,
          ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
          OutcomeFilter TEXT NOT NULL DEFAULT 'any'
            CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
          Perspective TEXT NOT NULL DEFAULT 'own'
            CHECK (Perspective IN ('own', 'opponent')),
          SortOrder INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        INSERT INTO TeamStatMetricCondition
          (TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)
        SELECT Id, ActionId, OutcomeFilter, 'own', 0
        FROM TeamStatMetric
        """
    )
    conn.execute(
        """
        CREATE TABLE TeamStatMetric_new (
          Id INTEGER PRIMARY KEY AUTOINCREMENT,
          SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
          Name TEXT NOT NULL,
          SortOrder INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        INSERT INTO TeamStatMetric_new (Id, SportTemplateId, Name, SortOrder)
        SELECT Id, SportTemplateId, Name, SortOrder FROM TeamStatMetric
        """
    )
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TABLE TeamStatMetric")
    conn.execute("ALTER TABLE TeamStatMetric_new RENAME TO TeamStatMetric")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS IX_TeamStatMetricCondition_MetricSort ON TeamStatMetricCondition(TeamStatMetricId, SortOrder)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS IX_TeamStatMetricCondition_ActionId ON TeamStatMetricCondition(ActionId)"
    )
```

Call from `_apply_migrations` after `_migrate_team_stat_metrics`:

```python
    _migrate_team_stat_metrics(conn)
    _migrate_team_stat_metric_conditions(conn)
```

- [x] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricMigrationTests.test_legacy_metric_migrates_to_own_condition_with_same_counts -v`

Expected: PASS

- [x] **Step 5: Commit**

```bash
git add backend/db.py tests/test_team_stat_metrics.py
git commit -m "feat: migrate legacy TeamStatMetric rows to conditions"
```

---

### Task 3: Repository — metric create (parent + first condition) and name-only update

**Files:**
- Modify: `backend/repository.py` — refactor `create_team_stat_metric`, `update_team_stat_metric`; add condition list/get helpers and constants
- Test: `tests/test_team_stat_metrics.py` — update `TeamStatMetricCrudTests`

**Interfaces:**
- Consumes: Task 1–2 schema
- Produces:
  - `VALID_PERSPECTIVES = frozenset({"own", "opponent"})`
  - `list_team_stat_metric_conditions(conn, metric_id: int) -> list[sqlite3.Row]`
  - `get_team_stat_metric_condition(conn, condition_id: int) -> sqlite3.Row | None`
  - `create_team_stat_metric(conn, template_id: int, name: str, action_id: int, outcome_filter: str, perspective: str = "own") -> int` — inserts parent + first condition atomically
  - `update_team_stat_metric(conn, metric_id: int, name: str) -> None` — name only

- [x] **Step 1: Write the failing tests**

Update `TeamStatMetricCrudTests` — replace existing CRUD tests:

```python
    def test_create_metric_inserts_parent_and_first_condition(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Passes", self.action_id, "Success", "own"
            )
            metric = repo.get_team_stat_metric(conn, metric_id)
            assert metric is not None
            self.assertEqual(metric["Name"], "TEST_Passes")
            conditions = repo.list_team_stat_metric_conditions(conn, metric_id)
            self.assertEqual(len(conditions), 1)
            self.assertEqual(int(conditions[0]["ActionId"]), self.action_id)
            self.assertEqual(conditions[0]["OutcomeFilter"], "Success")
            self.assertEqual(conditions[0]["Perspective"], "own")
            self.assertEqual(int(conditions[0]["SortOrder"]), 0)
        finally:
            conn.close()

    def test_create_rejects_invalid_perspective(self) -> None:
        conn = connect(self.db_path)
        try:
            with self.assertRaises(ValueError):
                repo.create_team_stat_metric(
                    conn, self.template_id, "TEST_Bad", self.action_id, "any", "both"
                )
        finally:
            conn.close()

    def test_update_metric_name_only(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Old", self.action_id, "any", "own"
            )
            repo.update_team_stat_metric(conn, metric_id, "TEST_New")
            row = repo.get_team_stat_metric(conn, metric_id)
            assert row is not None
            self.assertEqual(row["Name"], "TEST_New")
            conditions = repo.list_team_stat_metric_conditions(conn, metric_id)
            self.assertEqual(conditions[0]["OutcomeFilter"], "any")
        finally:
            conn.close()
```

Update `test_create_and_list_metrics_ordered_by_sort_order` to use new signature (no `OutcomeFilter` on metric row):

```python
    def test_create_and_list_metrics_ordered_by_sort_order(self) -> None:
        conn = connect(self.db_path)
        try:
            first_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Passes", self.action_id, "Success", "own"
            )
            second_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_All passes", self.action_id, "any", "own"
            )
            rows = repo.list_team_stat_metrics(conn, self.template_id)
            self.assertEqual([int(r["Id"]) for r in rows], [first_id, second_id])
            self.assertEqual(rows[0]["Name"], "TEST_Passes")
            first_conditions = repo.list_team_stat_metric_conditions(conn, first_id)
            self.assertEqual(first_conditions[0]["OutcomeFilter"], "Success")
        finally:
            conn.close()
```

Remove or rewrite `test_update_and_delete_metric` (delete stays; update moves to name-only test above).

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests.test_create_metric_inserts_parent_and_first_condition -v`

Expected: FAIL — `list_team_stat_metric_conditions` missing or insert still targets legacy columns.

- [x] **Step 3: Write minimal implementation**

Add to `backend/repository.py`:

```python
VALID_PERSPECTIVES = frozenset({"own", "opponent"})


def list_team_stat_metric_conditions(
    conn: sqlite3.Connection, metric_id: int
) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """SELECT * FROM TeamStatMetricCondition
           WHERE TeamStatMetricId = ? ORDER BY SortOrder, Id""",
        (metric_id,),
    )


def get_team_stat_metric_condition(
    conn: sqlite3.Connection, condition_id: int
) -> sqlite3.Row | None:
    return _row(
        conn, "SELECT * FROM TeamStatMetricCondition WHERE Id = ?", (condition_id,)
    )


def _validate_condition_fields(
    conn: sqlite3.Connection,
    template_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> None:
    if outcome_filter not in VALID_OUTCOME_FILTERS:
        raise ValueError("Недопустимый фильтр исхода.")
    if perspective not in VALID_PERSPECTIVES:
        raise ValueError("Недопустимая перспектива.")
    if not action_belongs_to_template(conn, template_id, action_id):
        raise ValueError("Действие не принадлежит этому шаблону.")
```

Replace `create_team_stat_metric`:

```python
def create_team_stat_metric(
    conn: sqlite3.Connection,
    template_id: int,
    name: str,
    action_id: int,
    outcome_filter: str,
    perspective: str = "own",
) -> int:
    _validate_condition_fields(conn, template_id, action_id, outcome_filter, perspective)
    existing = list_team_stat_metrics(conn, template_id)
    sort_order = (max(int(m["SortOrder"]) for m in existing) + 1) if existing else 0
    metric_id = _insert(
        conn,
        """INSERT INTO TeamStatMetric (SportTemplateId, Name, SortOrder)
           VALUES (?, ?, ?)""",
        (template_id, name.strip(), sort_order),
    )
    _insert(
        conn,
        """INSERT INTO TeamStatMetricCondition
           (TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)
           VALUES (?, ?, ?, ?, 0)""",
        (metric_id, action_id, outcome_filter, perspective),
    )
    return metric_id
```

Replace `update_team_stat_metric`:

```python
def update_team_stat_metric(conn: sqlite3.Connection, metric_id: int, name: str) -> None:
    metric = get_team_stat_metric(conn, metric_id)
    if not metric:
        raise ValueError("Метрика не найдена.")
    _run(
        conn,
        "UPDATE TeamStatMetric SET Name = ? WHERE Id = ?",
        (name.strip(), metric_id),
    )
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCrudTests -v`

Expected: PASS for updated CRUD tests (reorder tests may still pass unchanged).

- [x] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: create metric with first condition, name-only update"
```

---

### Task 4: Repository — condition CRUD, insertion order, last-condition deletes parent

**Files:**
- Modify: `backend/repository.py`
- Test: `tests/test_team_stat_metrics.py` — add `TeamStatMetricConditionCrudTests`

**Interfaces:**
- Consumes: Task 3 metric helpers
- Produces:
  - `create_team_stat_condition(conn, metric_id: int, action_id: int, outcome_filter: str, perspective: str) -> int`
  - `update_team_stat_condition(conn, condition_id: int, action_id: int, outcome_filter: str, perspective: str) -> None`
  - `delete_team_stat_condition(conn, condition_id: int) -> None` — deletes parent metric when last condition removed
  - `delete_team_stat_metric(conn, metric_id: int) -> None` — unchanged; cascades conditions via FK

- [x] **Step 1: Write the failing tests**

```python
class TeamStatMetricConditionCrudTests(unittest.TestCase):
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
            self.action_id = int(
                repo.list_actions_by_category(conn, int(handling["Id"]))[0]["Id"]
            )
            setpiece = next(c for c in categories if c["Name"] == "Set-piece")
            self.other_action_id = int(
                repo.list_actions_by_category(conn, int(setpiece["Id"]))[0]["Id"]
            )
            self.metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Composite", self.action_id, "Success", "own"
            )
        finally:
            conn.close()

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_add_condition_appends_sort_order(self) -> None:
        conn = connect(self.db_path)
        try:
            second_id = repo.create_team_stat_condition(
                conn, self.metric_id, self.other_action_id, "Failure", "opponent"
            )
            conditions = repo.list_team_stat_metric_conditions(conn, self.metric_id)
            self.assertEqual(len(conditions), 2)
            self.assertEqual(int(conditions[1]["Id"]), second_id)
            self.assertEqual(int(conditions[1]["SortOrder"]), 1)
            self.assertEqual(conditions[1]["Perspective"], "opponent")
        finally:
            conn.close()

    def test_update_condition(self) -> None:
        conn = connect(self.db_path)
        try:
            condition_id = int(
                repo.list_team_stat_metric_conditions(conn, self.metric_id)[0]["Id"]
            )
            repo.update_team_stat_condition(
                conn, condition_id, self.other_action_id, "Failure", "opponent"
            )
            row = repo.get_team_stat_metric_condition(conn, condition_id)
            assert row is not None
            self.assertEqual(int(row["ActionId"]), self.other_action_id)
            self.assertEqual(row["OutcomeFilter"], "Failure")
            self.assertEqual(row["Perspective"], "opponent")
        finally:
            conn.close()

    def test_delete_non_last_condition_keeps_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.create_team_stat_condition(
                conn, self.metric_id, self.other_action_id, "any", "own"
            )
            first_id = int(
                repo.list_team_stat_metric_conditions(conn, self.metric_id)[0]["Id"]
            )
            repo.delete_team_stat_condition(conn, first_id)
            self.assertIsNotNone(repo.get_team_stat_metric(conn, self.metric_id))
            self.assertEqual(len(repo.list_team_stat_metric_conditions(conn, self.metric_id)), 1)
        finally:
            conn.close()

    def test_delete_last_condition_deletes_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            condition_id = int(
                repo.list_team_stat_metric_conditions(conn, self.metric_id)[0]["Id"]
            )
            repo.delete_team_stat_condition(conn, condition_id)
            self.assertIsNone(repo.get_team_stat_metric(conn, self.metric_id))
            self.assertEqual(
                repo.list_team_stat_metric_conditions(conn, self.metric_id), []
            )
        finally:
            conn.close()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricConditionCrudTests -v`

Expected: FAIL — `create_team_stat_condition` not defined.

- [x] **Step 3: Write minimal implementation**

```python
def create_team_stat_condition(
    conn: sqlite3.Connection,
    metric_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> int:
    metric = get_team_stat_metric(conn, metric_id)
    if not metric:
        raise ValueError("Метрика не найдена.")
    template_id = int(metric["SportTemplateId"])
    _validate_condition_fields(conn, template_id, action_id, outcome_filter, perspective)
    existing = list_team_stat_metric_conditions(conn, metric_id)
    sort_order = (max(int(c["SortOrder"]) for c in existing) + 1) if existing else 0
    return _insert(
        conn,
        """INSERT INTO TeamStatMetricCondition
           (TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)
           VALUES (?, ?, ?, ?, ?)""",
        (metric_id, action_id, outcome_filter, perspective, sort_order),
    )


def update_team_stat_condition(
    conn: sqlite3.Connection,
    condition_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> None:
    condition = get_team_stat_metric_condition(conn, condition_id)
    if not condition:
        raise ValueError("Условие не найдено.")
    metric = get_team_stat_metric(conn, int(condition["TeamStatMetricId"]))
    assert metric is not None
    _validate_condition_fields(
        conn, int(metric["SportTemplateId"]), action_id, outcome_filter, perspective
    )
    _run(
        conn,
        """UPDATE TeamStatMetricCondition
           SET ActionId = ?, OutcomeFilter = ?, Perspective = ?
           WHERE Id = ?""",
        (action_id, outcome_filter, perspective, condition_id),
    )


def delete_team_stat_condition(conn: sqlite3.Connection, condition_id: int) -> None:
    condition = get_team_stat_metric_condition(conn, condition_id)
    if not condition:
        return
    metric_id = int(condition["TeamStatMetricId"])
    remaining = [
        c
        for c in list_team_stat_metric_conditions(conn, metric_id)
        if int(c["Id"]) != condition_id
    ]
    _run(conn, "DELETE FROM TeamStatMetricCondition WHERE Id = ?", (condition_id,))
    if not remaining:
        delete_team_stat_metric(conn, metric_id)
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricConditionCrudTests -v`

Expected: PASS (4 tests)

- [x] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: add TeamStatMetricCondition CRUD with last-delete cleanup"
```

---

### Task 5: Repository — composite own/opponent aggregation query

**Files:**
- Modify: `backend/repository.py` — replace `get_match_team_stat_counts`
- Test: `tests/test_team_stat_metrics.py` — rewrite `TeamStatMetricCountTests`; extend migration test

**Interfaces:**
- Consumes: condition CRUD (Task 4), existing event/lineup helpers
- Produces: same `get_match_team_stat_counts(conn, match_id: int) -> list[dict[str, Any]]` return shape (unchanged for templates)

- [x] **Step 1: Write the failing tests**

Rewrite `TeamStatMetricCountTests.setUp` to use new create signature. Replace/add tests:

```python
    def test_legacy_migration_counts_unchanged(self) -> None:
        # Run after Task 2 migration test helper is available — or inline minimal legacy DB.
        migration = TeamStatMetricMigrationTests()
        migration.setUp()
        try:
            _, metric_id, match_id, _ = migration._seed_legacy_metric_db()
            ensure_db(migration.db_path)
            conn = connect(migration.db_path)
            try:
                rows = repo.get_match_team_stat_counts(conn, match_id)
                by_id = {r["metric_id"]: r for r in rows}
                self.assertEqual(by_id[metric_id]["home_count"], 1)
                self.assertEqual(by_id[metric_id]["away_count"], 0)
            finally:
                conn.close()
        finally:
            migration.tearDown()

    def test_own_and_opponent_conditions(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.delete_team_stat_metric(conn, self.metric_success_id)
            repo.delete_team_stat_metric(conn, self.metric_any_id)
            scrum_action = self._get_action_by_name(conn, "Scrum (own)")
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Scrums won", scrum_action, "Success", "own"
            )
            repo.create_team_stat_condition(
                conn, metric_id, scrum_action, "Failure", "opponent"
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=scrum_action, outcome="Success",
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_away, action_id=scrum_action, outcome="Failure",
            )
            rows = repo.get_match_team_stat_counts(conn, self.match_id)
            row = next(r for r in rows if r["metric_id"] == metric_id)
            self.assertEqual(row["home_count"], 2)  # home Success + away Failure (opponent)
            self.assertEqual(row["away_count"], 0)
        finally:
            conn.close()

    def test_overlapping_conditions_are_additive(self) -> None:
        conn = connect(self.db_path)
        try:
            repo.delete_team_stat_metric(conn, self.metric_success_id)
            repo.delete_team_stat_metric(conn, self.metric_any_id)
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Double", self.action_id, "Success", "own"
            )
            repo.create_team_stat_condition(
                conn, metric_id, self.action_id, "any", "own"
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            rows = repo.get_match_team_stat_counts(conn, self.match_id)
            row = next(r for r in rows if r["metric_id"] == metric_id)
            self.assertEqual(row["home_count"], 2)
        finally:
            conn.close()
```

Add helper to `TeamStatMetricCountTests`:

```python
    def _get_action_by_name(self, conn, name: str) -> int:
        categories = repo.list_categories_by_template(conn, self.template_id)
        for category in categories:
            for action in repo.list_actions_by_category(conn, int(category["Id"])):
                if action["Name"] == name:
                    return int(action["Id"])
        raise AssertionError(f"Action not found: {name}")
```

Keep existing `test_outcome_filters_and_zeros`, `test_orphan_player_event_ignored`, `test_transfer_does_not_change_counts` — update setUp create calls to include `"own"` perspective.

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCountTests.test_own_and_opponent_conditions -v`

Expected: FAIL — opponent condition not counted toward home.

- [x] **Step 3: Write minimal implementation**

Replace `get_match_team_stat_counts` body:

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
            END AS AttributedTeamId
          FROM Event e
          LEFT JOIN MatchLineup ml
            ON ml.MatchId = e.MatchId AND ml.PlayerId = e.PlayerId
          WHERE e.MatchId = ?
        ),
        matched AS (
          SELECT
            tsm.Id AS MetricId,
            c.Perspective,
            a.AttributedTeamId
          FROM TeamStatMetric tsm
          INNER JOIN TeamStatMetricCondition c ON c.TeamStatMetricId = tsm.Id
          INNER JOIN attributed a ON a.ActionId = c.ActionId
            AND a.AttributedTeamId IS NOT NULL
            AND (
              c.OutcomeFilter = 'any'
              OR a.Outcome = c.OutcomeFilter
            )
          WHERE tsm.SportTemplateId = ?
            AND a.AttributedTeamId IN (?, ?)
        )
        SELECT
          MetricId,
          CASE
            WHEN Perspective = 'own' THEN AttributedTeamId
            WHEN AttributedTeamId = ? THEN ?
            WHEN AttributedTeamId = ? THEN ?
            ELSE NULL
          END AS TargetTeamId,
          COUNT(*) AS Cnt
        FROM matched
        GROUP BY MetricId, TargetTeamId
        """,
        (
            match_id,
            template_id,
            home_team_id,
            away_team_id,
            home_team_id,
            away_team_id,
            away_team_id,
            home_team_id,
        ),
    )

    counts: dict[tuple[int, int], int] = {}
    for row in count_rows:
        target_team_id = row["TargetTeamId"]
        if target_team_id is None:
            continue
        counts[(int(row["MetricId"]), int(target_team_id))] = int(row["Cnt"])

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

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricCountTests -v`

Expected: PASS (all count tests including migration preservation)

- [x] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: sum composite own/opponent team stat conditions"
```

---

### Task 6: Repository — action/category delete safety for conditions

**Files:**
- Modify: `backend/repository.py` — replace `delete_team_stat_metrics_by_action/category`; add `_delete_empty_team_stat_metrics`
- Test: `tests/test_team_stat_metrics.py` — update `TeamStatMetricDeleteSafetyTests`

**Interfaces:**
- Consumes: condition CRUD (Task 4)
- Produces:
  - `delete_team_stat_conditions_by_action(conn, action_id: int) -> None`
  - `delete_team_stat_conditions_by_category(conn, category_id: int) -> None`
  - `_delete_empty_team_stat_metrics(conn) -> None`
  - Updated `delete_action` / `delete_category` — cascade conditions; remove metrics left with zero conditions; still block when events exist

- [x] **Step 1: Write the failing tests**

Add to `TeamStatMetricDeleteSafetyTests`:

```python
    def test_cascade_only_affected_condition_keeps_composite_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            setpiece = next(
                c for c in repo.list_categories_by_template(conn, self.template_id)
                if c["Name"] == "Set-piece"
            )
            other_action_id = int(
                repo.list_actions_by_category(conn, int(setpiece["Id"]))[0]["Id"]
            )
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Composite", self.action_id, "any", "own"
            )
            repo.create_team_stat_condition(
                conn, metric_id, other_action_id, "Success", "own"
            )
            repo.delete_action(conn, self.action_id)
            self.assertIsNotNone(repo.get_team_stat_metric(conn, metric_id))
            conditions = repo.list_team_stat_metric_conditions(conn, metric_id)
            self.assertEqual(len(conditions), 1)
            self.assertEqual(int(conditions[0]["ActionId"]), other_action_id)
        finally:
            conn.close()

    def test_remove_metric_when_last_condition_cascaded(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Single", self.action_id, "any", "own"
            )
            repo.delete_action(conn, self.action_id)
            self.assertIsNone(repo.get_team_stat_metric(conn, metric_id))
        finally:
            conn.close()
```

Update existing cascade test — still passes with new behavior.

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricDeleteSafetyTests.test_cascade_only_affected_condition_keeps_composite_metric -v`

Expected: FAIL — entire metric deleted instead of one condition.

- [x] **Step 3: Write minimal implementation**

```python
def delete_team_stat_conditions_by_action(conn: sqlite3.Connection, action_id: int) -> None:
    _run(conn, "DELETE FROM TeamStatMetricCondition WHERE ActionId = ?", (action_id,))


def delete_team_stat_conditions_by_category(conn: sqlite3.Connection, category_id: int) -> None:
    _run(
        conn,
        """
        DELETE FROM TeamStatMetricCondition
        WHERE ActionId IN (SELECT Id FROM Action WHERE CategoryId = ?)
        """,
        (category_id,),
    )


def _delete_empty_team_stat_metrics(conn: sqlite3.Connection) -> None:
    _run(
        conn,
        """
        DELETE FROM TeamStatMetric
        WHERE Id NOT IN (
          SELECT DISTINCT TeamStatMetricId FROM TeamStatMetricCondition
        )
        """,
    )


def delete_team_stat_metrics_by_action(conn: sqlite3.Connection, action_id: int) -> None:
    delete_team_stat_conditions_by_action(conn, action_id)
    _delete_empty_team_stat_metrics(conn)


def delete_team_stat_metrics_by_category(conn: sqlite3.Connection, category_id: int) -> None:
    delete_team_stat_conditions_by_category(conn, category_id)
    _delete_empty_team_stat_metrics(conn)
```

`delete_action` / `delete_category` bodies stay the same (they already call the `delete_team_stat_metrics_by_*` helpers).

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_team_stat_metrics.TeamStatMetricDeleteSafetyTests -v`

Expected: PASS (5 tests)

- [x] **Step 5: Commit**

```bash
git add backend/repository.py tests/test_team_stat_metrics.py
git commit -m "feat: cascade action delete through stat metric conditions"
```

---

### Task 7: Constructor routes — metric + condition CRUD

**Files:**
- Modify: `backend/app.py` — update stat-metrics routes
- Test: deferred to Task 9 page tests

**Interfaces:**
- Consumes: repository APIs from Tasks 3–4
- Produces Flask routes:
  - `POST .../stat-metrics/create` — name + first condition + perspective from checkbox
  - `POST .../stat-metrics/<metric_id>/update` — name only
  - `POST .../stat-metrics/<metric_id>/conditions/create`
  - `POST .../stat-metrics/<metric_id>/conditions/<condition_id>/update`
  - `POST .../stat-metrics/<metric_id>/conditions/<condition_id>/delete`
  - Existing delete/move-up/move-down unchanged

- [x] **Step 1: Write the failing test**

Add to `tests/test_match_statistics_page.py`:

```python
    def test_create_metric_with_opponent_checkbox(self) -> None:
        resp = self.client.post(
            f"/directories/templates/{self.template_id}/stat-metrics/create",
            data={
                "name": "TEST_OpponentMetric",
                "actionId": "1",
                "outcomeFilter": "Failure",
                "countOpponent": "1",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        conn = connect(self.db_path)
        try:
            metrics = repo.list_team_stat_metrics(conn, self.template_id)
            metric = next(m for m in metrics if m["Name"] == "TEST_OpponentMetric")
            conditions = repo.list_team_stat_metric_conditions(conn, int(metric["Id"]))
            self.assertEqual(conditions[0]["Perspective"], "opponent")
        finally:
            conn.close()
```

Note: use a real `actionId` from seeded template in setUp (store `self.action_id` like count tests).

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_create_metric_with_opponent_checkbox -v`

Expected: FAIL — perspective stored as `own` or route ignores checkbox.

- [x] **Step 3: Write minimal implementation**

Update `template_stat_metrics` to load conditions per metric:

```python
    @app.get("/directories/templates/<int:template_id>/stat-metrics")
    def template_stat_metrics(template_id: int):
        with db() as conn:
            template = repo.get_sport_template(conn, template_id)
            if not template:
                return redirect(url_for("templates_page"))
            metrics = repo.list_team_stat_metrics(conn, template_id)
            metric_conditions = {
                int(m["Id"]): repo.list_team_stat_metric_conditions(conn, int(m["Id"]))
                for m in metrics
            }
            categories = repo.list_categories_by_template(conn, template_id)
            actions = []
            for cat in categories:
                cat_name = str(cat["Name"])
                for action in repo.list_actions_by_category(conn, int(cat["Id"])):
                    actions.append(
                        {
                            "Id": int(action["Id"]),
                            "Name": f"{cat_name} — {action['Name']}",
                        }
                    )
        return render_template(
            "templates/stat_metrics.html",
            template=template,
            metrics=metrics,
            metric_conditions=metric_conditions,
            actions=actions,
        )
```

Update create route:

```python
    @app.post("/directories/templates/<int:template_id>/stat-metrics/create")
    def template_stat_metrics_create(template_id: int):
        name = request.form.get("name", "").strip()
        action_id = request.form.get("actionId", type=int)
        outcome_filter = request.form.get("outcomeFilter", "any")
        perspective = "opponent" if request.form.get("countOpponent") else "own"
        if name and action_id:
            try:
                with db() as conn:
                    repo.create_team_stat_metric(
                        conn, template_id, name, action_id, outcome_filter, perspective
                    )
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))
```

Update metric update route (name only):

```python
    @app.post("/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/update")
    def template_stat_metrics_update(template_id: int, metric_id: int):
        name = request.form.get("name", "").strip()
        if name:
            try:
                with db() as conn:
                    metric = repo.get_team_stat_metric(conn, metric_id)
                    if not metric or int(metric["SportTemplateId"]) != template_id:
                        flash("Метрика не найдена.", "error")
                    else:
                        repo.update_team_stat_metric(conn, metric_id, name)
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))
```

Add condition routes:

```python
    @app.post(
        "/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/conditions/create"
    )
    def template_stat_metrics_condition_create(template_id: int, metric_id: int):
        action_id = request.form.get("actionId", type=int)
        outcome_filter = request.form.get("outcomeFilter", "any")
        perspective = "opponent" if request.form.get("countOpponent") else "own"
        if action_id:
            try:
                with db() as conn:
                    metric = repo.get_team_stat_metric(conn, metric_id)
                    if not metric or int(metric["SportTemplateId"]) != template_id:
                        flash("Метрика не найдена.", "error")
                    else:
                        repo.create_team_stat_condition(
                            conn, metric_id, action_id, outcome_filter, perspective
                        )
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post(
        "/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/conditions/<int:condition_id>/update"
    )
    def template_stat_metrics_condition_update(
        template_id: int, metric_id: int, condition_id: int
    ):
        action_id = request.form.get("actionId", type=int)
        outcome_filter = request.form.get("outcomeFilter", "any")
        perspective = "opponent" if request.form.get("countOpponent") else "own"
        if action_id:
            try:
                with db() as conn:
                    metric = repo.get_team_stat_metric(conn, metric_id)
                    condition = repo.get_team_stat_metric_condition(conn, condition_id)
                    if (
                        not metric
                        or int(metric["SportTemplateId"]) != template_id
                        or not condition
                        or int(condition["TeamStatMetricId"]) != metric_id
                    ):
                        flash("Условие не найдено.", "error")
                    else:
                        repo.update_team_stat_condition(
                            conn, condition_id, action_id, outcome_filter, perspective
                        )
            except ValueError as exc:
                flash(str(exc), "error")
        return redirect(url_for("template_stat_metrics", template_id=template_id))

    @app.post(
        "/directories/templates/<int:template_id>/stat-metrics/<int:metric_id>/conditions/<int:condition_id>/delete"
    )
    def template_stat_metrics_condition_delete(
        template_id: int, metric_id: int, condition_id: int
    ):
        with db() as conn:
            metric = repo.get_team_stat_metric(conn, metric_id)
            condition = repo.get_team_stat_metric_condition(conn, condition_id)
            if (
                metric
                and int(metric["SportTemplateId"]) == template_id
                and condition
                and int(condition["TeamStatMetricId"]) == metric_id
            ):
                repo.delete_team_stat_condition(conn, condition_id)
        return redirect(url_for("template_stat_metrics", template_id=template_id))
```

- [x] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_create_metric_with_opponent_checkbox -v`

Expected: PASS (after Task 8 template renders checkbox — may need both tasks for full pass; route logic sufficient for DB assertion)

- [x] **Step 5: Commit**

```bash
git add backend/app.py tests/test_match_statistics_page.py
git commit -m "feat: add stat metric condition routes and perspective parsing"
```

---

### Task 8: Constructor template — grouped conditions and opponent checkbox

**Files:**
- Modify: `templates/templates/stat_metrics.html`
- Test: `tests/test_match_statistics_page.py`

**Interfaces:**
- Consumes: `metric_conditions` dict from route (Task 7)
- Produces: UI with nested condition lists, «Учитывать события противника» checkbox on create/add/edit forms, metric name-only edit

- [ ] **Step 1: Write the failing tests**

Add to `StatMetricsConstructorPageTests`:

```python
    def test_stat_metrics_page_shows_opponent_checkbox_and_conditions(self) -> None:
        conn = connect(self.db_path)
        try:
            categories = repo.list_categories_by_template(conn, self.template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            action_id = int(
                repo.list_actions_by_category(conn, int(handling["Id"]))[0]["Id"]
            )
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_UI", action_id, "Success", "own"
            )
            repo.create_team_stat_condition(
                conn, metric_id, action_id, "Failure", "opponent"
            )
        finally:
            conn.close()
        resp = self.client.get(f"/directories/templates/{self.template_id}/stat-metrics")
        html = resp.get_data(as_text=True)
        self.assertIn("Учитывать события противника", html)
        self.assertIn("TEST_UI", html)
        self.assertIn('name="countOpponent"', html)
        self.assertIn("conditions/create", html)
```

Update `test_stat_metrics_page_renders_create_form` — remove assertion on inline metric `actionId` edit; keep create form fields.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests.test_stat_metrics_page_shows_opponent_checkbox_and_conditions -v`

Expected: FAIL — checkbox label or condition routes absent in HTML.

- [ ] **Step 3: Write minimal implementation**

Replace `templates/templates/stat_metrics.html` body with grouped layout:

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
    <label>
      <input type="checkbox" name="countOpponent" value="1" />
      Учитывать события противника
    </label>
    <button class="btn btn-primary" type="submit">Добавить</button>
  </form>
</div>

<div class="card">
  {% for m in metrics %}
  <div class="stat-metric-block">
    <form class="form-row" method="post" action="{{ url_for('template_stat_metrics_update', template_id=template.Id, metric_id=m.Id) }}">
      <strong>{{ m.Name }}</strong>
      <input name="name" value="{{ m.Name }}" />
      <button class="btn btn-primary" type="submit">Переименовать</button>
    </form>
    <form method="post" action="{{ url_for('template_stat_metrics_move_up', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
      <button class="btn" type="submit">↑</button>
    </form>
    <form method="post" action="{{ url_for('template_stat_metrics_move_down', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
      <button class="btn" type="submit">↓</button>
    </form>
    <form method="post" action="{{ url_for('template_stat_metrics_delete', template_id=template.Id, metric_id=m.Id) }}" style="display:inline;">
      <button class="btn btn-danger" type="submit">Удалить метрику</button>
    </form>

    <h4>Условия</h4>
    {% set conditions = metric_conditions.get(m.Id, []) %}
    {% for c in conditions %}
    <form class="form-row" method="post" action="{{ url_for('template_stat_metrics_condition_update', template_id=template.Id, metric_id=m.Id, condition_id=c.Id) }}">
      <select name="actionId">
        {% for action in actions %}
        <option value="{{ action.Id }}" {% if action.Id == c.ActionId %}selected{% endif %}>{{ action.Name }}</option>
        {% endfor %}
      </select>
      <select name="outcomeFilter">
        <option value="any" {% if c.OutcomeFilter == 'any' %}selected{% endif %}>Любой</option>
        <option value="Success" {% if c.OutcomeFilter == 'Success' %}selected{% endif %}>Успех</option>
        <option value="Failure" {% if c.OutcomeFilter == 'Failure' %}selected{% endif %}>Неудача</option>
      </select>
      <label>
        <input type="checkbox" name="countOpponent" value="1" {% if c.Perspective == 'opponent' %}checked{% endif %} />
        Учитывать события противника
      </label>
      <button class="btn btn-primary" type="submit">Сохранить</button>
    </form>
    <form method="post" action="{{ url_for('template_stat_metrics_condition_delete', template_id=template.Id, metric_id=m.Id, condition_id=c.Id) }}" style="display:inline;">
      <button class="btn btn-danger" type="submit">Удалить условие</button>
    </form>
    {% endfor %}

    <form class="form-row" method="post" action="{{ url_for('template_stat_metrics_condition_create', template_id=template.Id, metric_id=m.Id) }}">
      <select name="actionId" required>
        <option value="">Добавить условие — действие</option>
        {% for action in actions %}
        <option value="{{ action.Id }}">{{ action.Name }}</option>
        {% endfor %}
      </select>
      <select name="outcomeFilter">
        <option value="any">Любой исход</option>
        <option value="Success">Успех</option>
        <option value="Failure">Неудача</option>
      </select>
      <label>
        <input type="checkbox" name="countOpponent" value="1" />
        Учитывать события противника
      </label>
      <button class="btn" type="submit">Добавить условие</button>
    </form>
  </div>
  {% else %}
  <p>Метрики не настроены.</p>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_match_statistics_page.StatMetricsConstructorPageTests -v`

Expected: PASS (all constructor page tests)

- [ ] **Step 5: Commit**

```bash
git add templates/templates/stat_metrics.html tests/test_match_statistics_page.py
git commit -m "feat: show composite conditions in stat metrics constructor"
```

---

### Task 9: Match statistics page regression and empty-metrics cleanup

**Files:**
- Modify: `tests/test_match_statistics_page.py` — update create calls; fix empty-metrics test DELETE
- No template changes (layout unchanged per spec)

**Interfaces:**
- Consumes: composite aggregation (Task 5)

- [ ] **Step 1: Write the failing test**

Update `MatchStatisticsPageTests.setUp`:

```python
            repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Pass OK", self.action_id, "Success", "own"
            )
```

Update `test_empty_metrics_shows_message` to delete conditions first (FK cascade) or delete metrics:

```python
    def test_empty_metrics_shows_message(self) -> None:
        conn = connect(self.db_path)
        try:
            conn.execute("DELETE FROM TeamStatMetricCondition")
            conn.execute("DELETE FROM TeamStatMetric")
            conn.commit()
        finally:
            conn.close()
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        html = resp.get_data(as_text=True)
        self.assertIn("match-score", html)
        self.assertIn("Метрики не настроены", html)
```

Add composite page smoke test:

```python
    def test_statistics_page_reflects_composite_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            conn.execute("DELETE FROM TeamStatMetricCondition")
            conn.execute("DELETE FROM TeamStatMetric")
            categories = repo.list_categories_by_template(conn, self.template_id)
            setpiece = next(c for c in categories if c["Name"] == "Set-piece")
            scrum_id = int(
                next(
                    a["Id"]
                    for a in repo.list_actions_by_category(conn, int(setpiece["Id"]))
                    if a["Name"] == "Scrum (own)"
                )
            )
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Scrums won page", scrum_id, "Success", "own"
            )
            repo.create_team_stat_condition(conn, metric_id, scrum_id, "Failure", "opponent")
            away_player = repo.create_player(conn, self.away_id, "TEST_AwayPlayer", None)
            repo.add_match_lineup_row(
                conn, self.match_id, self.away_id, away_player, None, "starter", 1
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=scrum_id, outcome="Success",
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=away_player, action_id=scrum_id, outcome="Failure",
            )
        finally:
            conn.close()
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        html = resp.get_data(as_text=True)
        self.assertIn("TEST_Scrums won page", html)
        self.assertRegex(
            html,
            r'match-statistics__value[^>]*>\s*2\s*</td>\s*'
            r'<td[^>]*match-statistics__name[^>]*>\s*TEST_Scrums won page\s*</td>\s*'
            r'<td[^>]*match-statistics__value[^>]*>\s*0\s*</td>',
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests.test_statistics_page_reflects_composite_metric -v`

Expected: FAIL until Tasks 5–8 complete; FAIL on setUp if old create signature used.

- [ ] **Step 3: Fix test setup only (no production code)**

Apply setUp and empty-metrics fixes above; ensure `self.away_id` exists in setUp (add `self.away_id = repo.create_team(conn, "TEST_Away")` if missing).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_match_statistics_page.MatchStatisticsPageTests -v`

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_match_statistics_page.py
git commit -m "test: cover composite metrics on statistics page"
```

---

### Task 10: Full test suite and documentation

**Files:**
- Modify: `docs/development-context.md`
- Test: full suite

- [ ] **Step 1: Run full isolated test suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS

- [ ] **Step 2: Update development-context.md**

Replace the team-statistics row in the data model table:

```markdown
| Командная статистика матча | Метрики шаблона (`TeamStatMetric` + `TeamStatMetricCondition`: Action, OutcomeFilter, perspective `own`/`opponent`; значение = сумма условий); атрибуция игроков через `MatchLineup`; `/reports` без изменений |
```

Update constructor route description:

```markdown
| `/directories/templates/<id>/stat-metrics` | Конструктор командных метрик (↑/↓ метрик; CRUD условий; чекбокс «Учитывать события противника») |
```

- [ ] **Step 3: Commit**

```bash
git add docs/development-context.md
git commit -m "docs: document composite team stat metric semantics"
```

---

## Self-Review Checklist

| Spec requirement | Task |
|------------------|------|
| `TeamStatMetricCondition` table + slim parent | Task 1 |
| Legacy migration to one `own` condition | Task 2 |
| Create metric with first condition | Task 3 |
| Condition list/create/update/delete | Task 4 |
| Last condition delete removes parent metric | Task 4 |
| Own/opponent aggregation, additive overlap | Task 5 |
| Scrums-won composition | Task 5 |
| Zeros, orphans, transfer stability | Task 5 (retained tests) |
| Action delete cascades conditions; empty metric removed | Task 6 |
| Partial cascade keeps composite metric | Task 6 |
| Constructor opponent checkbox (Russian label) | Tasks 7–8 |
| Condition insertion order, no condition ↑/↓ | Tasks 4, 8 |
| Metric ↑/↓ unchanged | Task 8 (existing routes) |
| Match statistics layout unchanged | Task 9 |
| Isolated TEST_ tests, not production DB | All test tasks |
| SQL only in repository.py | Global constraint |
| docs/schema.sql + backend/db.py sync | Tasks 1–2 |

**Placeholder scan:** none — all steps include concrete code, paths, and commands.

**Type consistency:** `create_team_stat_metric(..., perspective)` and `get_match_team_stat_counts` return shape unchanged for templates/routes; condition helpers use consistent `Perspective` column name throughout.
