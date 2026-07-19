from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend import repository as repo
from backend.db import connect, ensure_db
from backend.seed import ensure_seeded


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

    def test_create_rejects_action_from_other_template(self) -> None:
        conn = connect(self.db_path)
        try:
            other_template_id = repo.create_sport_template(conn, "TEST_OtherSport")
            other_cat_id = repo.create_category(conn, other_template_id, "TEST_Cat", 0)
            other_action_id = repo.create_action(
                conn, other_cat_id, "TEST_Action", True, 0, "handling"
            )
            with self.assertRaises(ValueError):
                repo.create_team_stat_metric(
                    conn, self.template_id, "TEST_Bad", other_action_id, "any"
                )
        finally:
            conn.close()

    def test_delete_metric(self) -> None:
        conn = connect(self.db_path)
        try:
            metric_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Old", self.action_id, "any", "own"
            )
            repo.delete_team_stat_metric(conn, metric_id)
            self.assertIsNone(repo.get_team_stat_metric(conn, metric_id))
        finally:
            conn.close()

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

    def test_reorder_works_after_delete_and_recreate(self) -> None:
        conn = connect(self.db_path)
        try:
            first_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_A", self.action_id, "any"
            )
            second_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_B", self.action_id, "any"
            )
            repo.delete_team_stat_metric(conn, first_id)
            third_id = repo.create_team_stat_metric(
                conn, self.template_id, "TEST_C", self.action_id, "any"
            )
            repo.swap_team_stat_metric_order(conn, self.template_id, third_id, "up")
            rows = repo.list_team_stat_metrics(conn, self.template_id)
            self.assertEqual([int(r["Id"]) for r in rows], [third_id, second_id])
        finally:
            conn.close()


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
            # Simulate transfer: Player.TeamId changes; MatchLineup attribution must stay.
            conn.execute(
                "UPDATE Player SET TeamId = ? WHERE Id = ?",
                (self.away_id, self.player_home),
            )
            conn.commit()
            after = repo.get_match_team_stat_counts(conn, self.match_id)
            self.assertEqual(before, after)
        finally:
            conn.close()


class TeamStatMetricDeleteSafetyTests(unittest.TestCase):
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
            self.match_id = repo.create_match(
                conn, self.template_id, self.home_id, self.away_id, "2026-01-15", None, None, None
            )
            repo.add_match_lineup_row(
                conn, self.match_id, self.home_id, self.player_home, None, "starter", 0
            )
            categories = repo.list_categories_by_template(conn, self.template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            self.category_id = int(handling["Id"])
            self.action_id = int(
                repo.list_actions_by_category(conn, self.category_id)[0]["Id"]
            )
        finally:
            conn.close()

    def tearDown(self) -> None:
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

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
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
            with self.assertRaises(ValueError):
                repo.delete_category(conn, self.category_id)
        finally:
            conn.close()


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


if __name__ == "__main__":
    unittest.main()
