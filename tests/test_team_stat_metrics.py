from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend.db import connect, ensure_db


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


if __name__ == "__main__":
    unittest.main()
