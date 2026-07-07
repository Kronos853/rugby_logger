from __future__ import annotations

import sqlite3

from . import repository as repo


def _latinize_homoglyphs(text: str) -> str:
    mapping = {
        "а": "a",
        "Ӑ": "a",
        "в": "b",
        "с": "c",
        "е": "e",
        "ё": "e",
        "н": "h",
        "к": "k",
        "м": "m",
        "о": "o",
        "п": "p",
        "р": "p",
        "т": "t",
        "х": "x",
        "у": "y",
        "і": "i",
        "ї": "i",
    }
    return "".join(mapping.get(ch, ch) for ch in text.strip().lower())


def get_scoring_points(action_name: str, outcome: str | None) -> int:
    normalized_action = _latinize_homoglyphs(action_name)
    normalized_outcome = (outcome or "").strip().lower()
    if normalized_action == "try":
        return 5
    if normalized_action.startswith("conversion"):
        return 0 if normalized_outcome == "failure" else 2
    return 0


def calculate_match_score_for_match(conn: sqlite3.Connection, match_id: int) -> dict[str, int]:
    match = repo.get_match(conn, match_id)
    if not match:
        return {"home": 0, "away": 0}

    lineups = repo.list_match_lineup(conn, match_id)
    players = repo.list_players(conn)
    events = repo.list_events_by_match(conn, match_id)
    player_to_lineup_team = {int(row["PlayerId"]): int(row["TeamId"]) for row in lineups}
    player_to_team = {int(row["Id"]): int(row["TeamId"]) for row in players}
    actions_cache: dict[int, sqlite3.Row | None] = {}

    home_team = int(match["HomeTeamId"])
    away_team = int(match["AwayTeamId"])
    score = {"home": 0, "away": 0}

    for event in events:
        action_id = event["ActionId"]
        if action_id is None:
            continue
        action_id_int = int(action_id)
        if action_id_int not in actions_cache:
            actions_cache[action_id_int] = repo.get_action(conn, action_id_int)
        action = actions_cache[action_id_int]
        if not action:
            continue
        points = get_scoring_points(str(action["Name"]), event["Outcome"])
        if points <= 0:
            continue

        team_id: int | None = None
        if event["TeamId"] is not None:
            candidate = int(event["TeamId"])
            if candidate in (home_team, away_team):
                team_id = candidate
        if team_id is None and event["PlayerId"] is not None:
            player_id = int(event["PlayerId"])
            team_id = player_to_lineup_team.get(player_id) or player_to_team.get(player_id)
            if team_id not in (home_team, away_team):
                team_id = None

        if team_id == home_team:
            score["home"] += points
        elif team_id == away_team:
            score["away"] += points

    return score

