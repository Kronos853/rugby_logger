from __future__ import annotations

from typing import Any

import sqlite3


def _enrich_action_row(row: sqlite3.Row) -> dict[str, Any]:
    total = int(row["Total"])
    success = int(row["SuccessCount"])
    failure = int(row["FailureCount"])
    has_outcome = bool(row["HasOutcome"])
    success_pct: float | None = None
    if has_outcome and (success + failure) > 0:
        success_pct = round(100.0 * success / (success + failure), 1)
    return {
        "action_id": int(row["ActionId"]),
        "name": row["ActionName"],
        "has_outcome": has_outcome,
        "total": total,
        "success": success,
        "failure": failure,
        "success_pct": success_pct,
    }


def _enrich_subject_row(row: sqlite3.Row, *, has_outcome: bool) -> dict[str, Any]:
    total = int(row["Total"])
    success = int(row["SuccessCount"])
    failure = int(row["FailureCount"])
    success_pct: float | None = None
    if has_outcome and (success + failure) > 0:
        success_pct = round(100.0 * success / (success + failure), 1)
    return {
        "label": row["SubjectLabel"],
        "total": total,
        "success": success,
        "failure": failure,
        "success_pct": success_pct,
    }


def build_player_detail(rows: list[sqlite3.Row], *, has_outcome: bool) -> list[dict[str, Any]]:
    return [_enrich_subject_row(row, has_outcome=has_outcome) for row in rows]


def _category_bucket(categories: dict[int, dict[str, Any]], row: sqlite3.Row) -> dict[str, Any]:
    category_id = int(row["CategoryId"])
    if category_id not in categories:
        categories[category_id] = {
            "name": row["CategoryName"],
            "sort_order": int(row["CategorySortOrder"]),
            "actions": [],
        }
    return categories[category_id]


def build_report_summary(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    categories: dict[int, dict[str, Any]] = {}
    for row in rows:
        bucket = _category_bucket(categories, row)
        bucket["actions"].append(_enrich_action_row(row))
    return sorted(categories.values(), key=lambda c: (c["sort_order"], c["name"]))


def build_report_by_match(
    rows: list[sqlite3.Row], teams_by_id: dict[int, sqlite3.Row]
) -> list[dict[str, Any]]:
    matches: dict[int, dict[str, Any]] = {}
    for row in rows:
        match_id = int(row["MatchId"])
        if match_id not in matches:
            home = teams_by_id.get(int(row["HomeTeamId"]))
            away = teams_by_id.get(int(row["AwayTeamId"]))
            home_name = home["Name"] if home else "?"
            away_name = away["Name"] if away else "?"
            matches[match_id] = {
                "match_id": match_id,
                "match_date": row["MatchDate"],
                "label": f"{home_name} — {away_name}",
                "categories": {},
            }
        categories = matches[match_id]["categories"]
        bucket = _category_bucket(categories, row)
        bucket["actions"].append(_enrich_action_row(row))

    sections: list[dict[str, Any]] = []
    for match in sorted(matches.values(), key=lambda m: (m["match_date"], m["match_id"]), reverse=True):
        category_list = sorted(
            match["categories"].values(), key=lambda c: (c["sort_order"], c["name"])
        )
        sections.append(
            {
                "match_id": match["match_id"],
                "match_date": match["match_date"],
                "label": match["label"],
                "categories": category_list,
            }
        )
    return sections
