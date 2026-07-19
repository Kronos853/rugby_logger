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
            other_action_id = repo.create_action(
                conn, other_cat_id, "TEST_Action", True, 0, "handling"
            )
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


if __name__ == "__main__":
    unittest.main()
