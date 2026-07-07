from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sports_logger.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS SportTemplate (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  Name TEXT NOT NULL,
  PeriodCount INTEGER NOT NULL DEFAULT 2,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS Category (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  SortOrder INTEGER NOT NULL DEFAULT 0,
  ShowInReport INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Action (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  CategoryId INTEGER NOT NULL REFERENCES Category(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  HasOutcome INTEGER NOT NULL DEFAULT 1,
  SortOrder INTEGER NOT NULL DEFAULT 0,
  ColorClass TEXT,
  ShowInReport INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS CommentTemplate (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ActionId INTEGER NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
  Text TEXT NOT NULL,
  SortOrder INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Team (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  Name TEXT NOT NULL,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS Player (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  TeamId INTEGER NOT NULL REFERENCES Team(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  FullName TEXT,
  BirthDay TEXT,
  DefaultPosition TEXT,
  IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Tournament (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  Name TEXT NOT NULL UNIQUE,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS Squad (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  TeamId INTEGER NOT NULL REFERENCES Team(Id) ON DELETE CASCADE,
  Name TEXT NOT NULL,
  TournamentId INTEGER REFERENCES Tournament(Id) ON DELETE SET NULL,
  Note TEXT,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS SquadPlayer (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  SquadId INTEGER NOT NULL REFERENCES Squad(Id) ON DELETE CASCADE,
  PlayerId INTEGER NOT NULL REFERENCES Player(Id) ON DELETE CASCADE,
  Position TEXT,
  LineupRole TEXT NOT NULL DEFAULT 'starter' CHECK (LineupRole IN ('starter', 'substitute')),
  SortOrder INTEGER NOT NULL DEFAULT 0,
  UNIQUE (SquadId, PlayerId)
);

CREATE TABLE IF NOT EXISTS Match (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  SportTemplateId INTEGER NOT NULL REFERENCES SportTemplate(Id),
  HomeTeamId INTEGER NOT NULL REFERENCES Team(Id),
  AwayTeamId INTEGER NOT NULL REFERENCES Team(Id),
  MatchDate TEXT NOT NULL,
  TournamentId INTEGER REFERENCES Tournament(Id) ON DELETE SET NULL,
  ScoreHome INTEGER,
  ScoreAway INTEGER,
  HomeSquadId INTEGER REFERENCES Squad(Id) ON DELETE SET NULL,
  AwaySquadId INTEGER REFERENCES Squad(Id) ON DELETE SET NULL,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS MatchLineup (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchId INTEGER NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
  TeamId INTEGER NOT NULL REFERENCES Team(Id),
  PlayerId INTEGER NOT NULL REFERENCES Player(Id),
  Position TEXT,
  LineupRole TEXT NOT NULL DEFAULT 'starter' CHECK (LineupRole IN ('starter', 'substitute')),
  SortOrder INTEGER NOT NULL DEFAULT 0,
  UNIQUE (MatchId, TeamId, PlayerId)
);

CREATE TABLE IF NOT EXISTS MatchPeriod (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchId INTEGER NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
  PeriodNumber INTEGER NOT NULL,
  Label TEXT,
  UNIQUE (MatchId, PeriodNumber)
);

CREATE TABLE IF NOT EXISTS Event (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchId INTEGER NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
  PeriodNumber INTEGER NOT NULL,
  TimestampSec INTEGER NOT NULL,
  SubjectType TEXT NOT NULL CHECK (SubjectType IN ('player', 'team')),
  PlayerId INTEGER REFERENCES Player(Id),
  TeamId INTEGER REFERENCES Team(Id),
  ActionId INTEGER REFERENCES Action(Id),
  Outcome TEXT CHECK (Outcome IN ('Success', 'Failure') OR Outcome IS NULL),
  Comment TEXT,
  CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (
    (SubjectType = 'player' AND TeamId IS NULL) OR
    (SubjectType = 'team' AND PlayerId IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS IX_Player_TeamId ON Player(TeamId);
CREATE INDEX IF NOT EXISTS IX_Squad_TeamId ON Squad(TeamId);
CREATE INDEX IF NOT EXISTS IX_SquadPlayer_SquadId ON SquadPlayer(SquadId);
CREATE INDEX IF NOT EXISTS IX_Match_HomeTeamId ON Match(HomeTeamId);
CREATE INDEX IF NOT EXISTS IX_Match_AwayTeamId ON Match(AwayTeamId);
CREATE INDEX IF NOT EXISTS IX_MatchLineup_MatchId ON MatchLineup(MatchId);
CREATE INDEX IF NOT EXISTS IX_Event_MatchId ON Event(MatchId);

CREATE TABLE IF NOT EXISTS AppSetting (
  Key TEXT PRIMARY KEY,
  Value TEXT
);
"""


def backup_database_file(db_path: Path, *, reason: str = "schema") -> Path | None:
    """Copy the live SQLite file before structural changes."""
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.backup-{reason}-{stamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def _pending_migrations(conn: sqlite3.Connection) -> bool:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(Player)")}
    if "FullName" not in columns or "BirthDay" not in columns:
        return True
    match_columns = {row[1] for row in conn.execute("PRAGMA table_info(Match)")}
    if "TournamentId" not in match_columns:
        return True
    category_columns = {row[1] for row in conn.execute("PRAGMA table_info(Category)")}
    if "ShowInReport" not in category_columns:
        return True
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='AppSetting'"
        )
    }
    if "AppSetting" not in tables:
        return True
    return False


def _apply_migrations(conn: sqlite3.Connection) -> None:
    _migrate_player_profile(conn)
    _migrate_tournament_refactor(conn)
    _migrate_phase2_reports(conn)
    _migrate_app_settings(conn)


def ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists() and db_path.stat().st_size > 0:
        with sqlite3.connect(db_path) as conn:
            if _pending_migrations(conn):
                backup_database_file(db_path, reason="pre-migrate")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _apply_migrations(conn)
        conn.commit()


def _migrate_player_profile(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(Player)")}
    if "FullName" not in columns:
        conn.execute("ALTER TABLE Player ADD COLUMN FullName TEXT")
    if "BirthDay" not in columns:
        conn.execute("ALTER TABLE Player ADD COLUMN BirthDay TEXT")


def _sqlite_supports_drop_column(conn: sqlite3.Connection) -> bool:
    version = conn.execute("SELECT sqlite_version()").fetchone()[0]
    parts = tuple(int(x) for x in version.split("."))
    return parts >= (3, 35, 0)


def _migrate_tournament_refactor(conn: sqlite3.Connection) -> None:
    match_columns = {row[1] for row in conn.execute("PRAGMA table_info(Match)")}
    if "TournamentId" in match_columns:
        return

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Tournament (
          Id INTEGER PRIMARY KEY AUTOINCREMENT,
          Name TEXT NOT NULL UNIQUE,
          CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO Tournament (Name)
        SELECT DISTINCT Tournament FROM Match
        WHERE Tournament IS NOT NULL AND trim(Tournament) != ''
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO Tournament (Name)
        SELECT DISTINCT Tournament FROM Squad
        WHERE Tournament IS NOT NULL AND trim(Tournament) != ''
        """
    )

    conn.execute("ALTER TABLE Match ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id)")
    conn.execute(
        """
        UPDATE Match SET TournamentId = (
          SELECT Id FROM Tournament WHERE Name = Match.Tournament
        )
        WHERE Tournament IS NOT NULL AND trim(Tournament) != ''
        """
    )

    squad_columns = {row[1] for row in conn.execute("PRAGMA table_info(Squad)")}
    if "TournamentId" not in squad_columns:
        conn.execute("ALTER TABLE Squad ADD COLUMN TournamentId INTEGER REFERENCES Tournament(Id)")
    conn.execute(
        """
        UPDATE Squad SET TournamentId = (
          SELECT Id FROM Tournament WHERE Name = Squad.Tournament
        )
        WHERE Tournament IS NOT NULL AND trim(Tournament) != ''
        """
    )

    if _sqlite_supports_drop_column(conn):
        if "Tournament" in match_columns:
            conn.execute("ALTER TABLE Match DROP COLUMN Tournament")
        squad_columns = {row[1] for row in conn.execute("PRAGMA table_info(Squad)")}
        if "Tournament" in squad_columns:
            conn.execute("ALTER TABLE Squad DROP COLUMN Tournament")


def _migrate_phase2_reports(conn: sqlite3.Connection) -> None:
    template_columns = {row[1] for row in conn.execute("PRAGMA table_info(SportTemplate)")}
    if "PeriodCount" not in template_columns:
        conn.execute("ALTER TABLE SportTemplate ADD COLUMN PeriodCount INTEGER NOT NULL DEFAULT 2")

    category_columns = {row[1] for row in conn.execute("PRAGMA table_info(Category)")}
    if "ShowInReport" not in category_columns:
        conn.execute("ALTER TABLE Category ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1")

    action_columns = {row[1] for row in conn.execute("PRAGMA table_info(Action)")}
    if "ShowInReport" not in action_columns:
        conn.execute("ALTER TABLE Action ADD COLUMN ShowInReport INTEGER NOT NULL DEFAULT 1")


def _migrate_app_settings(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS AppSetting (
          Key TEXT PRIMARY KEY,
          Value TEXT
        )
        """
    )


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def validate_sqlite_file(path: Path) -> None:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    finally:
        conn.close()


def restore_database_from_file(db_path: Path, source_path: Path) -> None:
    """Copy all pages from source into the live DB file (safe on Windows)."""
    src = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(db_path)
        try:
            src.backup(dst)
            dst.commit()
        finally:
            dst.close()
    finally:
        src.close()

