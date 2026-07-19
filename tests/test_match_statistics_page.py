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
            categories = repo.list_categories_by_template(conn, self.template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            self.action_id = int(
                repo.list_actions_by_category(conn, int(handling["Id"]))[0]["Id"]
            )
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
        self.assertIn('name="actionId"', html)
        self.assertIn('name="outcomeFilter"', html)

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

    def test_each_metric_has_card_header_and_grouped_conditions(self) -> None:
        conn = connect(self.db_path)
        try:
            for metric in repo.list_team_stat_metrics(conn, self.template_id):
                repo.delete_team_stat_metric(conn, int(metric["Id"]))
            repo.create_team_stat_metric(
                conn, self.template_id, "TEST_First card", self.action_id, "any", "own"
            )
            repo.create_team_stat_metric(
                conn, self.template_id, "TEST_Second card", self.action_id, "any", "own"
            )
        finally:
            conn.close()

        resp = self.client.get(f"/directories/templates/{self.template_id}/stat-metrics")
        html = resp.get_data(as_text=True)
        card_marker = '<div class="stat-metric-card">'
        card_starts = []
        search_from = 0
        while (start := html.find(card_marker, search_from)) != -1:
            card_starts.append(start)
            search_from = start + len(card_marker)
        self.assertEqual(len(card_starts), 2)
        card_ends = card_starts[1:] + [len(html)]
        for metric_name, start, end in zip(
            ("TEST_First card", "TEST_Second card"), card_starts, card_ends
        ):
            card_html = html[start:end]
            self.assertRegex(
                card_html,
                rf'<h2 class="stat-metric-title">\s*{metric_name}\s*</h2>',
            )
            self.assertIn('<div class="stat-conditions">', card_html)

    def test_template_detail_links_to_stat_metrics(self) -> None:
        resp = self.client.get(f"/directories/templates/{self.template_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("/stat-metrics", html)
        self.assertIn("Командные метрики", html)

    def test_create_metric_with_opponent_checkbox(self) -> None:
        resp = self.client.post(
            f"/directories/templates/{self.template_id}/stat-metrics/create",
            data={
                "name": "TEST_OpponentMetric",
                "actionId": str(self.action_id),
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
                conn, self.template_id, "TEST_Pass OK", self.action_id, "Success", "own"
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

    def test_statistics_page_shows_tournament_centered_before_score_when_available(self) -> None:
        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        html = resp.get_data(as_text=True)
        self.assertNotIn("match-statistics__tournament", html)

        conn = connect(self.db_path)
        try:
            repo.update_match_details(conn, self.match_id, "2026-01-15", "TEST_Cup")
        finally:
            conn.close()

        resp = self.client.get(f"/matches/{self.match_id}/statistics")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        tournament_heading = (
            '<h2 class="match-statistics__tournament">TEST_Cup</h2>'
        )
        self.assertIn(tournament_heading, html)
        self.assertLess(html.index(tournament_heading), html.index('<div class="match-score">'))

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

    def test_matches_list_has_statistics_link(self) -> None:
        resp = self.client.get("/matches")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn(f"/matches/{self.match_id}/statistics", html)
        self.assertIn("Статистика", html)

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


if __name__ == "__main__":
    unittest.main()
