from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from . import repository as repo
from .csv_export import build_csv, build_export_filename, export_content_disposition
from .csv_import import import_csv_events
from .db import DEFAULT_DB_PATH, connect, ensure_db, restore_database_from_file, validate_sqlite_file
from .match_score import calculate_match_score_for_match
from .format_time import format_timestamp
from .reports import build_player_detail, build_report_by_match, build_report_summary
from .seed import copy_squad_to_match_lineup, ensure_seeded, seed_rugby_template

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _tagging_event_subject_name(
    selected_event: sqlite3.Row | None,
    players: list[sqlite3.Row],
    teams: list[sqlite3.Row],
) -> str:
    if not selected_event:
        return "—"
    player_id = selected_event["PlayerId"]
    if player_id:
        player = next((p for p in players if int(p["Id"]) == int(player_id)), None)
        return str(player["Name"]) if player else "—"
    team_id = selected_event["TeamId"]
    if team_id:
        team = next((t for t in teams if int(t["Id"]) == int(team_id)), None)
        return str(team["Name"]) if team else "—"
    return "—"


def _tagging_scroll_focus_incomplete(
    selected_event: sqlite3.Row | None,
    selected_action: sqlite3.Row | None,
) -> str | None:
    if not selected_event:
        return None
    if not selected_event["PlayerId"] and not selected_event["TeamId"]:
        return "player"
    if not selected_event["ActionId"]:
        return "action"
    if selected_action and selected_action["HasOutcome"] and selected_event["Outcome"] is None:
        return "outcome"
    return None


