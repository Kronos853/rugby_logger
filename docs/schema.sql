/*
  Sports Video Logger — logical schema (MS SQL style)
  MVP: Dexie.js / IndexedDB  |  Future: PostgreSQL

  Naming: PascalCase tables (MS SQL habit); maps 1:1 to Postgres with quoted identifiers or snake_case.
*/

-- =============================================================================
-- SPORT TAXONOMY (шаблоны видов спорта)
-- =============================================================================

CREATE TABLE SportTemplate (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    Name            NVARCHAR(100)   NOT NULL,          -- e.g. N'Регби-7'
    PeriodCount     INT             NOT NULL DEFAULT 2,
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE Category (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SportTemplateId INT             NOT NULL REFERENCES SportTemplate(Id),
    Name            NVARCHAR(100)   NOT NULL,          -- e.g. N'Handling'
    SortOrder       INT             NOT NULL DEFAULT 0,
    ShowInReport    BIT             NOT NULL DEFAULT 1
);

CREATE TABLE Action (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    CategoryId      INT             NOT NULL REFERENCES Category(Id),
    Name            NVARCHAR(100)   NOT NULL,          -- e.g. N'Pass (success)'
    HasOutcome      BIT             NOT NULL DEFAULT 1,-- успех/провал опционален на уровне UI
    SortOrder       INT             NOT NULL DEFAULT 0,
    ShowInReport    BIT             NOT NULL DEFAULT 1
);

CREATE TABLE CommentTemplate (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    ActionId        INT             NOT NULL REFERENCES Action(Id),
    Text            NVARCHAR(500)   NOT NULL,          -- текст кнопки-подсказки
    SortOrder       INT             NOT NULL DEFAULT 0
);

-- Метрики командной статистики матча (конструктор на уровне шаблона)
CREATE TABLE TeamStatMetric (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SportTemplateId INT             NOT NULL REFERENCES SportTemplate(Id) ON DELETE CASCADE,
    Name            NVARCHAR(100)   NOT NULL,
    ActionId        INT             NOT NULL REFERENCES Action(Id) ON DELETE CASCADE,
    OutcomeFilter   VARCHAR(10)     NOT NULL DEFAULT 'any'
                    CHECK (OutcomeFilter IN ('any', 'Success', 'Failure')),
    SortOrder       INT             NOT NULL DEFAULT 0
);

-- =============================================================================
-- TOURNAMENTS (справочник турниров)
-- =============================================================================

CREATE TABLE Tournament (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    Name            NVARCHAR(200)   NOT NULL UNIQUE,
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);

-- =============================================================================
-- TEAMS & PLAYERS (справочник команд)
-- =============================================================================

CREATE TABLE Team (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    Name            NVARCHAR(200)   NOT NULL,
    -- Команда может существовать без игроков (соперник, «Команда» для командных действий)
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE Player (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    TeamId          INT             NOT NULL REFERENCES Team(Id),
    Name            NVARCHAR(200)   NOT NULL,              -- короткое имя (кнопки разметки)
    FullName        NVARCHAR(300)   NULL,                  -- полное имя
    BirthDay        DATE            NULL,                  -- дата рождения
    DefaultPosition NVARCHAR(50)    NULL,              -- позиция по умолчанию в заявке команды
    IsActive        BIT             NOT NULL DEFAULT 1
);

-- =============================================================================
-- SQUADS (сохранённые составы — переиспользуемые наборы игроков)
-- Отдельная сущность: составы с разных турниров, выбираются целиком для матча
-- =============================================================================

CREATE TABLE Squad (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    TeamId          INT             NOT NULL REFERENCES Team(Id),
    Name            NVARCHAR(200)   NOT NULL,          -- e.g. N'Весна 2025', N'Чемпионат U-15'
    TournamentId    INT             NULL REFERENCES Tournament(Id),
    Note            NVARCHAR(500)   NULL,
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE SquadPlayer (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SquadId         INT             NOT NULL REFERENCES Squad(Id) ON DELETE CASCADE,
    PlayerId        INT             NOT NULL REFERENCES Player(Id),
    Position        NVARCHAR(50)    NULL,              -- позиция в ЭТОМ составе (может отличаться)
    LineupRole      VARCHAR(20)     NOT NULL DEFAULT 'starter'
                    CHECK (LineupRole IN ('starter', 'substitute')),  -- основной / замена
    SortOrder       INT             NOT NULL DEFAULT 0,
    CONSTRAINT UQ_SquadPlayer UNIQUE (SquadId, PlayerId)
);

-- =============================================================================
-- MATCHES
-- =============================================================================

CREATE TABLE Match (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    SportTemplateId INT             NOT NULL REFERENCES SportTemplate(Id),
    HomeTeamId      INT             NOT NULL REFERENCES Team(Id),
    AwayTeamId      INT             NOT NULL REFERENCES Team(Id),
    MatchDate       DATE            NOT NULL,
    TournamentId    INT             NULL REFERENCES Tournament(Id),
    ScoreHome       INT             NULL,
    ScoreAway       INT             NULL,
    -- Ссылка на состав-источник (для истории); разметка идёт по MatchLineup (снимок)
    HomeSquadId     INT             NULL REFERENCES Squad(Id),
    AwaySquadId     INT             NULL REFERENCES Squad(Id),
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Снимок состава на матч (копируется из Squad при подготовке матча)
-- Даже если Squad потом изменится, статистика матча не «поплывёт»
CREATE TABLE MatchLineup (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    MatchId         INT             NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
    TeamId          INT             NOT NULL REFERENCES Team(Id),
    PlayerId        INT             NOT NULL REFERENCES Player(Id),
    Position        NVARCHAR(50)    NULL,
    LineupRole      VARCHAR(20)     NOT NULL DEFAULT 'starter'
                    CHECK (LineupRole IN ('starter', 'substitute')),  -- основной / замена
    SortOrder       INT             NOT NULL DEFAULT 0,
    CONSTRAINT UQ_MatchLineup UNIQUE (MatchId, TeamId, PlayerId)
);

-- Периоды/таймы матча (вручную; структура зависит от вида спорта)
CREATE TABLE MatchPeriod (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    MatchId         INT             NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
    PeriodNumber    INT             NOT NULL,          -- 1, 2, ...
    Label           NVARCHAR(50)    NULL,              -- e.g. N'1-й тайм'
    CONSTRAINT UQ_MatchPeriod UNIQUE (MatchId, PeriodNumber)
);

-- =============================================================================
-- EVENTS (события разметки)
-- =============================================================================

CREATE TABLE Event (
    Id              INT             NOT NULL IDENTITY(1,1) PRIMARY KEY,
    MatchId         INT             NOT NULL REFERENCES Match(Id) ON DELETE CASCADE,
    PeriodNumber    INT             NOT NULL,          -- тайм (вручную при вводе)
    TimestampSec    INT             NOT NULL,          -- секунды от начала текущего видеофайла
    -- Субъект: либо игрок из MatchLineup, либо команда целиком
    SubjectType     VARCHAR(10)     NOT NULL CHECK (SubjectType IN ('player', 'team')),
    PlayerId        INT             NULL REFERENCES Player(Id),
    TeamId          INT             NULL REFERENCES Team(Id),
    ActionId        INT             NOT NULL REFERENCES Action(Id),
    Outcome         NVARCHAR(20)    NULL CHECK (Outcome IN (N'Success', N'Failure') OR Outcome IS NULL),
    Comment         NVARCHAR(1000)  NULL,
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME(),
    -- Ровно один субъект
    CONSTRAINT CK_Event_Subject CHECK (
        (SubjectType = 'player' AND PlayerId IS NOT NULL AND TeamId IS NULL) OR
        (SubjectType = 'team'   AND TeamId IS NOT NULL AND PlayerId IS NULL)
    )
);

-- =============================================================================
-- APP SETTINGS (ключ-значение)
-- =============================================================================

CREATE TABLE AppSetting (
    Key             NVARCHAR(100)   NOT NULL PRIMARY KEY,
    Value           NVARCHAR(500)   NULL
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IX_Player_TeamId           ON Player(TeamId);
CREATE INDEX IX_Tournament_Name         ON Tournament(Name);
CREATE INDEX IX_Squad_TeamId            ON Squad(TeamId);
CREATE INDEX IX_SquadPlayer_SquadId     ON SquadPlayer(SquadId);
CREATE INDEX IX_Match_HomeTeamId        ON Match(HomeTeamId);
CREATE INDEX IX_Match_AwayTeamId        ON Match(AwayTeamId);
CREATE INDEX IX_MatchLineup_MatchId     ON MatchLineup(MatchId);
CREATE INDEX IX_Event_MatchId           ON Event(MatchId);
CREATE INDEX IX_Event_PlayerId          ON Event(PlayerId);
CREATE INDEX IX_Event_ActionId          ON Event(ActionId);
CREATE INDEX IX_TeamStatMetric_SportTemplateId ON TeamStatMetric(SportTemplateId);
CREATE INDEX IX_TeamStatMetric_ActionId ON TeamStatMetric(ActionId);

-- =============================================================================
-- WORKFLOW: подготовка матча из сохранённого состава
-- =============================================================================
/*
  1. Справочник: Team → Player (заявка команды)
  2. Squad + SquadPlayer — сохранённый состав на турнир/сезон
  3. Match: выбор HomeTeam, AwayTeam, HomeSquadId, AwaySquadId
  4. Копирование в MatchLineup (снимок):

     INSERT INTO MatchLineup (MatchId, TeamId, PlayerId, Position, LineupRole, SortOrder)
     SELECT @MatchId, s.TeamId, sp.PlayerId, sp.Position, sp.LineupRole, sp.SortOrder
     FROM SquadPlayer sp
     INNER JOIN Squad s ON s.Id = sp.SquadId
     WHERE sp.SquadId = @HomeSquadId;

  5. Разметка: кнопки игроков только из MatchLineup + команды из Team
*/
