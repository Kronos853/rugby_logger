from __future__ import annotations

import sqlite3

from . import repository as repo

RUGBY_CATEGORIES = [
    {
        "name": "Handling",
        "actions": [
            {"name": "Pass (success)", "colorClass": "handling"},
            {"name": "Pass (missed)", "colorClass": "handling"},
            {"name": "Catch (success)", "colorClass": "handling"},
            {"name": "Catch (failure)", "colorClass": "handling"},
            {"name": "Knock-on", "colorClass": "handling"},
            {"name": "Forward pass", "colorClass": "handling"},
        ],
    },
    {
        "name": "Offence",
        "actions": [
            {"name": "Carry", "colorClass": "offence"},
            {"name": "Linebreak", "colorClass": "offence"},
            {"name": "try", "colorClass": "offence"},
        ],
    },
    {
        "name": "Tackle",
        "actions": [
            {"name": "Tackle (success)", "colorClass": "tackle"},
            {"name": "Missed tackle", "colorClass": "tackle"},
        ],
    },
    {
        "name": "Kicking",
        "actions": [
            {"name": "Kick (tactical)", "colorClass": "kicking"},
            {"name": "Kick (attacking)", "colorClass": "kicking"},
            {"name": "conversion", "colorClass": "kicking"},
            {"name": "Conversion (opp)", "colorClass": "kicking"},
        ],
    },
    {
        "name": "Set-piece",
        "actions": [
            {"name": "Ruck", "colorClass": "setpiece"},
            {"name": "Lineout (own)", "colorClass": "setpiece"},
            {"name": "Lineout (opp)", "colorClass": "setpiece"},
            {"name": "Scrum (own)", "colorClass": "setpiece"},
            {"name": "Scrum (opp)", "colorClass": "setpiece"},
        ],
    },
    {
        "name": "Defence",
        "actions": [
            {"name": "Turnover", "colorClass": "defence"},
            {"name": "Try conceded", "colorClass": "defence"},
        ],
    },
    {
        "name": "Discipline",
        "actions": [
            {"name": "penalty (offside)", "colorClass": "discipline"},
            {"name": "penalty (high tackle)", "colorClass": "discipline"},
            {"name": "penalty (ruck)", "colorClass": "discipline"},
            {"name": "penalty (other)", "colorClass": "discipline"},
            {"name": "Penalty (opponent)", "colorClass": "discipline"},
            {"name": "yellow card", "colorClass": "discipline"},
            {"name": "red card", "colorClass": "discipline"},
        ],
    },
    {
        "name": "Substitute",
        "actions": [
            {"name": "On", "colorClass": "substitute", "hasOutcome": False},
            {"name": "Off", "colorClass": "substitute", "hasOutcome": False},
        ],
    },
]


def seed_rugby_template(conn: sqlite3.Connection) -> int:
    existing = repo.get_sport_template_by_name(conn, "Регби-7")
    if existing:
        return int(existing["Id"])

    template_id = repo.create_sport_template(conn, "Регби-7")
    category_order = 0
    for category in RUGBY_CATEGORIES:
        category_id = repo.create_category(conn, template_id, category["name"], category_order)
        action_order = 0
        for action in category["actions"]:
            repo.create_action(
                conn,
                category_id,
                action["name"],
                bool(action.get("hasOutcome", True)),
                action_order,
                action.get("colorClass"),
            )
            action_order += 1
        category_order += 1

    return template_id


def ensure_seeded(conn: sqlite3.Connection) -> None:
    if repo.count_sport_templates(conn) == 0:
        seed_rugby_template(conn)


def copy_squad_to_match_lineup(
    conn: sqlite3.Connection, match_id: int, squad_id: int, side: str
) -> None:
    squad = repo.get_squad(conn, squad_id)
    if not squad:
        return

    team_id = int(squad["TeamId"])
    repo.delete_match_lineup_for_team(conn, match_id, team_id)
    squad_players = repo.list_squad_players(conn, squad_id)
    for sp in squad_players:
        repo.add_match_lineup_row(
            conn,
            match_id=match_id,
            team_id=team_id,
            player_id=int(sp["PlayerId"]),
            position=sp["Position"],
            lineup_role=str(sp["LineupRole"]),
            sort_order=int(sp["SortOrder"]),
        )

    if side == "home":
        repo.update_match_squad_refs(conn, match_id, squad_id, None)
    else:
        repo.update_match_squad_refs(conn, match_id, None, squad_id)

