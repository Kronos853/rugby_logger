from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend import repository as repo
from backend.db import connect
from backend.seed import ensure_seeded

HX_HEADERS = {"HX-Request": "true"}


class TaggingHtmxTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        os.environ["SPORTS_LOGGER_DB"] = str(self.db_path)

        from backend.app import create_app

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.match_id, self.player_id, self.action_id = self._seed_data()

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
            handling_actions = repo.list_actions_by_category(conn, int(handling["Id"]))
            action_id = int(handling_actions[0]["Id"])
            return match_id, player_id, action_id
        finally:
            conn.close()

    def test_capture_htmx_returns_input_and_timeline_oob(self) -> None:
        resp = self.client.post(
            f"/tagging/{self.match_id}/capture",
            data={"timestampSec": "120", "period": "1"},
            headers=HX_HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("ТЕКУЩЕЕ СОБЫТИЕ", html)
        self.assertIn('id="tagging-timeline-col"', html)
        self.assertIn('hx-swap-oob="innerHTML"', html)
        self.assertIn("timeline-panel", html)
        self.assertIn('data-target="player"', html)

    def test_update_player_htmx_returns_selection_state(self) -> None:
        self.client.post(
            f"/tagging/{self.match_id}/capture",
            data={"timestampSec": "100", "period": "1"},
            headers=HX_HEADERS,
        )
        resp = self.client.post(
            f"/tagging/{self.match_id}/event/update",
            data={"subjectType": "player", "playerId": str(self.player_id)},
            headers=HX_HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("TEST_Player", html)
        self.assertIn("selected", html)
        self.assertIn("[Игрок: TEST_Player]", html)
        self.assertIn('data-target="action"', html)

    def test_capture_without_htmx_redirects(self) -> None:
        resp = self.client.post(
            f"/tagging/{self.match_id}/capture",
            data={"timestampSec": "50", "period": "1"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/control", resp.headers.get("Location", ""))

    def test_set_period_htmx_returns_partial(self) -> None:
        self.client.post(
            f"/tagging/{self.match_id}/capture",
            data={"timestampSec": "10", "period": "1"},
            headers=HX_HEADERS,
        )
        resp = self.client.post(
            f"/tagging/{self.match_id}/set-period",
            data={"period": "2"},
            headers=HX_HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('id="tagging-timeline-col"', html)
        self.assertIn("ТЕКУЩЕЕ СОБЫТИЕ", html)
        self.assertNotIn("302", html)


if __name__ == "__main__":
    unittest.main()
