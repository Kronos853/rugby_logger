from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend import repository as repo
from backend.db import connect
from backend.seed import ensure_seeded


class ReportsSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        os.environ["SPORTS_LOGGER_DB"] = str(self.db_path)

        from backend.app import create_app

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.team_id, self.player_id, self.action_id = self._seed_data()

    def tearDown(self) -> None:
        self.app = None
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _seed_data(self) -> tuple[int, int, int]:
        conn = connect(self.db_path)
        try:
            ensure_seeded(conn)
            template = repo.get_sport_template_by_name(conn, "Регби-7")
            assert template is not None
            template_id = int(template["Id"])
            home_id = repo.create_team(conn, "TEST_Home")
            away_id = repo.create_team(conn, "TEST_Away")
            player_id = repo.create_player(conn, home_id, "TEST_Player", None)
            match_id = repo.create_match(
                conn, template_id, home_id, away_id, "2026-01-15", None, None, None
            )
            categories = repo.list_categories_by_template(conn, template_id)
            handling = next(c for c in categories if c["Name"] == "Handling")
            actions = repo.list_actions_by_category(conn, int(handling["Id"]))
            action_id = int(actions[0]["Id"])
            repo.create_event(
                conn,
                match_id,
                1,
                0,
                "player",
                player_id=player_id,
                action_id=action_id,
                outcome="Success",
            )
            return home_id, player_id, action_id
        finally:
            conn.close()

    def test_team_report_renders_split_layout(self) -> None:
        resp = self.client.post(
            "/reports",
            data={
                "reportType": "team",
                "teamId": str(self.team_id),
                "dateFrom": "2026-01-01",
                "dateTo": "2026-12-31",
            },
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("report-split", html)
        self.assertIn("Отчёт команды", html)
        self.assertIn("Панель игрока", html)
        self.assertIn("Выберите действие", html)

    def test_individual_report_without_split(self) -> None:
        resp = self.client.post(
            "/reports",
            data={
                "reportType": "individual",
                "playerId": str(self.player_id),
                "dateFrom": "2026-01-01",
                "dateTo": "2026-12-31",
            },
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertNotIn("report-split", html)
        self.assertIn("Результаты", html)

    def test_player_panel_action_breakdown(self) -> None:
        resp = self.client.get(
            "/reports/player-panel",
            query_string={
                "mode": "action-breakdown",
                "actionId": self.action_id,
                "teamId": self.team_id,
                "dateFrom": "2026-01-01",
                "dateTo": "2026-12-31",
            },
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("TEST_Player", html)
        self.assertIn("report-player-table", html)

    def test_player_breakdown_sorted_by_total_desc(self) -> None:
        conn = connect(self.db_path)
        try:
            match_row = conn.execute(
                "SELECT MatchId FROM Event WHERE PlayerId = ? LIMIT 1",
                (self.player_id,),
            ).fetchone()
            assert match_row is not None
            match_id = int(match_row["MatchId"])
            top_id = repo.create_player(conn, self.team_id, "TEST_Zulu", None)
            low_id = repo.create_player(conn, self.team_id, "TEST_Alpha", None)
            for _ in range(3):
                repo.create_event(
                    conn,
                    match_id,
                    1,
                    0,
                    "player",
                    player_id=top_id,
                    action_id=self.action_id,
                    outcome="Success",
                )
            repo.create_event(
                conn,
                match_id,
                1,
                0,
                "player",
                player_id=low_id,
                action_id=self.action_id,
                outcome="Success",
            )
        finally:
            conn.close()

        resp = self.client.get(
            "/reports/player-panel",
            query_string={
                "mode": "action-breakdown",
                "actionId": self.action_id,
                "teamId": self.team_id,
                "dateFrom": "2026-01-01",
                "dateTo": "2026-12-31",
            },
        )
        html = resp.get_data(as_text=True)
        zulu_pos = html.index("TEST_Zulu")
        alpha_pos = html.index("TEST_Alpha")
        player_pos = html.index("TEST_Player")
        self.assertLess(zulu_pos, alpha_pos)
        self.assertLess(zulu_pos, player_pos)

    def test_player_breakdown_tie_sorted_by_name(self) -> None:
        conn = connect(self.db_path)
        try:
            match_row = conn.execute(
                "SELECT MatchId FROM Event WHERE PlayerId = ? LIMIT 1",
                (self.player_id,),
            ).fetchone()
            assert match_row is not None
            match_id = int(match_row["MatchId"])
            conn.execute("DELETE FROM Event")
            beta_id = repo.create_player(conn, self.team_id, "TEST_Beta", None)
            alpha_id = repo.create_player(conn, self.team_id, "TEST_Alpha", None)
            for player_id in (beta_id, alpha_id):
                for _ in range(2):
                    repo.create_event(
                        conn,
                        match_id,
                        1,
                        0,
                        "player",
                        player_id=player_id,
                        action_id=self.action_id,
                        outcome="Success",
                    )
        finally:
            conn.close()

        resp = self.client.get(
            "/reports/player-panel",
            query_string={
                "mode": "action-breakdown",
                "actionId": self.action_id,
                "teamId": self.team_id,
                "dateFrom": "2026-01-01",
                "dateTo": "2026-12-31",
            },
        )
        html = resp.get_data(as_text=True)
        self.assertLess(html.index("TEST_Alpha"), html.index("TEST_Beta"))


if __name__ == "__main__":
    unittest.main()
