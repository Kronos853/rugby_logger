from __future__ import annotations

import csv
import io
import re
import sqlite3
from urllib.parse import quote

from . import repository as repo

CSV_HEADERS = ["Тайм", "Время", "Игрок/Команда", "Категория", "Действие", "Результат", "Комментарий"]


def _sanitize_filename(name: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name).strip().strip(".")
    return sanitized or "match_export"


def build_export_filename(conn: sqlite3.Connection, match_id: int) -> str:
    match = repo.get_match(conn, match_id)
    if not match:
        return "match_export.csv"

    home = repo.get_team(conn, int(match["HomeTeamId"]))
    away = repo.get_team(conn, int(match["AwayTeamId"]))
    home_name = str(home["Name"]) if home else "home"
    away_name = str(away["Name"]) if away else "away"
    tournament = (match["TournamentName"] or "").strip()

    parts = [f"{home_name} vs {away_name}"]
    if tournament:
        parts.append(tournament)
    return _sanitize_filename(" - ".join(parts)) + ".csv"


def export_content_disposition(filename: str) -> str:
    try:
        filename.encode("ascii")
        return f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        fallback = "match_export.csv"
        return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"


def build_csv(conn: sqlite3.Connection, match_id: int) -> str:
    events = repo.list_events_by_match(conn, match_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADERS)

    for event in events:
        action = repo.get_action(conn, int(event["ActionId"])) if event["ActionId"] else None
        category = repo.get_category(conn, int(action["CategoryId"])) if action else None
        subject = ""
        if event["SubjectType"] == "player" and event["PlayerId"]:
            player = repo.get_player(conn, int(event["PlayerId"]))
            subject = player["Name"] if player else ""
        elif event["SubjectType"] == "team" and event["TeamId"]:
            team = repo.get_team(conn, int(event["TeamId"]))
            subject = team["Name"] if team else ""

        writer.writerow(
            [
                event["PeriodNumber"],
                event["TimestampSec"],
                subject,
                category["Name"] if category else "",
                action["Name"] if action else "",
                event["Outcome"] or "",
                event["Comment"] or "",
            ]
        )

    return "\ufeff" + output.getvalue()

