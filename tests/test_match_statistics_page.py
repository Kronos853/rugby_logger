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


if __name__ == "__main__":
    unittest.main()
