from __future__ import annotations

import csv
import io
import sqlite3

from . import repository as repo
from .format_time import parse_timestamp

EXPORT_HEADERS = ["Тайм", "Время", "Игрок/Команда", "Категория", "Действие", "Результат", "Комментарий"]
LEGACY_HEADERS = ["Match_ID", "Half", "Time_stamp", "Player_ID", "Event_Category", "Event", "Outcome"]

# Legacy HTML panel names -> names in DB (category, action).
LEGACY_ACTION_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    ("handling", "iinebreak"): ("Offence", "Linebreak"),
    ("offence", "iinebreak"): ("Offence", "Linebreak"),
    ("set-piece", "kick-off (receive)"): ("Set-piece", "Kick-off recieve"),
    ("discipline", "penalty (other)"): ("Discipline", "Penalty"),
    ("discipline", "penalty (ruck)"): ("Discipline", "Penalty"),
    ("discipline", "penalty (offside)"): ("Discipline", "Penalty"),
    ("discipline", "penalty (high tackle)"): ("Discipline", "Penalty"),
    ("discipline", "penalty (opponent)"): ("Discipline", "Penalty"),
    ("handling", "offload"): ("Handling", "Pass"),
    ("kicking", "conversion (opp)"): ("Kicking", "Conversion"),
    ("offence", "try"): ("Offence", "Try"),
}


def _norm(text: str) -> str:
    return text.strip().lower()


def _is_placeholder(value: str) -> bool:
    normalized = _norm(value)
    return normalized in {"", "не указан", "не указано", "-", "—"}


def _optional_text(value: str) -> str | None:
    return None if _is_placeholder(value) else (value or None)


def _detect_format(fieldnames: list[str] | None) -> str | None:
    if not fieldnames:
        return None
    normalized = [h.strip() for h in fieldnames]
    if normalized == EXPORT_HEADERS:
        return "export"
    if normalized == LEGACY_HEADERS:
        return "legacy"
    lowered = {_norm(name) for name in normalized}
    if {"match_id", "half", "time_stamp", "player_id", "event_category", "event"}.issubset(lowered):
        return "legacy"
    return None


def _resolve_action(
    action_map: dict[tuple[str, str], sqlite3.Row],
    category_raw: str,
    action_raw: str,
) -> sqlite3.Row | None:
    key = (_norm(category_raw), _norm(action_raw))
    alias = LEGACY_ACTION_ALIASES.get(key)
    if alias:
        category_raw, action_raw = alias
    return action_map.get((_norm(category_raw), _norm(action_raw)))


def _build_lookup_context(
    conn: sqlite3.Connection,
    match_id: int,
) -> tuple[sqlite3.Row, dict[tuple[str, str], sqlite3.Row], dict[str, sqlite3.Row], dict[str, sqlite3.Row]] | None:
    match = repo.get_match(conn, match_id)
    if not match:
        return None

    players = repo.list_players(conn)
    lineups = repo.list_match_lineup(conn, match_id)
    home_team = repo.get_team(conn, int(match["HomeTeamId"]))
    away_team = repo.get_team(conn, int(match["AwayTeamId"]))
    categories = repo.list_categories_by_template(conn, int(match["SportTemplateId"]))
    action_map: dict[tuple[str, str], sqlite3.Row] = {}

    for category in categories:
        actions = repo.list_actions_by_category(conn, int(category["Id"]))
        for action in actions:
            action_map[(_norm(str(category["Name"])), _norm(str(action["Name"])))] = action

    lineup_player_ids = {int(row["PlayerId"]) for row in lineups}
    player_lookup: dict[str, sqlite3.Row] = {}
    for player in players:
        if int(player["Id"]) in lineup_player_ids or int(player["TeamId"]) in (
            int(match["HomeTeamId"]),
            int(match["AwayTeamId"]),
        ):
            player_lookup[_norm(str(player["Name"]))] = player

    team_lookup: dict[str, sqlite3.Row] = {}
    if home_team:
        team_lookup[_norm(str(home_team["Name"]))] = home_team
        team_lookup["команда"] = home_team
    if away_team:
        team_lookup[_norm(str(away_team["Name"]))] = away_team
        team_lookup["соперник"] = away_team

    return match, action_map, player_lookup, team_lookup


