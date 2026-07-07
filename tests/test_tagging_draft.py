from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend import repository as repo
from backend.db import connect
from backend.seed import ensure_seeded


class TaggingDraftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = Path(self._tmp.name)
        os.environ["SPORTS_LOGGER_DB"] = str(self.db_path)

        from backend.app import create_app

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.match_id, self.player_id, self.action_ids = self._seed_data()

    def tearDown(self) -> None:
        self.app = None
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _seed_data(self) -> tuple[int, int, list[int]]:
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
            tackle_cat = next(c for c in categories if c["Name"] == "Tackle")
            handling_actions = repo.list_actions_by_category(conn, int(handling["Id"]))
            tackle_actions = repo.list_actions_by_category(conn, int(tackle_cat["Id"]))
            pass_id = int(handling_actions[0]["Id"])
            tackle_id = int(tackle_actions[0]["Id"])
            repo.create_event(
                conn,
                match_id,
                1,
                120,
                "player",
                player_id=player_id,
                action_id=pass_id,
                outcome="Success",
            )
            repo.create_event(
                conn,
                match_id,
                1,
                180,
                "player",
                player_id=player_id,
                action_id=tackle_id,
            )
            return match_id, player_id, [pass_id, tackle_id]
        finally:
            conn.close()

    def test_control_shows_current_event_draft_block(self) -> None:
        resp = self.client.get(f"/tagging/{self.match_id}/control")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("ТЕКУЩЕЕ СОБЫТИЕ", html)
        self.assertIn("current-event-draft", html)
        self.assertNotIn("Нажмите «НОВОЕ СОБЫТИЕ»", html)
        self.assertNotIn("Сначала зафиксируйте время события", html)

    def test_capture_shows_new_badge(self) -> None:
        resp = self.client.post(
            f"/tagging/{self.match_id}/capture",
            data={"timestampSec": "367", "period": "2"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("НОВОЕ", html)
        self.assertIn("Тайм: 2 • 6-07", html)

    def test_timeline_select_shows_edit_badge(self) -> None:
        conn = connect(self.db_path)
        try:
            events = repo.list_events_by_match(conn, self.match_id)
            event_id = int(events[0]["Id"])
        finally:
            conn.close()
        resp = self.client.post(
            f"/tagging/{self.match_id}/event/{event_id}/select",
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("РЕДАКТИРОВАНИЕ", html)
        self.assertIn("TEST_Player", html)


if __name__ == "__main__":
    unittest.main()
