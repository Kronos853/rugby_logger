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


if __name__ == "__main__":
    unittest.main()