def _tagging_scroll_focus_after_update(
    form,
    selected_action: sqlite3.Row | None,
) -> str | None:
    if form.get("subjectType"):
        return "action"
    if form.get("actionId"):
        if selected_action and selected_action["HasOutcome"]:
            return "outcome"
        return "comment"
    if "outcome" in form:
        return "comment"
    return None


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.secret_key = os.environ.get("SPORTS_LOGGER_SECRET", "sports-video-logger-local-secret")
    app.config["DB_PATH"] = Path(os.environ.get("SPORTS_LOGGER_DB", str(DEFAULT_DB_PATH)))

    ensure_db(app.config["DB_PATH"])

    @app.template_filter("format_time")
    def format_time_filter(seconds: int | float | None) -> str:
        return format_timestamp(seconds)

    @app.context_processor
    def inject_nav() -> dict[str, object]:
        return {"today": date.today().isoformat()}

    def db() -> sqlite3.Connection:
        conn = connect(app.config["DB_PATH"])
        ensure_seeded(conn)
        return conn

    @app.get("/")
    def home() -> str:
        return render_template("home.html")

    # Templates directory
    @app.get("/directories/templates")
    def templates_page() -> str:
        with db() as conn:
            templates = repo.list_sport_templates(conn)
        return render_template("templates/index.html", templates=templates)

    @app.post("/directories/templates/create")
    def templates_create():
        name = request.form.get("name", "").strip()
        if name:
            with db() as conn:
                repo.create_sport_template(conn, name)
                templates = repo.list_sport_templates(conn)
            if request.headers.get("HX-Request") == "true":
                return render_template("templates/_table.html", templates=templates)
        return redirect(url_for("templates_page"))

    @app.post("/directories/templates/seed-rugby")
    def templates_seed_rugby():
        with db() as conn:
            seed_rugby_template(conn)
            templates = repo.list_sport_templates(conn)
        if request.headers.get("HX-Request") == "true":
            return render_template("templates/_table.html", templates=templates)
        return redirect(url_for("templates_page"))

    @app.post("/directories/templates/<int:template_id>/delete")
    def templates_delete(template_id: int):
        try:
            with db() as conn:
                repo.delete_sport_template(conn, template_id)
                templates = repo.list_sport_templates(conn)
            if request.headers.get("HX-Request") == "true":
                return render_template("templates/_table.html", templates=templates)
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("templates_page"))

    @app.get("/directories/templates/<int:template_id>")
    def template_detail(template_id: int):
        with db() as conn:
            template = repo.get_sport_template(conn, template_id)
            categories = repo.list_categories_by_template(conn, template_id)
            actions = {int(c["Id"]): repo.list_actions_by_category(conn, int(c["Id"])) for c in categories}
            comments: dict[int, list[sqlite3.Row]] = {}
            for cat_actions in actions.values():
                for action in cat_actions:
                    comments[int(action["Id"])] = repo.list_comments_by_action(conn, int(action["Id"]))
        if not template:
            return redirect(url_for("templates_page"))
        return render_template(
            "templates/detail.html",
            template=template,
            categories=categories,
            actions=actions,
            comments=comments,
        )

    @app.post("/directories/templates/<int:template_id>/categories/create")
    def template_create_category(template_id: int):
        name = request.form.get("name", "").strip()
        if name:
            with db() as conn:
                sort_order = len(repo.list_categories_by_template(conn, template_id))
                repo.create_category(conn, template_id, name, sort_order)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/categories/<int:category_id>/delete")
    def template_delete_category(template_id: int, category_id: int):
        with db() as conn:
            repo.delete_category(conn, category_id)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/categories/<int:category_id>/rename")
    def template_rename_category(template_id: int, category_id: int):
        name = request.form.get("name", "").strip()
        if name:
            with db() as conn:
                category = repo.get_category(conn, category_id)
                if category and int(category["SportTemplateId"]) == template_id:
                    repo.update_category_name(conn, category_id, name)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/categories/<int:category_id>/actions/create")
    def template_create_action(template_id: int, category_id: int):
        name = request.form.get("name", "").strip()
        color_class = request.form.get("colorClass", "handling").strip() or "handling"
        if name:
            with db() as conn:
                sort_order = len(repo.list_actions_by_category(conn, category_id))
                repo.create_action(conn, category_id, name, True, sort_order, color_class)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/rename")
    def template_rename_action(template_id: int, action_id: int):
        name = request.form.get("name", "").strip()
        if name:
            with db() as conn:
                repo.update_action_name(conn, action_id, name)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/move-category")
    def template_move_action(template_id: int, action_id: int):
        category_id = request.form.get("categoryId", type=int)
        if not category_id:
            return redirect(url_for("template_detail", template_id=template_id))
        with db() as conn:
            action = repo.get_action(conn, action_id)
            category = repo.get_category(conn, category_id)
            if not action or not category:
                return redirect(url_for("template_detail", template_id=template_id))
            if int(category["SportTemplateId"]) != template_id:
                return redirect(url_for("template_detail", template_id=template_id))
            current = repo.get_category(conn, int(action["CategoryId"]))
            if current and int(current["SportTemplateId"]) != template_id:
                return redirect(url_for("template_detail", template_id=template_id))
            if int(action["CategoryId"]) != category_id:
                repo.update_action_category(conn, action_id, category_id)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/toggle-outcome")
    def template_toggle_action_outcome(template_id: int, action_id: int):
        with db() as conn:
            action = repo.get_action(conn, action_id)
            if action:
                repo.update_action_has_outcome(conn, action_id, not bool(action["HasOutcome"]))
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/delete")
    def template_delete_action(template_id: int, action_id: int):
        with db() as conn:
            repo.delete_action(conn, action_id)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/comments/create")
    def template_create_comment(template_id: int, action_id: int):
        text = request.form.get("text", "").strip()
        if text:
            with db() as conn:
                sort_order = len(repo.list_comments_by_action(conn, action_id))
                repo.create_comment_template(conn, action_id, text, sort_order)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/comments/<int:comment_id>/delete")
    def template_delete_comment(template_id: int, comment_id: int):
        with db() as conn:
            repo.delete_comment_template(conn, comment_id)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/update-period-count")
    def template_update_period_count(template_id: int):
        period_count = request.form.get("periodCount", type=int)
        if period_count and period_count > 0:
            with db() as conn:
                repo.update_sport_template_period_count(conn, template_id, period_count)
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/categories/<int:category_id>/toggle-report")
    def template_toggle_category_report(template_id: int, category_id: int):
        show = request.form.get("showInReport") == "1"
        with db() as conn:
            category = repo.get_category(conn, category_id)
            if category and int(category["SportTemplateId"]) == template_id:
                repo.update_category_show_in_report(conn, category_id, show)
        if request.headers.get("HX-Request") == "true":
            return "", 204
        return redirect(url_for("template_detail", template_id=template_id))

    @app.post("/directories/templates/<int:template_id>/actions/<int:action_id>/toggle-report")
    def template_toggle_action_report(template_id: int, action_id: int):
        show = request.form.get("showInReport") == "1"
        with db() as conn:
            action = repo.get_action(conn, action_id)
            if action:
                category = repo.get_category(conn, int(action["CategoryId"]))
                if category and int(category["SportTemplateId"]) == template_id:
                    repo.update_action_show_in_report(conn, action_id, show)
        if request.headers.get("HX-Request") == "true":
            return "", 204
        return redirect(url_for("template_detail", template_id=template_id))

    # Teams
    @app.get("/directories/teams")
    def teams_page() -> str:
        with db() as conn:
            teams = repo.list_teams(conn)
        return render_template("teams/index.html", teams=teams)

    @app.post("/directories/teams/create")
    def teams_create():
        name = request.form.get("name", "").strip()
        if name:
            with db() as conn:
                repo.create_team(conn, name)
                teams = repo.list_teams(conn)
            if request.headers.get("HX-Request") == "true":
                return render_template("teams/_table.html", teams=teams)
        return redirect(url_for("teams_page"))

    @app.post("/directories/teams/<int:team_id>/delete")
    def teams_delete(team_id: int):
        try:
            with db() as conn:
                repo.delete_team(conn, team_id)
                teams = repo.list_teams(conn)
            if request.headers.get("HX-Request") == "true":
                return render_template("teams/_table.html", teams=teams)
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("teams_page"))

    @app.get("/directories/teams/<int:team_id>")
    def team_detail(team_id: int):
        show_inactive = request.args.get("show_inactive") == "1"
        with db() as conn:
            team = repo.get_team(conn, team_id)
            players = repo.list_players_by_team(conn, team_id, active_only=not show_inactive)
        if not team:
            return redirect(url_for("teams_page"))
        return render_template(
            "teams/detail.html",
            team=team,
            players=players,
            show_inactive=show_inactive,
        )

    def _team_detail_url(team_id: int, show_inactive: bool = False) -> str:
        if show_inactive:
            return url_for("team_detail", team_id=team_id, show_inactive=1)
        return url_for("team_detail", team_id=team_id)

    @app.post("/directories/teams/<int:team_id>/players/create")
    def team_create_player(team_id: int):
        name = request.form.get("name", "").strip()
        position = request.form.get("position", "").strip() or None
        show_inactive = request.form.get("showInactive") == "1"
        if name:
            with db() as conn:
                repo.create_player(conn, team_id, name, position)
        return redirect(_team_detail_url(team_id, show_inactive))

    @app.post("/directories/teams/<int:team_id>/players/<int:player_id>/delete")
    def team_delete_player(team_id: int, player_id: int):
        show_inactive = request.form.get("showInactive") == "1"
        try:
            with db() as conn:
                player = repo.get_player(conn, player_id)
                if not player or int(player["TeamId"]) != team_id:
                    flash("Игрок не найден.", "error")
                    return redirect(_team_detail_url(team_id, show_inactive))
                repo.delete_player(conn, player_id)
            flash("Игрок удалён.", "ok")
        except sqlite3.IntegrityError:
            flash("Не удалось удалить игрока: есть связанные данные.", "error")
        return redirect(_team_detail_url(team_id, show_inactive))

    @app.get("/directories/teams/<int:team_id>/players/<int:player_id>/edit")
    def team_edit_player(team_id: int, player_id: int):
        with db() as conn:
            team = repo.get_team(conn, team_id)
            player = repo.get_player(conn, player_id)
            if not team or not player or int(player["TeamId"]) != team_id:
                return redirect(url_for("teams_page"))
            last_matches = repo.get_player_last_match_ids(conn, player_id, limit=5)
            stats_rows = repo.get_player_last5_stats(conn, player_id)
            player_stats = build_report_summary(stats_rows)
        return render_template(
            "teams/player_edit.html",
            team=team,
            player=player,
            last_matches=last_matches,
            player_stats=player_stats,
        )

    @app.post("/directories/teams/<int:team_id>/players/<int:player_id>/update")
    def team_update_player(team_id: int, player_id: int):
        name = request.form.get("name", "").strip()
        full_name = request.form.get("fullName", "").strip() or None
        birth_day = request.form.get("birthDay", "").strip() or None
        position = request.form.get("position", "").strip() or None
        is_active = request.form.get("isActive") == "1"
        if not name:
            flash("Укажите короткое имя игрока.", "error")
            return redirect(url_for("team_edit_player", team_id=team_id, player_id=player_id))
        with db() as conn:
            player = repo.get_player(conn, player_id)
            if not player or int(player["TeamId"]) != team_id:
                return redirect(url_for("teams_page"))
            repo.update_player(conn, player_id, name, full_name, birth_day, position, is_active)
        flash("Данные игрока сохранены.", "ok")
        return redirect(url_for("team_edit_player", team_id=team_id, player_id=player_id))

    # Squads
    @app.get("/directories/squads")
    def squads_page():
        edit_id = request.args.get("edit", type=int)
        with db() as conn:
            teams = repo.list_teams(conn)
            squads = repo.list_squads(conn)
            editing_squad = repo.get_squad(conn, edit_id) if edit_id else None
            team_players = (
                repo.list_players_by_team(conn, int(editing_squad["TeamId"]), active_only=True)
                if editing_squad
                else []
            )
            squad_players = repo.list_squad_players(conn, edit_id) if edit_id else []
            tournaments = repo.get_tournaments(conn)
        return render_template(
            "squads/index.html",
            teams=teams,
            squads=squads,
            tournaments=tournaments,
            editing_squad=editing_squad,
            team_players=team_players,
            squad_players=squad_players,
        )

    @app.post("/directories/squads/create")
    def squads_create():
        team_id = request.form.get("teamId", type=int)
        name = request.form.get("name", "").strip()
        tournament = request.form.get("tournament", "").strip() or None
        if team_id and name:
            with db() as conn:
                repo.create_squad(conn, team_id, name, tournament)
        return redirect(url_for("squads_page"))

    @app.post("/directories/squads/<int:squad_id>/update")
    def squads_update(squad_id: int):
        name = request.form.get("name", "").strip() or None
        tournament = request.form.get("tournament", "").strip() or None
        with db() as conn:
            repo.update_squad(conn, squad_id, name, tournament)
        return redirect(url_for("squads_page", edit=squad_id))

    @app.post("/directories/squads/<int:squad_id>/delete")
    def squads_delete(squad_id: int):
        with db() as conn:
            repo.delete_squad(conn, squad_id)
        return redirect(url_for("squads_page"))

    @app.post("/directories/squads/<int:squad_id>/players/add")
    def squads_add_player(squad_id: int):
        player_id = request.form.get("playerId", type=int)
        if player_id:
            with db() as conn:
                if not repo.is_player_active(conn, player_id):
                    flash("Неактивного игрока нельзя добавить в состав.", "error")
                    return redirect(url_for("squads_page", edit=squad_id))
                sort_order = len(repo.list_squad_players(conn, squad_id))
                repo.add_squad_player(conn, squad_id, player_id, sort_order)
        return redirect(url_for("squads_page", edit=squad_id))

    @app.post("/directories/squads/<int:squad_id>/players/<int:row_id>/toggle-role")
    def squads_toggle_role(squad_id: int, row_id: int):
        with db() as conn:
            rows = repo.list_squad_players(conn, squad_id)
            row = next((r for r in rows if int(r["Id"]) == row_id), None)
            if row:
                next_role = "substitute" if row["LineupRole"] == "starter" else "starter"
                repo.update_squad_player_role(conn, row_id, next_role)
        return redirect(url_for("squads_page", edit=squad_id))

    @app.post("/directories/squads/<int:squad_id>/players/<int:row_id>/delete")
    def squads_delete_player(squad_id: int, row_id: int):
        with db() as conn:
            repo.delete_squad_player(conn, row_id)
        return redirect(url_for("squads_page", edit=squad_id))

    # Matches
    @app.get("/matches")
    def matches_page():
        with db() as conn:
            templates = repo.list_sport_templates(conn)
            teams = repo.list_teams(conn)
            matches = repo.list_matches(conn)
            tournaments = repo.get_tournaments(conn)
            scores = {int(m["Id"]): calculate_match_score_for_match(conn, int(m["Id"])) for m in matches}
        return render_template(
            "matches/index.html",
            templates=templates,
            teams=teams,
            matches=matches,
            tournaments=tournaments,
            scores=scores,
        )

    @app.post("/matches/create")
    def matches_create():
        sport_template_id = request.form.get("sportTemplateId", type=int)
        home_team_id = request.form.get("homeTeamId", type=int)
        away_team_id = request.form.get("awayTeamId", type=int)
        match_date = request.form.get("matchDate", "").strip()
        tournament = request.form.get("tournament", "").strip() or None
        score_home = request.form.get("scoreHome", "").strip()
        score_away = request.form.get("scoreAway", "").strip()
        if sport_template_id and home_team_id and away_team_id and match_date:
            with db() as conn:
                match_id = repo.create_match(
                    conn,
                    sport_template_id,
                    home_team_id,
                    away_team_id,
                    match_date,
                    tournament,
                    int(score_home) if score_home else None,
                    int(score_away) if score_away else None,
                )
                repo.create_match_periods(conn, match_id)
        return redirect(url_for("matches_page"))

    @app.post("/matches/<int:match_id>/delete")
    def matches_delete(match_id: int):
        with db() as conn:
            repo.delete_match(conn, match_id)
        return redirect(url_for("matches_page"))

    @app.get("/matches/<int:match_id>/setup")
    def match_setup(match_id: int):
        with db() as conn:
            match = repo.get_match(conn, match_id)
            if not match:
                return redirect(url_for("matches_page"))
            teams = repo.list_teams(conn)
            squads = repo.list_squads(conn)
            lineups = repo.list_match_lineup(conn, match_id)
            players = repo.list_players(conn)
            tournaments = repo.get_tournaments(conn)
            score = calculate_match_score_for_match(conn, match_id)
        return render_template(
            "matches/setup.html",
            match=match,
            teams=teams,
            squads=squads,
            lineups=lineups,
            players=players,
            tournaments=tournaments,
            score=score,
        )

    @app.post("/matches/<int:match_id>/setup/update-details")
    def match_setup_update_details(match_id: int):
        match_date = request.form.get("matchDate", "").strip()
        tournament = request.form.get("tournament", "").strip() or None
        if not match_date:
            flash("Укажите дату матча.", "error")
            return redirect(url_for("match_setup", match_id=match_id))
        with db() as conn:
            if not repo.get_match(conn, match_id):
                return redirect(url_for("matches_page"))
            repo.update_match_details(conn, match_id, match_date, tournament)
        flash("Сведения о матче сохранены.", "ok")
        return redirect(url_for("match_setup", match_id=match_id))

    @app.post("/matches/<int:match_id>/setup/apply-squad")
    def match_setup_apply_squad(match_id: int):
        squad_id = request.form.get("squadId", type=int)
        side = request.form.get("side", "").strip()
        if squad_id and side in ("home", "away"):
            with db() as conn:
                copy_squad_to_match_lineup(conn, match_id, squad_id, side)
        return redirect(url_for("match_setup", match_id=match_id))

    @app.post("/matches/<int:match_id>/setup/toggle-lineup-role")
    def match_setup_toggle_lineup_role(match_id: int):
        row_id = request.form.get("rowId", type=int)
        if row_id:
            with db() as conn:
                rows = repo.list_match_lineup(conn, match_id)
                row = next((r for r in rows if int(r["Id"]) == row_id), None)
                if row:
                    next_role = "substitute" if row["LineupRole"] == "starter" else "starter"
                    repo.update_match_lineup_role(conn, row_id, next_role)
        return redirect(url_for("match_setup", match_id=match_id))

    # Tagging
    def _load_tagging_context(conn: sqlite3.Connection, match_id: int) -> dict[str, object] | None:
        match = repo.get_match(conn, match_id)
        if not match:
            return None
        teams = repo.list_teams(conn)
        players = repo.list_players(conn)
        lineups = repo.list_match_lineup(conn, match_id)
        events = repo.list_events_by_match(conn, match_id)
        categories = repo.list_categories_by_template(conn, int(match["SportTemplateId"]))
        actions: list[sqlite3.Row] = []
        comments: dict[int, list[sqlite3.Row]] = {}
        category_by_id = {int(c["Id"]): c for c in categories}
        for cat in categories:
            cat_actions = repo.list_actions_by_category(conn, int(cat["Id"]))
            actions.extend(cat_actions)
            for action in cat_actions:
                comments[int(action["Id"])] = repo.list_comments_by_action(conn, int(action["Id"]))
        score = calculate_match_score_for_match(conn, match_id)
        selected_event_id = session.get(f"selected_event_{match_id}")
        selected_event = next((e for e in events if int(e["Id"]) == selected_event_id), None)
        current_period = session.get(f"period_{match_id}", 1)
        selected_action = (
            next((a for a in actions if int(a["Id"]) == int(selected_event["ActionId"])), None)
            if selected_event and selected_event["ActionId"]
            else None
        )
        draft_mode = session.get(f"draft_mode_{match_id}", "new" if selected_event else None)
        if selected_event and draft_mode not in ("new", "edit"):
            draft_mode = "edit"
        draft_outcome = "—"
        if selected_event and selected_event["Outcome"]:
            draft_outcome = str(selected_event["Outcome"])
        scroll_focus = session.pop(f"scroll_focus_{match_id}", None)
        return {
            "match": match,
            "teams": teams,
            "players": players,
            "lineups": lineups,
            "events": events,
            "categories": categories,
            "actions": actions,
            "comments": comments,
            "category_by_id": category_by_id,
            "score": score,
            "selected_event_id": selected_event_id,
            "selected_event": selected_event,
            "selected_action": selected_action,
            "current_period": current_period,
            "draft_mode": draft_mode,
            "draft_player_label": _tagging_event_subject_name(selected_event, players, teams),
            "draft_action_label": selected_action["Name"] if selected_action else "—",
            "draft_outcome_label": draft_outcome,
            "scroll_focus": scroll_focus,
        }

    def _render_tagging_htmx_response(match_id: int):
        with db() as conn:
            context = _load_tagging_context(conn, match_id)
            if context is None:
                return "", 404
        return render_template("tagging/_htmx_swap.html", **context)

    @app.post("/tagging/<int:match_id>/set-period")
    def tagging_set_period(match_id: int):
        period = request.form.get("period", type=int)
        if period in (1, 2):
            session[f"period_{match_id}"] = period
            event_id = session.get(f"selected_event_{match_id}")
            if event_id:
                with db() as conn:
                    repo.update_event(conn, int(event_id), period_number=period)
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    @app.get("/tagging/<int:match_id>/control")
    def tagging_control(match_id: int):
        with db() as conn:
            context = _load_tagging_context(conn, match_id)
            if context is None:
                return redirect(url_for("matches_page"))
        return render_template("tagging/control.html", **context)

    @app.post("/tagging/<int:match_id>/capture")
    def tagging_capture(match_id: int):
        period = request.form.get("period", type=int) or session.get(f"period_{match_id}", 1)
        if period not in (1, 2):
            period = 1
        session[f"period_{match_id}"] = period
        timestamp_sec = request.form.get("timestampSec", type=int) or 0
        with db() as conn:
            event_id = repo.create_event(
                conn,
                match_id=match_id,
                period_number=period,
                timestamp_sec=timestamp_sec,
                subject_type="player",
            )
        session[f"selected_event_{match_id}"] = event_id
        session[f"draft_mode_{match_id}"] = "new"
        session[f"scroll_focus_{match_id}"] = "player"
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    @app.post("/tagging/<int:match_id>/event/update")
    def tagging_update_event(match_id: int):
        event_id = session.get(f"selected_event_{match_id}")
        if not event_id:
            return redirect(url_for("tagging_control", match_id=match_id))
        subject_type = request.form.get("subjectType")
        with db() as conn:
            repo.update_event(
                conn,
                int(event_id),
                period_number=request.form.get("period", type=int),
                subject_type=subject_type,
                player_id=request.form.get("playerId", type=int),
                team_id=request.form.get("teamId", type=int),
                action_id=request.form.get("actionId", type=int),
                outcome=request.form.get("outcome"),
                comment=request.form.get("comment"),
            )
            updated = conn.execute("SELECT * FROM Event WHERE Id = ?", (int(event_id),)).fetchone()
            action_id = request.form.get("actionId", type=int) or (int(updated["ActionId"]) if updated and updated["ActionId"] else None)
            selected_action = None
            if action_id:
                selected_action = conn.execute("SELECT * FROM Action WHERE Id = ?", (action_id,)).fetchone()
        focus = _tagging_scroll_focus_after_update(request.form, selected_action)
        if focus:
            session[f"scroll_focus_{match_id}"] = focus
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    @app.post("/tagging/<int:match_id>/event/<int:event_id>/select")
    def tagging_select_event(match_id: int, event_id: int):
        with db() as conn:
            row = conn.execute(
                "SELECT PeriodNumber FROM Event WHERE Id = ? AND MatchId = ?",
                (event_id, match_id),
            ).fetchone()
            selected_event = conn.execute(
                "SELECT * FROM Event WHERE Id = ? AND MatchId = ?",
                (event_id, match_id),
            ).fetchone()
            selected_action = None
            if selected_event and selected_event["ActionId"]:
                selected_action = conn.execute(
                    "SELECT * FROM Action WHERE Id = ?",
                    (int(selected_event["ActionId"]),),
                ).fetchone()
        if row:
            session[f"period_{match_id}"] = int(row["PeriodNumber"])
        session[f"selected_event_{match_id}"] = event_id
        session[f"draft_mode_{match_id}"] = "edit"
        focus = _tagging_scroll_focus_incomplete(selected_event, selected_action)
        if focus:
            session[f"scroll_focus_{match_id}"] = focus
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    @app.post("/tagging/<int:match_id>/event/<int:event_id>/delete")
    def tagging_delete_event(match_id: int, event_id: int):
        with db() as conn:
            repo.delete_event(conn, event_id)
        if session.get(f"selected_event_{match_id}") == event_id:
            session[f"selected_event_{match_id}"] = None
            session.pop(f"draft_mode_{match_id}", None)
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    @app.get("/tagging/<int:match_id>/video")
    def tagging_video(match_id: int):
        return render_template("tagging/video.html", match_id=match_id)

    @app.get("/tagging/<int:match_id>/export.csv")
    def tagging_export_csv(match_id: int):
        with db() as conn:
            csv_text = build_csv(conn, match_id)
            filename = build_export_filename(conn, match_id)
        return (
            csv_text,
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": export_content_disposition(filename),
            },
        )

    @app.post("/tagging/<int:match_id>/import-csv")
    def tagging_import_csv(match_id: int):
        file = request.files.get("csvFile")
        mode = request.form.get("mode", "append")
        if not file:
            flash("Не выбран CSV файл.", "error")
            return redirect(url_for("tagging_control", match_id=match_id))
        with db() as conn:
            existing_events = repo.count_events_by_match(conn, match_id)
            if existing_events > 0 and mode not in ("append", "replace"):
                flash("Для непустого матча выберите режим append или replace.", "error")
                return redirect(url_for("tagging_control", match_id=match_id))
            count, errors = import_csv_events(conn, match_id, file.read(), mode if existing_events > 0 else "append")
            if errors:
                flash(f"Импорт не выполнен: {len(errors)} ошибок.", "error")
                for err in errors[:10]:
                    flash(err, "error")
                if len(errors) > 10:
                    flash(f"... и ещё {len(errors) - 10} ошибок.", "error")
            else:
                flash(f"Импортировано событий: {count}.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _render_tagging_htmx_response(match_id)
        return redirect(url_for("tagging_control", match_id=match_id))

    # Reports
    @app.route("/reports", methods=["GET", "POST"])
    def reports_page():
        default_from = date.today().replace(month=1, day=1).isoformat()
        default_to = date.today().isoformat()
        report_type = request.values.get("reportType", "team")
        team_id = request.values.get("teamId", type=int)
        player_id = request.values.get("playerId", type=int)
        date_from = request.values.get("dateFrom", default_from) or default_from
        date_to = request.values.get("dateTo", default_to) or default_to
        by_match = request.values.get("byMatch") == "1"
        tournament_raw = request.values.get("tournamentId", "")
        tournament_id = int(tournament_raw) if tournament_raw else None

        with db() as conn:
            teams = repo.list_teams(conn)
            players = repo.list_players(conn)
            tournaments = repo.get_tournaments(conn)
            primary_team_id = repo.get_primary_team_id(conn)
            teams_by_id = {int(t["Id"]): t for t in teams}

            if request.method == "GET" and report_type == "team" and not team_id and primary_team_id:
                team_id = primary_team_id

            report_summary = None
            report_sections = None
            generated = False

            if request.method == "POST":
                subject_type = None
                subject_id = None
                if report_type == "team" and team_id:
                    subject_type, subject_id = "team", team_id
                elif report_type == "individual" and player_id:
                    subject_type, subject_id = "player", player_id

                if subject_type and subject_id:
                    rows = repo.get_report_data(
                        conn,
                        subject_type,
                        subject_id,
                        date_from,
                        date_to,
                        by_match=by_match,
                        tournament_id=tournament_id,
                    )
                    generated = True
                    if by_match:
                        report_sections = build_report_by_match(rows, teams_by_id)
                    else:
                        report_summary = build_report_summary(rows)

        return render_template(
            "reports.html",
            teams=teams,
            players=players,
            tournaments=tournaments,
            report_type=report_type,
            team_id=team_id,
            player_id=player_id,
            date_from=date_from,
            date_to=date_to,
            by_match=by_match,
            tournament_id=tournament_id,
            report_summary=report_summary,
            report_sections=report_sections,
            generated=generated,
            primary_team_id=primary_team_id,
        )

    @app.get("/reports/comment-detail")
    def reports_comment_detail():
        action_id = request.args.get("actionId", type=int)
        subject_type = request.args.get("subjectType", "")
        subject_id = request.args.get("subjectId", type=int)
        date_from = request.args.get("dateFrom", "")
        date_to = request.args.get("dateTo", "")
        tournament_raw = request.args.get("tournamentId", "")
        tournament_id = int(tournament_raw) if tournament_raw else None
        match_id = request.args.get("matchId", type=int)

        if not action_id or subject_type not in ("team", "player") or not subject_id:
            return "", 400
        if not date_from or not date_to:
            return "", 400

        with db() as conn:
            action = repo.get_action(conn, action_id)
            if not action:
                return "", 404
            rows = repo.get_report_comment_detail(
                conn,
                action_id,
                subject_type,
                subject_id,
                date_from,
                date_to,
                tournament_id=tournament_id,
                match_id=match_id,
            )

        return render_template(
            "_report_comment_detail.html",
            action=action,
            rows=rows,
        )

    def _report_player_breakdown_context(
        conn: sqlite3.Connection,
        action_id: int,
        team_id: int,
        date_from: str,
        date_to: str,
        *,
        tournament_id: int | None,
        match_id: int | None,
    ) -> dict[str, object] | None:
        action = repo.get_action(conn, action_id)
        if not action:
            return None
        category = repo.get_category(conn, int(action["CategoryId"]))
        rows = repo.get_report_player_detail(
            conn,
            action_id,
            team_id,
            date_from,
            date_to,
            tournament_id=tournament_id,
            match_id=match_id,
        )
        match_label = None
        if match_id:
            match = repo.get_match(conn, match_id)
            if match:
                home = repo.get_team(conn, int(match["HomeTeamId"]))
                away = repo.get_team(conn, int(match["AwayTeamId"]))
                home_name = home["Name"] if home else "?"
                away_name = away["Name"] if away else "?"
                match_label = f"{match['MatchDate']} — {home_name} — {away_name}"
        return {
            "mode": "action-breakdown",
            "action": action,
            "category": category,
            "rows": build_player_detail(rows, has_outcome=bool(action["HasOutcome"])),
            "match_label": match_label,
        }

    @app.get("/reports/player-panel")
    def reports_player_panel():
        mode = request.args.get("mode", "empty")
        if mode == "empty":
            return render_template("_report_player_panel.html", mode="empty")

        if mode != "action-breakdown":
            return "", 400

        action_id = request.args.get("actionId", type=int)
        team_id = request.args.get("teamId", type=int)
        date_from = request.args.get("dateFrom", "")
        date_to = request.args.get("dateTo", "")
        tournament_raw = request.args.get("tournamentId", "")
        tournament_id = int(tournament_raw) if tournament_raw else None
        match_id = request.args.get("matchId", type=int)

        if not action_id or not team_id or not date_from or not date_to:
            return "", 400

        with db() as conn:
            ctx = _report_player_breakdown_context(
                conn,
                action_id,
                team_id,
                date_from,
                date_to,
                tournament_id=tournament_id,
                match_id=match_id,
            )
            if ctx is None:
                return "", 404

        return render_template("_report_player_panel.html", **ctx)

    @app.get("/reports/player-detail")
    def reports_player_detail():
        action_id = request.args.get("actionId", type=int)
        subject_type = request.args.get("subjectType", "")
        subject_id = request.args.get("subjectId", type=int)
        date_from = request.args.get("dateFrom", "")
        date_to = request.args.get("dateTo", "")
        tournament_raw = request.args.get("tournamentId", "")
        tournament_id = int(tournament_raw) if tournament_raw else None
        match_id = request.args.get("matchId", type=int)

        if not action_id or subject_type != "team" or not subject_id:
            return "", 400
        if not date_from or not date_to:
            return "", 400

        with db() as conn:
            ctx = _report_player_breakdown_context(
                conn,
                action_id,
                subject_id,
                date_from,
                date_to,
                tournament_id=tournament_id,
                match_id=match_id,
            )
            if ctx is None:
                return "", 404

        return render_template("_report_player_panel.html", **ctx)

    # Settings
    @app.route("/settings", methods=["GET", "POST"])
    def settings_page():
        with db() as conn:
            teams = repo.list_teams(conn)
            if request.method == "POST":
                raw = request.form.get("primaryTeamId", "").strip()
                team_id = int(raw) if raw else None
                try:
                    repo.set_primary_team_id(conn, team_id)
                except ValueError as exc:
                    flash(str(exc), "error")
                    return redirect(url_for("settings_page"))
                flash("Настройки сохранены.", "ok")
                return redirect(url_for("settings_page"))
            primary_team_id = repo.get_primary_team_id(conn)
        return render_template(
            "settings/index.html",
            teams=teams,
            primary_team_id=primary_team_id,
        )

    # Administration
    @app.get("/admin")
    def admin_page():
        return render_template("admin/index.html")

    @app.get("/admin/export-db")
    def admin_export_db():
        db_path = app.config["DB_PATH"]
        filename = f"SportsVideoLogger_{date.today().isoformat()}.db"
        return send_file(db_path, as_attachment=True, download_name=filename)

    @app.post("/admin/import-db")
    def admin_import_db():
        upload = request.files.get("dbFile")
        if not upload:
            flash("Выберите .db файл для импорта.", "error")
            return redirect(url_for("admin_page"))
        db_path: Path = app.config["DB_PATH"]
        tmp_path = db_path.with_suffix(".import.tmp")
        backup_path = db_path.with_suffix(f".backup-{date.today().isoformat()}.db")
        try:
            upload.save(tmp_path)
            validate_sqlite_file(tmp_path)
            if db_path.exists():
                shutil.copy2(db_path, backup_path)
            restore_database_from_file(db_path, tmp_path)
            flash("Импорт завершён. Обновите страницу (F5).", "ok")
        except (sqlite3.DatabaseError, OSError, ValueError):
            flash("Файл не является валидной SQLite базой.", "error")
        except Exception as exc:
            flash(f"Ошибка импорта: {exc}", "error")
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
        return redirect(url_for("admin_page"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

