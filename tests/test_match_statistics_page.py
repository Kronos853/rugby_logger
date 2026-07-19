from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend import repository as repo
from backend.db import connect
from backend.seed import ensure_seeded


class StatMetricsConstructorPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        os.environ["SPORTS_LOGGER_DB"] = str(self.db_path)

        from backend.app import create_app

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        conn = connect(self.db_path)
        try:
            ensure_seeded(conn)
            template = repo.get_sport_template_by_name(conn, "Регби-7")
            assert template is not None
            self.template_id = int(template["Id"])
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.app = None
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_stat_metrics_page_renders_create_form(self) -> None:
        resp = self.client.get(f"/directories/templates/{self.template_id}/stat-metrics")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Командные метрики", html)
        self.assertIn('name="outcomeFilter"', html)

    def test_template_detail_links_to_stat_metrics(self) -> None:
        resp = self.client.get(f"/directories/templates/{self.template_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("/stat-metrics", html)
        self.assertIn("Командные метрики", html)


class MatchStatisticsPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        os.environ["SPORTS_LOGGER_DB"] = str(self.db_path)

        from backend.app import create_app

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

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
            self.action_id = int(
                repo.list_actions_by_category(conn, int(handling["Id"]))[0]["Id"]
            )
            repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Pass OK", self.action_id, "Success"
            )
            repo.create_event(
                conn, self.match_id, 1, 0, "player",
                player_id=self.player_home, action_id=self.action_id, outcome="Success",
            )
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.app = None
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_statistics_page_shows_score_and_counts(self) -> None:
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("match-score", html)
        self.assertIn("TEST_Pass OK", html)
        self.assertIn("match-statistics", html)
        self.assertNotIn("Разметка", html)
        self.assertNotIn(">Метрика<", html)
        self.assertNotIn(">Значение<", html)
        self.assertEqual(html.count("TEST_Home"), 1)
        self.assertEqual(html.count("TEST_Away"), 1)
        self.assertRegex(
            html,
            r'<colgroup>\s*'
            r'<col class="match-statistics__team-column"\s*/>\s*'
            r'<col class="match-statistics__metric-column"\s*/>\s*'
            r'<col class="match-statistics__team-column"\s*/>\s*'
            r'</colgroup>',
        )
        # One comparison row: home value | metric name | away value
        self.assertRegex(
            html,
            r'match-statistics__value[^>]*>\s*1\s*</td>\s*'
            r'<td[^>]*match-statistics__name[^>]*>\s*TEST_Pass OK\s*</td>\s*'
            r'<td[^>]*match-statistics__value[^>]*>\s*0\s*</td>',
        )

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

    def test_matches_list_has_statistics_link(self) -> None:
        resp = self.client.get("/matches")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn(f"/matches/{self.match_id}/statistics", html)
        self.assertIn("Статистика", html)


if __name__ == "__main__":
    unittest.main()
