from __future__ import annotations

import sqlite3
from typing import Any


def _rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def _row(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def _insert(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    cur = conn.execute(sql, params)
    conn.commit()
    return int(cur.lastrowid)


def _run(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> None:
    conn.execute(sql, params)
    conn.commit()


def list_sport_templates(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(conn, "SELECT * FROM SportTemplate ORDER BY Name")


def get_sport_template(conn: sqlite3.Connection, template_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM SportTemplate WHERE Id = ?", (template_id,))


def get_sport_template_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM SportTemplate WHERE Name = ?", (name,))


def count_sport_templates(conn: sqlite3.Connection) -> int:
    row = _row(conn, "SELECT COUNT(*) AS c FROM SportTemplate")
    return int(row["c"]) if row else 0


def create_sport_template(conn: sqlite3.Connection, name: str) -> int:
    return _insert(
        conn,
        "INSERT INTO SportTemplate (Name, CreatedAt) VALUES (?, datetime('now'))",
        (name,),
    )


def list_categories_by_template(conn: sqlite3.Connection, template_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn,
        "SELECT * FROM Category WHERE SportTemplateId = ? ORDER BY SortOrder, Id",
        (template_id,),
    )


def get_category(conn: sqlite3.Connection, category_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM Category WHERE Id = ?", (category_id,))


def create_category(
    conn: sqlite3.Connection, sport_template_id: int, name: str, sort_order: int
) -> int:
    return _insert(
        conn,
        "INSERT INTO Category (SportTemplateId, Name, SortOrder) VALUES (?, ?, ?)",
        (sport_template_id, name, sort_order),
    )


def list_actions_by_category(conn: sqlite3.Connection, category_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn, "SELECT * FROM Action WHERE CategoryId = ? ORDER BY SortOrder, Id", (category_id,)
    )


def get_action(conn: sqlite3.Connection, action_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM Action WHERE Id = ?", (action_id,))


def create_action(
    conn: sqlite3.Connection,
    category_id: int,
    name: str,
    has_outcome: bool,
    sort_order: int,
    color_class: str | None,
) -> int:
    return _insert(
        conn,
        "INSERT INTO Action (CategoryId, Name, HasOutcome, SortOrder, ColorClass) VALUES (?, ?, ?, ?, ?)",
        (category_id, name, 1 if has_outcome else 0, sort_order, color_class),
    )


def update_action_name(conn: sqlite3.Connection, action_id: int, name: str) -> None:
    _run(conn, "UPDATE Action SET Name = ? WHERE Id = ?", (name, action_id))


def update_category_name(conn: sqlite3.Connection, category_id: int, name: str) -> None:
    _run(conn, "UPDATE Category SET Name = ? WHERE Id = ?", (name, category_id))


def update_category_show_in_report(conn: sqlite3.Connection, category_id: int, show: bool) -> None:
    _run(conn, "UPDATE Category SET ShowInReport = ? WHERE Id = ?", (1 if show else 0, category_id))


def update_action_category(conn: sqlite3.Connection, action_id: int, category_id: int) -> None:
    sort_order = len(list_actions_by_category(conn, category_id))
    _run(
        conn,
        "UPDATE Action SET CategoryId = ?, SortOrder = ? WHERE Id = ?",
        (category_id, sort_order, action_id),
    )


def update_action_has_outcome(conn: sqlite3.Connection, action_id: int, has_outcome: bool) -> None:
    _run(
        conn,
        "UPDATE Action SET HasOutcome = ? WHERE Id = ?",
        (1 if has_outcome else 0, action_id),
    )


def update_action_show_in_report(conn: sqlite3.Connection, action_id: int, show: bool) -> None:
    _run(conn, "UPDATE Action SET ShowInReport = ? WHERE Id = ?", (1 if show else 0, action_id))


def update_sport_template_period_count(
    conn: sqlite3.Connection, template_id: int, period_count: int
) -> None:
    _run(conn, "UPDATE SportTemplate SET PeriodCount = ? WHERE Id = ?", (period_count, template_id))


VALID_OUTCOME_FILTERS = frozenset({"any", "Success", "Failure"})
VALID_PERSPECTIVES = frozenset({"own", "opponent"})


def action_belongs_to_template(conn: sqlite3.Connection, template_id: int, action_id: int) -> bool:
    row = _row(
        conn,
        """
        SELECT 1
        FROM Action a
        INNER JOIN Category c ON c.Id = a.CategoryId
        WHERE a.Id = ? AND c.SportTemplateId = ?
        """,
        (action_id, template_id),
    )
    return row is not None


def list_team_stat_metrics(conn: sqlite3.Connection, template_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn,
        "SELECT * FROM TeamStatMetric WHERE SportTemplateId = ? ORDER BY SortOrder, Id",
        (template_id,),
    )


def get_team_stat_metric(conn: sqlite3.Connection, metric_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM TeamStatMetric WHERE Id = ?", (metric_id,))


def list_team_stat_metric_conditions(
    conn: sqlite3.Connection, metric_id: int
) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """SELECT * FROM TeamStatMetricCondition
           WHERE TeamStatMetricId = ? ORDER BY SortOrder, Id""",
        (metric_id,),
    )


def get_team_stat_metric_condition(
    conn: sqlite3.Connection, condition_id: int
) -> sqlite3.Row | None:
    return _row(
        conn, "SELECT * FROM TeamStatMetricCondition WHERE Id = ?", (condition_id,)
    )


def _validate_condition_fields(
    conn: sqlite3.Connection,
    template_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> None:
    if outcome_filter not in VALID_OUTCOME_FILTERS:
        raise ValueError("Недопустимый фильтр исхода.")
    if perspective not in VALID_PERSPECTIVES:
        raise ValueError("Недопустимая перспектива.")
    if not action_belongs_to_template(conn, template_id, action_id):
        raise ValueError("Действие не принадлежит этому шаблону.")


def create_team_stat_metric(
    conn: sqlite3.Connection,
    template_id: int,
    name: str,
    action_id: int,
    outcome_filter: str,
    perspective: str = "own",
) -> int:
    _validate_condition_fields(conn, template_id, action_id, outcome_filter, perspective)
    existing = list_team_stat_metrics(conn, template_id)
    sort_order = (max(int(m["SortOrder"]) for m in existing) + 1) if existing else 0
    metric_id = _insert(
        conn,
        """INSERT INTO TeamStatMetric (SportTemplateId, Name, SortOrder)
           VALUES (?, ?, ?)""",
        (template_id, name.strip(), sort_order),
    )
    _insert(
        conn,
        """INSERT INTO TeamStatMetricCondition
           (TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)
           VALUES (?, ?, ?, ?, 0)""",
        (metric_id, action_id, outcome_filter, perspective),
    )
    return metric_id


def update_team_stat_metric(conn: sqlite3.Connection, metric_id: int, name: str) -> None:
    metric = get_team_stat_metric(conn, metric_id)
    if not metric:
        raise ValueError("Метрика не найдена.")
    _run(
        conn,
        "UPDATE TeamStatMetric SET Name = ? WHERE Id = ?",
        (name.strip(), metric_id),
    )


def create_team_stat_condition(
    conn: sqlite3.Connection,
    metric_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> int:
    metric = get_team_stat_metric(conn, metric_id)
    if not metric:
        raise ValueError("Метрика не найдена.")
    template_id = int(metric["SportTemplateId"])
    _validate_condition_fields(conn, template_id, action_id, outcome_filter, perspective)
    existing = list_team_stat_metric_conditions(conn, metric_id)
    sort_order = (max(int(c["SortOrder"]) for c in existing) + 1) if existing else 0
    return _insert(
        conn,
        """INSERT INTO TeamStatMetricCondition
           (TeamStatMetricId, ActionId, OutcomeFilter, Perspective, SortOrder)
           VALUES (?, ?, ?, ?, ?)""",
        (metric_id, action_id, outcome_filter, perspective, sort_order),
    )


def update_team_stat_condition(
    conn: sqlite3.Connection,
    condition_id: int,
    action_id: int,
    outcome_filter: str,
    perspective: str,
) -> None:
    condition = get_team_stat_metric_condition(conn, condition_id)
    if not condition:
        raise ValueError("Условие не найдено.")
    metric = get_team_stat_metric(conn, int(condition["TeamStatMetricId"]))
    assert metric is not None
    _validate_condition_fields(
        conn, int(metric["SportTemplateId"]), action_id, outcome_filter, perspective
    )
    _run(
        conn,
        """UPDATE TeamStatMetricCondition
           SET ActionId = ?, OutcomeFilter = ?, Perspective = ?
           WHERE Id = ?""",
        (action_id, outcome_filter, perspective, condition_id),
    )


def delete_team_stat_condition(conn: sqlite3.Connection, condition_id: int) -> None:
    condition = get_team_stat_metric_condition(conn, condition_id)
    if not condition:
        return
    metric_id = int(condition["TeamStatMetricId"])
    remaining = [
        c
        for c in list_team_stat_metric_conditions(conn, metric_id)
        if int(c["Id"]) != condition_id
    ]
    _run(conn, "DELETE FROM TeamStatMetricCondition WHERE Id = ?", (condition_id,))
    if not remaining:
        delete_team_stat_metric(conn, metric_id)


def delete_team_stat_metric(conn: sqlite3.Connection, metric_id: int) -> None:
    _run(conn, "DELETE FROM TeamStatMetric WHERE Id = ?", (metric_id,))


def swap_team_stat_metric_order(
    conn: sqlite3.Connection,
    template_id: int,
    metric_id: int,
    direction: str,
) -> None:
    metrics = list_team_stat_metrics(conn, template_id)
    ids = [int(m["Id"]) for m in metrics]
    if metric_id not in ids:
        raise ValueError("Метрика не найдена.")
    idx = ids.index(metric_id)
    if direction == "up":
        if idx == 0:
            return
        neighbor_idx = idx - 1
    elif direction == "down":
        if idx == len(ids) - 1:
            return
        neighbor_idx = idx + 1
    else:
        raise ValueError("Недопустимое направление.")
    current = metrics[idx]
    neighbor = metrics[neighbor_idx]
    _run(
        conn,
        "UPDATE TeamStatMetric SET SortOrder = ? WHERE Id = ?",
        (int(neighbor["SortOrder"]), int(current["Id"])),
    )
    _run(
        conn,
        "UPDATE TeamStatMetric SET SortOrder = ? WHERE Id = ?",
        (int(current["SortOrder"]), int(neighbor["Id"])),
    )


def get_match_team_stat_counts(conn: sqlite3.Connection, match_id: int) -> list[dict[str, Any]]:
    match = get_match(conn, match_id)
    if not match:
        return []
    template_id = int(match["SportTemplateId"])
    home_team_id = int(match["HomeTeamId"])
    away_team_id = int(match["AwayTeamId"])
    metrics = list_team_stat_metrics(conn, template_id)
    if not metrics:
        return []

    count_rows = _rows(
        conn,
        """
        WITH attributed AS (
          SELECT
            e.ActionId,
            e.Outcome,
            CASE
              WHEN e.SubjectType = 'team' THEN e.TeamId
              ELSE ml.TeamId
            END AS TeamId
          FROM Event e
          LEFT JOIN MatchLineup ml
            ON ml.MatchId = e.MatchId AND ml.PlayerId = e.PlayerId
          WHERE e.MatchId = ?
        )
        SELECT
          tsm.Id AS MetricId,
          a.TeamId,
          COUNT(*) AS Cnt
        FROM TeamStatMetric tsm
        INNER JOIN attributed a ON a.ActionId = tsm.ActionId
          AND a.TeamId IS NOT NULL
          AND (
            tsm.OutcomeFilter = 'any'
            OR a.Outcome = tsm.OutcomeFilter
          )
        WHERE tsm.SportTemplateId = ?
          AND a.TeamId IN (?, ?)
        GROUP BY tsm.Id, a.TeamId
        """,
        (match_id, template_id, home_team_id, away_team_id),
    )

    counts: dict[tuple[int, int], int] = {}
    for row in count_rows:
        counts[(int(row["MetricId"]), int(row["TeamId"]))] = int(row["Cnt"])

    result: list[dict[str, Any]] = []
    for metric in metrics:
        metric_id = int(metric["Id"])
        result.append(
            {
                "metric_id": metric_id,
                "name": str(metric["Name"]),
                "sort_order": int(metric["SortOrder"]),
                "home_count": counts.get((metric_id, home_team_id), 0),
                "away_count": counts.get((metric_id, away_team_id), 0),
            }
        )
    return result


def count_events_by_action(conn: sqlite3.Connection, action_id: int) -> int:
    row = _row(conn, "SELECT COUNT(*) AS c FROM Event WHERE ActionId = ?", (action_id,))
    return int(row["c"]) if row else 0


def delete_team_stat_metrics_by_action(conn: sqlite3.Connection, action_id: int) -> None:
    _run(conn, "DELETE FROM TeamStatMetric WHERE ActionId = ?", (action_id,))


def delete_team_stat_metrics_by_category(conn: sqlite3.Connection, category_id: int) -> None:
    _run(
        conn,
        """
        DELETE FROM TeamStatMetric
        WHERE ActionId IN (SELECT Id FROM Action WHERE CategoryId = ?)
        """,
        (category_id,),
    )


def list_comments_by_action(conn: sqlite3.Connection, action_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn, "SELECT * FROM CommentTemplate WHERE ActionId = ? ORDER BY SortOrder, Id", (action_id,)
    )


def create_comment_template(
    conn: sqlite3.Connection, action_id: int, text: str, sort_order: int
) -> int:
    return _insert(
        conn,
        "INSERT INTO CommentTemplate (ActionId, Text, SortOrder) VALUES (?, ?, ?)",
        (action_id, text, sort_order),
    )


def list_teams(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(conn, "SELECT * FROM Team ORDER BY Name")


def get_team(conn: sqlite3.Connection, team_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM Team WHERE Id = ?", (team_id,))


def create_team(conn: sqlite3.Connection, name: str) -> int:
    return _insert(conn, "INSERT INTO Team (Name, CreatedAt) VALUES (?, datetime('now'))", (name,))


def list_players(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(conn, "SELECT * FROM Player ORDER BY Name")


def list_players_by_team(
    conn: sqlite3.Connection,
    team_id: int,
    *,
    active_only: bool = False,
) -> list[sqlite3.Row]:
    if active_only:
        return _rows(
            conn,
            "SELECT * FROM Player WHERE TeamId = ? AND IsActive = 1 ORDER BY Name",
            (team_id,),
        )
    return _rows(conn, "SELECT * FROM Player WHERE TeamId = ? ORDER BY Name", (team_id,))


def get_player(conn: sqlite3.Connection, player_id: int) -> sqlite3.Row | None:
    return _row(conn, "SELECT * FROM Player WHERE Id = ?", (player_id,))


def is_player_active(conn: sqlite3.Connection, player_id: int) -> bool:
    row = _row(conn, "SELECT IsActive FROM Player WHERE Id = ?", (player_id,))
    return bool(row and row["IsActive"])


def create_player(
    conn: sqlite3.Connection,
    team_id: int,
    name: str,
    default_position: str | None,
    full_name: str | None = None,
    birth_day: str | None = None,
) -> int:
    return _insert(
        conn,
        "INSERT INTO Player (TeamId, Name, FullName, BirthDay, DefaultPosition, IsActive) VALUES (?, ?, ?, ?, ?, 1)",
        (team_id, name, full_name, birth_day, default_position),
    )


def update_player(
    conn: sqlite3.Connection,
    player_id: int,
    name: str,
    full_name: str | None,
    birth_day: str | None,
    default_position: str | None,
    is_active: bool = True,
) -> None:
    _run(
        conn,
        "UPDATE Player SET Name = ?, FullName = ?, BirthDay = ?, DefaultPosition = ?, IsActive = ? WHERE Id = ?",
        (name, full_name, birth_day, default_position, 1 if is_active else 0, player_id),
    )


def list_squads(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """
        SELECT s.*, t.Name AS TournamentName
        FROM Squad s
        LEFT JOIN Tournament t ON t.Id = s.TournamentId
        ORDER BY s.Name
        """,
    )


def list_squads_by_team(conn: sqlite3.Connection, team_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """
        SELECT s.*, t.Name AS TournamentName
        FROM Squad s
        LEFT JOIN Tournament t ON t.Id = s.TournamentId
        WHERE s.TeamId = ?
        ORDER BY s.Name
        """,
        (team_id,),
    )


def get_squad(conn: sqlite3.Connection, squad_id: int) -> sqlite3.Row | None:
    return _row(
        conn,
        """
        SELECT s.*, t.Name AS TournamentName
        FROM Squad s
        LEFT JOIN Tournament t ON t.Id = s.TournamentId
        WHERE s.Id = ?
        """,
        (squad_id,),
    )


def get_tournaments(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(conn, "SELECT * FROM Tournament ORDER BY Name")


def get_or_create_tournament(conn: sqlite3.Connection, name: str | None) -> int | None:
    if not name or not name.strip():
        return None
    clean = name.strip()
    row = _row(conn, "SELECT Id FROM Tournament WHERE Name = ?", (clean,))
    if row:
        return int(row["Id"])
    return _insert(
        conn,
        "INSERT INTO Tournament (Name, CreatedAt) VALUES (?, datetime('now'))",
        (clean,),
    )


def create_squad(
    conn: sqlite3.Connection, team_id: int, name: str, tournament_name: str | None
) -> int:
    tournament_id = get_or_create_tournament(conn, tournament_name)
    return _insert(
        conn,
        "INSERT INTO Squad (TeamId, Name, TournamentId, CreatedAt) VALUES (?, ?, ?, datetime('now'))",
        (team_id, name, tournament_id),
    )


def update_squad(
    conn: sqlite3.Connection, squad_id: int, name: str | None, tournament_name: str | None
) -> None:
    if name is not None:
        conn.execute("UPDATE Squad SET Name = ? WHERE Id = ?", (name, squad_id))
    tournament_id = get_or_create_tournament(conn, tournament_name)
    conn.execute("UPDATE Squad SET TournamentId = ? WHERE Id = ?", (tournament_id, squad_id))
    conn.commit()


def list_squad_players(conn: sqlite3.Connection, squad_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn, "SELECT * FROM SquadPlayer WHERE SquadId = ? ORDER BY SortOrder, Id", (squad_id,)
    )


def add_squad_player(
    conn: sqlite3.Connection, squad_id: int, player_id: int, sort_order: int
) -> int:
    return _insert(
        conn,
        "INSERT INTO SquadPlayer (SquadId, PlayerId, LineupRole, SortOrder) VALUES (?, ?, 'starter', ?)",
        (squad_id, player_id, sort_order),
    )


def update_squad_player_role(conn: sqlite3.Connection, squad_player_id: int, role: str) -> None:
    _run(conn, "UPDATE SquadPlayer SET LineupRole = ? WHERE Id = ?", (role, squad_player_id))


def delete_squad_player(conn: sqlite3.Connection, squad_player_id: int) -> None:
    _run(conn, "DELETE FROM SquadPlayer WHERE Id = ?", (squad_player_id,))


def list_matches(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """
        SELECT m.*, t.Name AS TournamentName
        FROM Match m
        LEFT JOIN Tournament t ON t.Id = m.TournamentId
        ORDER BY m.MatchDate DESC, m.Id DESC
        """,
    )


def get_match(conn: sqlite3.Connection, match_id: int) -> sqlite3.Row | None:
    return _row(
        conn,
        """
        SELECT m.*, t.Name AS TournamentName
        FROM Match m
        LEFT JOIN Tournament t ON t.Id = m.TournamentId
        WHERE m.Id = ?
        """,
        (match_id,),
    )


def count_matches_by_template(conn: sqlite3.Connection, template_id: int) -> int:
    row = _row(conn, "SELECT COUNT(*) AS c FROM Match WHERE SportTemplateId = ?", (template_id,))
    return int(row["c"]) if row else 0


def count_matches_by_team(conn: sqlite3.Connection, team_id: int) -> int:
    row = _row(
        conn, "SELECT COUNT(*) AS c FROM Match WHERE HomeTeamId = ? OR AwayTeamId = ?", (team_id, team_id)
    )
    return int(row["c"]) if row else 0


def create_match(
    conn: sqlite3.Connection,
    sport_template_id: int,
    home_team_id: int,
    away_team_id: int,
    match_date: str,
    tournament_name: str | None,
    score_home: int | None,
    score_away: int | None,
) -> int:
    tournament_id = get_or_create_tournament(conn, tournament_name)
    return _insert(
        conn,
        """INSERT INTO Match (SportTemplateId, HomeTeamId, AwayTeamId, MatchDate, TournamentId, ScoreHome, ScoreAway, CreatedAt)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (sport_template_id, home_team_id, away_team_id, match_date, tournament_id, score_home, score_away),
    )


def create_match_periods(conn: sqlite3.Connection, match_id: int) -> None:
    conn.execute("INSERT INTO MatchPeriod (MatchId, PeriodNumber, Label) VALUES (?, 1, ?)", (match_id, "1-й тайм"))
    conn.execute("INSERT INTO MatchPeriod (MatchId, PeriodNumber, Label) VALUES (?, 2, ?)", (match_id, "2-й тайм"))
    conn.commit()


def update_match_details(
    conn: sqlite3.Connection,
    match_id: int,
    match_date: str,
    tournament_name: str | None,
) -> None:
    tournament_id = get_or_create_tournament(conn, tournament_name)
    conn.execute(
        "UPDATE Match SET MatchDate = ?, TournamentId = ? WHERE Id = ?",
        (match_date, tournament_id, match_id),
    )
    conn.commit()


def update_match_squad_refs(
    conn: sqlite3.Connection, match_id: int, home_squad_id: int | None, away_squad_id: int | None
) -> None:
    if home_squad_id is not None:
        conn.execute("UPDATE Match SET HomeSquadId = ? WHERE Id = ?", (home_squad_id, match_id))
    if away_squad_id is not None:
        conn.execute("UPDATE Match SET AwaySquadId = ? WHERE Id = ?", (away_squad_id, match_id))
    conn.commit()


def list_match_lineup(conn: sqlite3.Connection, match_id: int) -> list[sqlite3.Row]:
    return _rows(
        conn, "SELECT * FROM MatchLineup WHERE MatchId = ? ORDER BY SortOrder, Id", (match_id,)
    )


def delete_match_lineup_for_team(conn: sqlite3.Connection, match_id: int, team_id: int) -> None:
    _run(conn, "DELETE FROM MatchLineup WHERE MatchId = ? AND TeamId = ?", (match_id, team_id))


def add_match_lineup_row(
    conn: sqlite3.Connection,
    match_id: int,
    team_id: int,
    player_id: int,
    position: str | None,
    lineup_role: str,
    sort_order: int,
) -> int:
    return _insert(
        conn,
        """INSERT INTO MatchLineup (MatchId, TeamId, PlayerId, Position, LineupRole, SortOrder)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (match_id, team_id, player_id, position, lineup_role, sort_order),
    )


def update_match_lineup_role(conn: sqlite3.Connection, row_id: int, role: str) -> None:
    _run(conn, "UPDATE MatchLineup SET LineupRole = ? WHERE Id = ?", (role, row_id))


def list_events_by_match(conn: sqlite3.Connection, match_id: int) -> list[sqlite3.Row]:
    return _rows(conn, "SELECT * FROM Event WHERE MatchId = ? ORDER BY CreatedAt, Id", (match_id,))


def count_events_by_match(conn: sqlite3.Connection, match_id: int) -> int:
    row = _row(conn, "SELECT COUNT(*) AS c FROM Event WHERE MatchId = ?", (match_id,))
    return int(row["c"]) if row else 0


def create_event(
    conn: sqlite3.Connection,
    match_id: int,
    period_number: int,
    timestamp_sec: int,
    subject_type: str,
    player_id: int | None = None,
    team_id: int | None = None,
    action_id: int | None = None,
    outcome: str | None = None,
    comment: str | None = None,
) -> int:
    return _insert(
        conn,
        """INSERT INTO Event (MatchId, PeriodNumber, TimestampSec, SubjectType, PlayerId, TeamId, ActionId, Outcome, Comment, CreatedAt)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (match_id, period_number, timestamp_sec, subject_type, player_id, team_id, action_id, outcome, comment),
    )


def update_event(
    conn: sqlite3.Connection,
    event_id: int,
    period_number: int | None = None,
    subject_type: str | None = None,
    player_id: int | None = None,
    team_id: int | None = None,
    action_id: int | None = None,
    outcome: str | None = None,
    comment: str | None = None,
) -> None:
    fields: list[str] = []
    values: list[Any] = []

    if period_number is not None:
        fields.append("PeriodNumber = ?")
        values.append(period_number)
    if subject_type is not None:
        fields.append("SubjectType = ?")
        values.append(subject_type)
    if player_id is not None or subject_type == "team":
        fields.append("PlayerId = ?")
        values.append(player_id)
    if team_id is not None or subject_type == "player":
        fields.append("TeamId = ?")
        values.append(team_id)
    if action_id is not None:
        fields.append("ActionId = ?")
        values.append(action_id)
    if outcome is not None or outcome == "":
        fields.append("Outcome = ?")
        values.append(outcome if outcome else None)
    if comment is not None:
        fields.append("Comment = ?")
        values.append(comment)

    if not fields:
        return

    values.append(event_id)
    conn.execute(f"UPDATE Event SET {', '.join(fields)} WHERE Id = ?", tuple(values))
    conn.commit()


def delete_event(conn: sqlite3.Connection, event_id: int) -> None:
    _run(conn, "DELETE FROM Event WHERE Id = ?", (event_id,))


def delete_events_by_match(conn: sqlite3.Connection, match_id: int) -> None:
    _run(conn, "DELETE FROM Event WHERE MatchId = ?", (match_id,))


def delete_comment_template(conn: sqlite3.Connection, comment_id: int) -> None:
    _run(conn, "DELETE FROM CommentTemplate WHERE Id = ?", (comment_id,))


def delete_action(conn: sqlite3.Connection, action_id: int) -> None:
    if count_events_by_action(conn, action_id) > 0:
        raise ValueError("Действие используется в событиях матчей.")
    delete_team_stat_metrics_by_action(conn, action_id)
    _run(conn, "DELETE FROM Action WHERE Id = ?", (action_id,))


def delete_category(conn: sqlite3.Connection, category_id: int) -> None:
    actions = list_actions_by_category(conn, category_id)
    for action in actions:
        if count_events_by_action(conn, int(action["Id"])) > 0:
            raise ValueError("Категория содержит действия, используемые в событиях матчей.")
    delete_team_stat_metrics_by_category(conn, category_id)
    _run(conn, "DELETE FROM Category WHERE Id = ?", (category_id,))


def delete_sport_template(conn: sqlite3.Connection, template_id: int) -> None:
    if count_matches_by_template(conn, template_id) > 0:
        raise ValueError("Шаблон используется в матчах. Сначала удалите матчи.")
    _run(conn, "DELETE FROM SportTemplate WHERE Id = ?", (template_id,))


def delete_player(conn: sqlite3.Connection, player_id: int) -> None:
    conn.execute("DELETE FROM MatchLineup WHERE PlayerId = ?", (player_id,))
    conn.execute("UPDATE Event SET PlayerId = NULL WHERE PlayerId = ?", (player_id,))
    conn.execute("DELETE FROM Player WHERE Id = ?", (player_id,))
    conn.commit()


def delete_team(conn: sqlite3.Connection, team_id: int) -> None:
    if count_matches_by_team(conn, team_id) > 0:
        raise ValueError("Команда используется в матчах. Сначала удалите матчи.")
    _run(conn, "DELETE FROM Team WHERE Id = ?", (team_id,))


def delete_squad(conn: sqlite3.Connection, squad_id: int) -> None:
    conn.execute("UPDATE Match SET HomeSquadId = NULL WHERE HomeSquadId = ?", (squad_id,))
    conn.execute("UPDATE Match SET AwaySquadId = NULL WHERE AwaySquadId = ?", (squad_id,))
    conn.execute("DELETE FROM Squad WHERE Id = ?", (squad_id,))
    conn.commit()


def delete_match(conn: sqlite3.Connection, match_id: int) -> None:
    _run(conn, "DELETE FROM Match WHERE Id = ?", (match_id,))


SETTING_PRIMARY_TEAM = "primary_team_id"


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = _row(conn, "SELECT Value FROM AppSetting WHERE Key = ?", (key,))
    return str(row["Value"]) if row and row["Value"] is not None else None


def set_setting(conn: sqlite3.Connection, key: str, value: str | None) -> None:
    if value is None:
        conn.execute("DELETE FROM AppSetting WHERE Key = ?", (key,))
    else:
        conn.execute(
            "INSERT INTO AppSetting (Key, Value) VALUES (?, ?) "
            "ON CONFLICT(Key) DO UPDATE SET Value = excluded.Value",
            (key, value),
        )
    conn.commit()


def get_primary_team_id(conn: sqlite3.Connection) -> int | None:
    value = get_setting(conn, SETTING_PRIMARY_TEAM)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def set_primary_team_id(conn: sqlite3.Connection, team_id: int | None) -> None:
    if team_id is None:
        set_setting(conn, SETTING_PRIMARY_TEAM, None)
        return
    team = get_team(conn, team_id)
    if not team:
        raise ValueError("Команда не найдена.")
    set_setting(conn, SETTING_PRIMARY_TEAM, str(team_id))


def _report_subject_clause(subject_type: str) -> tuple[str, tuple[Any, ...]]:
    if subject_type == "player":
        return "e.SubjectType = 'player' AND e.PlayerId = ?", ()
    if subject_type == "team":
        return (
            """(
                (e.SubjectType = 'player' AND e.PlayerId IN (SELECT Id FROM Player WHERE TeamId = ?))
                OR (e.SubjectType = 'team' AND e.TeamId = ?)
            )""",
            (),
        )
    raise ValueError(f"Unknown subject_type: {subject_type}")


def get_player_last_match_ids(
    conn: sqlite3.Connection, player_id: int, *, limit: int = 5
) -> list[sqlite3.Row]:
    return _rows(
        conn,
        """
        SELECT DISTINCT m.Id AS MatchId, m.MatchDate, m.HomeTeamId, m.AwayTeamId
        FROM MatchLineup ml
        INNER JOIN Match m ON m.Id = ml.MatchId
        WHERE ml.PlayerId = ?
        ORDER BY m.MatchDate DESC, m.Id DESC
        LIMIT ?
        """,
        (player_id, limit),
    )


def get_report_data(
    conn: sqlite3.Connection,
    subject_type: str,
    subject_id: int,
    date_from: str,
    date_to: str,
    *,
    by_match: bool = False,
    tournament_id: int | None = None,
    match_ids: list[int] | None = None,
) -> list[sqlite3.Row]:
    subject_sql, _ = _report_subject_clause(subject_type)
    group_match = ", m.Id, m.MatchDate, m.HomeTeamId, m.AwayTeamId" if by_match else ""
    select_match = (
        ", m.Id AS MatchId, m.MatchDate, m.HomeTeamId, m.AwayTeamId" if by_match else ""
    )

    params: list[Any] = [date_from, date_to]
    if subject_type == "player":
        params.append(subject_id)
    else:
        params.extend([subject_id, subject_id])

    tournament_sql = ""
    if tournament_id is not None:
        tournament_sql = "AND m.TournamentId = ?"
        params.append(tournament_id)

    match_ids_sql = ""
    if match_ids:
        placeholders = ",".join("?" for _ in match_ids)
        match_ids_sql = f"AND m.Id IN ({placeholders})"
        params.extend(match_ids)

    sql = f"""
        SELECT
            c.Id AS CategoryId,
            c.Name AS CategoryName,
            c.SortOrder AS CategorySortOrder,
            a.Id AS ActionId,
            a.Name AS ActionName,
            a.HasOutcome,
            a.SortOrder AS ActionSortOrder
            {select_match},
            COUNT(*) AS Total,
            SUM(CASE WHEN e.Outcome = 'Success' THEN 1 ELSE 0 END) AS SuccessCount,
            SUM(CASE WHEN e.Outcome = 'Failure' THEN 1 ELSE 0 END) AS FailureCount
        FROM Event e
        INNER JOIN Match m ON m.Id = e.MatchId
        INNER JOIN Action a ON a.Id = e.ActionId
        INNER JOIN Category c ON c.Id = a.CategoryId
        WHERE e.ActionId IS NOT NULL
          AND c.ShowInReport = 1
          AND a.ShowInReport = 1
          AND m.MatchDate >= ? AND m.MatchDate <= ?
          AND {subject_sql}
          {tournament_sql}
          {match_ids_sql}
        GROUP BY c.Id, a.Id{group_match}
        HAVING COUNT(*) > 0
        ORDER BY c.SortOrder, c.Id, a.SortOrder, a.Id
    """
    if by_match:
        sql += ", m.MatchDate DESC, m.Id DESC"

    return _rows(conn, sql, tuple(params))


def get_report_comment_detail(
    conn: sqlite3.Connection,
    action_id: int,
    subject_type: str,
    subject_id: int,
    date_from: str,
    date_to: str,
    *,
    tournament_id: int | None = None,
    match_id: int | None = None,
) -> list[sqlite3.Row]:
    subject_sql, _ = _report_subject_clause(subject_type)
    params: list[Any] = [action_id, date_from, date_to]
    if subject_type == "player":
        params.append(subject_id)
    else:
        params.extend([subject_id, subject_id])

    tournament_sql = ""
    if tournament_id is not None:
        tournament_sql = "AND m.TournamentId = ?"
        params.append(tournament_id)

    match_sql = ""
    if match_id is not None:
        match_sql = "AND m.Id = ?"
        params.append(match_id)

    return _rows(
        conn,
        f"""
        SELECT
            COALESCE(NULLIF(trim(e.Comment), ''), '— no comment —') AS CommentLabel,
            COUNT(*) AS Total,
            SUM(CASE WHEN e.Outcome = 'Success' THEN 1 ELSE 0 END) AS SuccessCount,
            SUM(CASE WHEN e.Outcome = 'Failure' THEN 1 ELSE 0 END) AS FailureCount
        FROM Event e
        INNER JOIN Match m ON m.Id = e.MatchId
        INNER JOIN Action a ON a.Id = e.ActionId
        INNER JOIN Category c ON c.Id = a.CategoryId
        WHERE e.ActionId = ?
          AND c.ShowInReport = 1
          AND a.ShowInReport = 1
          AND m.MatchDate >= ? AND m.MatchDate <= ?
          AND {subject_sql}
          {tournament_sql}
          {match_sql}
        GROUP BY CommentLabel
        HAVING COUNT(*) > 0
        ORDER BY Total DESC, CommentLabel
        """,
        tuple(params),
    )


def get_report_player_detail(
    conn: sqlite3.Connection,
    action_id: int,
    team_id: int,
    date_from: str,
    date_to: str,
    *,
    tournament_id: int | None = None,
    match_id: int | None = None,
) -> list[sqlite3.Row]:
    params: list[Any] = [action_id, date_from, date_to, team_id, team_id]

    tournament_sql = ""
    if tournament_id is not None:
        tournament_sql = "AND m.TournamentId = ?"
        params.append(tournament_id)

    match_sql = ""
    if match_id is not None:
        match_sql = "AND m.Id = ?"
        params.append(match_id)

    return _rows(
        conn,
        f"""
        SELECT
            COALESCE(p.Name, tm.Name, '?') AS SubjectLabel,
            COUNT(*) AS Total,
            SUM(CASE WHEN e.Outcome = 'Success' THEN 1 ELSE 0 END) AS SuccessCount,
            SUM(CASE WHEN e.Outcome = 'Failure' THEN 1 ELSE 0 END) AS FailureCount
        FROM Event e
        INNER JOIN Match m ON m.Id = e.MatchId
        INNER JOIN Action a ON a.Id = e.ActionId
        INNER JOIN Category c ON c.Id = a.CategoryId
        LEFT JOIN Player p ON e.SubjectType = 'player' AND e.PlayerId = p.Id
        LEFT JOIN Team tm ON e.SubjectType = 'team' AND e.TeamId = tm.Id
        WHERE e.ActionId = ?
          AND c.ShowInReport = 1
          AND a.ShowInReport = 1
          AND m.MatchDate >= ? AND m.MatchDate <= ?
          AND (
              (e.SubjectType = 'player' AND e.PlayerId IN (SELECT Id FROM Player WHERE TeamId = ?))
              OR (e.SubjectType = 'team' AND e.TeamId = ?)
          )
          {tournament_sql}
          {match_sql}
        GROUP BY e.SubjectType, e.PlayerId, e.TeamId
        HAVING COUNT(*) > 0
        ORDER BY Total DESC, SubjectLabel ASC
        """,
        tuple(params),
    )


def get_player_last5_stats(conn: sqlite3.Connection, player_id: int) -> list[sqlite3.Row]:
    matches = get_player_last_match_ids(conn, player_id, limit=5)
    if not matches:
        return []
    match_ids = [int(m["MatchId"]) for m in matches]
    date_from = min(str(m["MatchDate"]) for m in matches)
    date_to = max(str(m["MatchDate"]) for m in matches)
    return get_report_data(
        conn,
        "player",
        player_id,
        date_from,
        date_to,
        match_ids=match_ids,
    )