def _prepare_event(
    *,
    idx: int,
    period: int,
    time_sec: int,
    subject_raw: str,
    category_raw: str,
    action_raw: str,
    outcome_raw: str,
    comment_raw: str,
    action_map: dict[tuple[str, str], sqlite3.Row],
    player_lookup: dict[str, sqlite3.Row],
    team_lookup: dict[str, sqlite3.Row],
    errors: list[str],
) -> dict[str, object | None] | None:
    if period not in (1, 2):
        errors.append(f"Строка {idx}: тайм должен быть 1 или 2.")
        return None

    action_id: int | None = None
    if not _is_placeholder(category_raw) and not _is_placeholder(action_raw):
        action = _resolve_action(action_map, category_raw, action_raw)
        if not action:
            errors.append(
                f"Строка {idx}: действие '{action_raw}' в категории '{category_raw}' не найдено в шаблоне матча."
            )
            return None
        action_id = int(action["Id"])

    player_id: int | None = None
    team_id: int | None = None
    subject_type = "player"
    if _is_placeholder(subject_raw):
        pass
    else:
        player = player_lookup.get(_norm(subject_raw))
        team = team_lookup.get(_norm(subject_raw))
        if not player and not team:
            errors.append(f"Строка {idx}: субъект '{subject_raw}' не найден среди игроков/команд матча.")
            return None
        subject_type = "player" if player else "team"
        player_id = int(player["Id"]) if player else None
        team_id = int(team["Id"]) if team else None

    return {
        "period": period,
        "time": time_sec,
        "subject_type": subject_type,
        "player_id": player_id,
        "team_id": team_id,
        "action_id": action_id,
        "outcome": _optional_text(outcome_raw),
        "comment": _optional_text(comment_raw),
    }


def _parse_export_rows(
    reader: csv.DictReader,
    match_id: int,
    action_map: dict[tuple[str, str], sqlite3.Row],
    player_lookup: dict[str, sqlite3.Row],
    team_lookup: dict[str, sqlite3.Row],
) -> tuple[list[dict[str, object | None]], list[str]]:
    prepared: list[dict[str, object | None]] = []
    errors: list[str] = []

    for idx, row in enumerate(reader, start=2):
        try:
            period = int((row.get("Тайм") or "").strip())
            time_sec = parse_timestamp((row.get("Время") or "").strip())
        except ValueError:
            errors.append(f"Строка {idx}: некорректный тайм или время.")
            continue

        item = _prepare_event(
            idx=idx,
            period=period,
            time_sec=time_sec,
            subject_raw=(row.get("Игрок/Команда") or "").strip(),
            category_raw=(row.get("Категория") or "").strip(),
            action_raw=(row.get("Действие") or "").strip(),
            outcome_raw=(row.get("Результат") or "").strip(),
            comment_raw=(row.get("Комментарий") or "").strip(),
            action_map=action_map,
            player_lookup=player_lookup,
            team_lookup=team_lookup,
            errors=errors,
        )
        if item:
            prepared.append(item)

    return prepared, errors


def _parse_legacy_rows(
    reader: csv.DictReader,
    match_id: int,
    action_map: dict[tuple[str, str], sqlite3.Row],
    player_lookup: dict[str, sqlite3.Row],
    team_lookup: dict[str, sqlite3.Row],
) -> tuple[list[dict[str, object | None]], list[str]]:
    prepared: list[dict[str, object | None]] = []
    errors: list[str] = []

    for idx, row in enumerate(reader, start=2):
        try:
            period = int((row.get("Half") or "").strip())
            time_sec = parse_timestamp((row.get("Time_stamp") or "").strip())
        except ValueError:
            errors.append(f"Строка {idx}: некорректный тайм или время.")
            continue

        item = _prepare_event(
            idx=idx,
            period=period,
            time_sec=time_sec,
            subject_raw=(row.get("Player_ID") or "").strip(),
            category_raw=(row.get("Event_Category") or "").strip(),
            action_raw=(row.get("Event") or "").strip(),
            outcome_raw=(row.get("Outcome") or "").strip(),
            comment_raw="",
            action_map=action_map,
            player_lookup=player_lookup,
            team_lookup=team_lookup,
            errors=errors,
        )
        if item:
            prepared.append(item)

    return prepared, errors


def import_csv_events(
    conn: sqlite3.Connection,
    match_id: int,
    file_bytes: bytes,
    mode: str,
) -> tuple[int, list[str]]:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    csv_format = _detect_format(reader.fieldnames)
    if csv_format is None:
        return 0, [
            "Неверный формат CSV. Поддерживаются: экспорт приложения "
            f"({', '.join(EXPORT_HEADERS)}) или legacy ({', '.join(LEGACY_HEADERS)})."
        ]

    context = _build_lookup_context(conn, match_id)
    if context is None:
        return 0, ["Матч не найден."]

    _, action_map, player_lookup, team_lookup = context
    if csv_format == "export":
        prepared, errors = _parse_export_rows(reader, match_id, action_map, player_lookup, team_lookup)
    else:
        prepared, errors = _parse_legacy_rows(reader, match_id, action_map, player_lookup, team_lookup)

    if errors:
        return 0, errors
    if not prepared:
        return 0, ["CSV не содержит событий для импорта."]

    with conn:
        if mode == "replace":
            conn.execute("DELETE FROM Event WHERE MatchId = ?", (match_id,))
        for item in prepared:
            conn.execute(
                """INSERT INTO Event (MatchId, PeriodNumber, TimestampSec, SubjectType, PlayerId, TeamId, ActionId, Outcome, Comment, CreatedAt)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                (
                    match_id,
                    int(item["period"]),
                    int(item["time"]),
                    str(item["subject_type"]),
                    item["player_id"],
                    item["team_id"],
                    item["action_id"],
                    item["outcome"],
                    item["comment"],
                ),
            )

    return len(prepared), []
