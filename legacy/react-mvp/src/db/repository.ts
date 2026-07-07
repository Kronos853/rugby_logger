import type {
  Action,
  Category,
  CommentTemplate,
  Event,
  LineupRole,
  Match,
  MatchLineup,
  Outcome,
  Player,
  Squad,
  SquadPlayer,
  SportTemplate,
  SubjectType,
  Team,
} from '../types';
import { all, get, insert, run, withWrite, withWriteVoid } from './sqlite';

type Row = Record<string, string | number | null | Uint8Array>;

function bool(v: Row[keyof Row]): boolean {
  return v === 1 || v === '1';
}

function mapSportTemplate(r: Row): SportTemplate {
  return {
    id: r.Id as number,
    name: r.Name as string,
    createdAt: new Date(r.CreatedAt as string),
  };
}

function mapCategory(r: Row): Category {
  return {
    id: r.Id as number,
    sportTemplateId: r.SportTemplateId as number,
    name: r.Name as string,
    sortOrder: r.SortOrder as number,
  };
}

function mapAction(r: Row): Action {
  return {
    id: r.Id as number,
    categoryId: r.CategoryId as number,
    name: r.Name as string,
    hasOutcome: bool(r.HasOutcome),
    sortOrder: r.SortOrder as number,
    colorClass: (r.ColorClass as string) || undefined,
  };
}

function mapComment(r: Row): CommentTemplate {
  return {
    id: r.Id as number,
    actionId: r.ActionId as number,
    text: r.Text as string,
    sortOrder: r.SortOrder as number,
  };
}

function mapTeam(r: Row): Team {
  return {
    id: r.Id as number,
    name: r.Name as string,
    createdAt: new Date(r.CreatedAt as string),
  };
}

function mapPlayer(r: Row): Player {
  return {
    id: r.Id as number,
    teamId: r.TeamId as number,
    name: r.Name as string,
    defaultPosition: (r.DefaultPosition as string) || undefined,
    isActive: bool(r.IsActive),
  };
}

function mapSquad(r: Row): Squad {
  return {
    id: r.Id as number,
    teamId: r.TeamId as number,
    name: r.Name as string,
    tournament: (r.Tournament as string) || undefined,
    note: (r.Note as string) || undefined,
    createdAt: new Date(r.CreatedAt as string),
  };
}

function mapSquadPlayer(r: Row): SquadPlayer {
  return {
    id: r.Id as number,
    squadId: r.SquadId as number,
    playerId: r.PlayerId as number,
    position: (r.Position as string) || undefined,
    lineupRole: r.LineupRole as LineupRole,
    sortOrder: r.SortOrder as number,
  };
}

function mapMatch(r: Row): Match {
  return {
    id: r.Id as number,
    sportTemplateId: r.SportTemplateId as number,
    homeTeamId: r.HomeTeamId as number,
    awayTeamId: r.AwayTeamId as number,
    matchDate: r.MatchDate as string,
    tournament: (r.Tournament as string) || undefined,
    scoreHome: r.ScoreHome != null ? (r.ScoreHome as number) : undefined,
    scoreAway: r.ScoreAway != null ? (r.ScoreAway as number) : undefined,
    homeSquadId: r.HomeSquadId != null ? (r.HomeSquadId as number) : undefined,
    awaySquadId: r.AwaySquadId != null ? (r.AwaySquadId as number) : undefined,
    createdAt: new Date(r.CreatedAt as string),
  };
}

function mapMatchLineup(r: Row): MatchLineup {
  return {
    id: r.Id as number,
    matchId: r.MatchId as number,
    teamId: r.TeamId as number,
    playerId: r.PlayerId as number,
    position: (r.Position as string) || undefined,
    lineupRole: r.LineupRole as LineupRole,
    sortOrder: r.SortOrder as number,
  };
}

function mapEvent(r: Row): Event {
  return {
    id: r.Id as number,
    matchId: r.MatchId as number,
    periodNumber: r.PeriodNumber as number,
    timestampSec: r.TimestampSec as number,
    subjectType: r.SubjectType as SubjectType,
    playerId: r.PlayerId != null ? (r.PlayerId as number) : undefined,
    teamId: r.TeamId != null ? (r.TeamId as number) : undefined,
    actionId: r.ActionId != null ? (r.ActionId as number) : undefined,
    outcome: (r.Outcome as Outcome) || undefined,
    comment: (r.Comment as string) || undefined,
    createdAt: new Date(r.CreatedAt as string),
  };
}

// --- Sport templates ---

export async function listSportTemplates(): Promise<SportTemplate[]> {
  return all<Row>('SELECT * FROM SportTemplate ORDER BY Name').map(mapSportTemplate);
}

export async function getSportTemplateByName(name: string): Promise<SportTemplate | undefined> {
  const row = get<Row>('SELECT * FROM SportTemplate WHERE Name = ?', [name]);
  return row ? mapSportTemplate(row) : undefined;
}

export async function countSportTemplates(): Promise<number> {
  const row = get<Row>('SELECT COUNT(*) AS c FROM SportTemplate');
  return (row?.c as number) ?? 0;
}

export async function createSportTemplate(name: string): Promise<number> {
  return withWrite(() =>
    insert('INSERT INTO SportTemplate (Name, CreatedAt) VALUES (?, datetime("now"))', [name]),
  );
}

// --- Categories ---

export async function listCategoriesByTemplate(templateId: number): Promise<Category[]> {
  return all<Row>('SELECT * FROM Category WHERE SportTemplateId = ? ORDER BY SortOrder', [
    templateId,
  ]).map(mapCategory);
}

export async function createCategory(
  sportTemplateId: number,
  name: string,
  sortOrder: number,
): Promise<number> {
  return withWrite(() =>
    insert(
      'INSERT INTO Category (SportTemplateId, Name, SortOrder) VALUES (?, ?, ?)',
      [sportTemplateId, name, sortOrder],
    ),
  );
}

// --- Actions ---

export async function listActionsByCategory(categoryId: number): Promise<Action[]> {
  return all<Row>('SELECT * FROM Action WHERE CategoryId = ? ORDER BY SortOrder', [categoryId]).map(
    mapAction,
  );
}

export async function getAction(id: number): Promise<Action | undefined> {
  const row = get<Row>('SELECT * FROM Action WHERE Id = ?', [id]);
  return row ? mapAction(row) : undefined;
}

export async function createAction(
  categoryId: number,
  name: string,
  hasOutcome: boolean,
  sortOrder: number,
  colorClass?: string,
): Promise<number> {
  return withWrite(() =>
    insert(
      'INSERT INTO Action (CategoryId, Name, HasOutcome, SortOrder, ColorClass) VALUES (?, ?, ?, ?, ?)',
      [categoryId, name, hasOutcome ? 1 : 0, sortOrder, colorClass ?? null],
    ),
  );
}

export async function updateActionHasOutcome(id: number, hasOutcome: boolean): Promise<void> {
  return withWriteVoid(() => {
    run('UPDATE Action SET HasOutcome = ? WHERE Id = ?', [hasOutcome ? 1 : 0, id]);
  });
}

export async function updateActionName(id: number, name: string): Promise<void> {
  return withWriteVoid(() => {
    run('UPDATE Action SET Name = ? WHERE Id = ?', [name, id]);
  });
}

// --- Comment templates ---

export async function listCommentsByAction(actionId: number): Promise<CommentTemplate[]> {
  return all<Row>('SELECT * FROM CommentTemplate WHERE ActionId = ? ORDER BY SortOrder', [
    actionId,
  ]).map(mapComment);
}

export async function createCommentTemplate(
  actionId: number,
  text: string,
  sortOrder: number,
): Promise<number> {
  return withWrite(() =>
    insert('INSERT INTO CommentTemplate (ActionId, Text, SortOrder) VALUES (?, ?, ?)', [
      actionId,
      text,
      sortOrder,
    ]),
  );
}

// --- Teams ---

export async function listTeams(): Promise<Team[]> {
  return all<Row>('SELECT * FROM Team ORDER BY Name').map(mapTeam);
}

export async function getTeam(id: number): Promise<Team | undefined> {
  const row = get<Row>('SELECT * FROM Team WHERE Id = ?', [id]);
  return row ? mapTeam(row) : undefined;
}

export async function createTeam(name: string): Promise<number> {
  return withWrite(() =>
    insert('INSERT INTO Team (Name, CreatedAt) VALUES (?, datetime("now"))', [name]),
  );
}

// --- Players ---

export async function listPlayersByTeam(teamId: number): Promise<Player[]> {
  return all<Row>('SELECT * FROM Player WHERE TeamId = ? ORDER BY Name', [teamId]).map(mapPlayer);
}

export async function listPlayers(): Promise<Player[]> {
  return all<Row>('SELECT * FROM Player ORDER BY Name').map(mapPlayer);
}

export async function getPlayer(id: number): Promise<Player | undefined> {
  const row = get<Row>('SELECT * FROM Player WHERE Id = ?', [id]);
  return row ? mapPlayer(row) : undefined;
}

export async function createPlayer(
  teamId: number,
  name: string,
  defaultPosition?: string,
): Promise<number> {
  return withWrite(() =>
    insert(
      'INSERT INTO Player (TeamId, Name, DefaultPosition, IsActive) VALUES (?, ?, ?, 1)',
      [teamId, name, defaultPosition ?? null],
    ),
  );
}

// --- Squads ---

export async function listSquads(): Promise<Squad[]> {
  return all<Row>('SELECT * FROM Squad ORDER BY Name').map(mapSquad);
}

export async function listSquadsByTeam(teamId: number): Promise<Squad[]> {
  return all<Row>('SELECT * FROM Squad WHERE TeamId = ? ORDER BY Name', [teamId]).map(mapSquad);
}

export async function getSquad(id: number): Promise<Squad | undefined> {
  const row = get<Row>('SELECT * FROM Squad WHERE Id = ?', [id]);
  return row ? mapSquad(row) : undefined;
}

export async function createSquad(
  teamId: number,
  name: string,
  tournament?: string,
): Promise<number> {
  return withWrite(() =>
    insert(
      'INSERT INTO Squad (TeamId, Name, Tournament, CreatedAt) VALUES (?, ?, ?, datetime("now"))',
      [teamId, name, tournament ?? null],
    ),
  );
}

export async function updateSquad(
  id: number,
  patch: { name?: string; tournament?: string | null },
): Promise<void> {
  return withWriteVoid(() => {
    if (patch.name !== undefined) {
      run('UPDATE Squad SET Name = ? WHERE Id = ?', [patch.name, id]);
    }
    if (patch.tournament !== undefined) {
      run('UPDATE Squad SET Tournament = ? WHERE Id = ?', [patch.tournament, id]);
    }
  });
}

export async function listSquadPlayers(squadId: number): Promise<SquadPlayer[]> {
  return all<Row>('SELECT * FROM SquadPlayer WHERE SquadId = ? ORDER BY SortOrder', [squadId]).map(
    mapSquadPlayer,
  );
}

export async function addSquadPlayer(
  squadId: number,
  playerId: number,
  sortOrder: number,
): Promise<number> {
  return withWrite(() =>
    insert(
      `INSERT INTO SquadPlayer (SquadId, PlayerId, LineupRole, SortOrder) VALUES (?, ?, 'starter', ?)`,
      [squadId, playerId, sortOrder],
    ),
  );
}

export async function updateSquadPlayerRole(id: number, role: LineupRole): Promise<void> {
  return withWriteVoid(() => {
    run('UPDATE SquadPlayer SET LineupRole = ? WHERE Id = ?', [role, id]);
  });
}

export async function deleteSquadPlayer(id: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM SquadPlayer WHERE Id = ?', [id]);
  });
}

// --- Matches ---

export async function listMatches(): Promise<Match[]> {
  return all<Row>('SELECT * FROM Match ORDER BY MatchDate DESC').map(mapMatch);
}

export async function getMatch(id: number): Promise<Match | undefined> {
  const row = get<Row>('SELECT * FROM Match WHERE Id = ?', [id]);
  return row ? mapMatch(row) : undefined;
}

export async function countMatchesByTemplate(templateId: number): Promise<number> {
  const row = get<Row>('SELECT COUNT(*) AS c FROM Match WHERE SportTemplateId = ?', [templateId]);
  return (row?.c as number) ?? 0;
}

export async function countMatchesByTeam(teamId: number): Promise<number> {
  const row = get<Row>(
    'SELECT COUNT(*) AS c FROM Match WHERE HomeTeamId = ? OR AwayTeamId = ?',
    [teamId, teamId],
  );
  return (row?.c as number) ?? 0;
}

export async function createMatch(data: Omit<Match, 'id' | 'createdAt'>): Promise<number> {
  return withWrite(() =>
    insert(
      `INSERT INTO Match (SportTemplateId, HomeTeamId, AwayTeamId, MatchDate, Tournament, ScoreHome, ScoreAway, CreatedAt)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
      [
        data.sportTemplateId,
        data.homeTeamId,
        data.awayTeamId,
        data.matchDate,
        data.tournament ?? null,
        data.scoreHome ?? null,
        data.scoreAway ?? null,
      ],
    ),
  );
}

export async function updateMatchSquadRefs(
  matchId: number,
  patch: { homeSquadId?: number; awaySquadId?: number },
): Promise<void> {
  return withWriteVoid(() => {
    if (patch.homeSquadId !== undefined) {
      run('UPDATE Match SET HomeSquadId = ? WHERE Id = ?', [patch.homeSquadId, matchId]);
    }
    if (patch.awaySquadId !== undefined) {
      run('UPDATE Match SET AwaySquadId = ? WHERE Id = ?', [patch.awaySquadId, matchId]);
    }
  });
}

export async function createMatchPeriods(matchId: number): Promise<void> {
  return withWriteVoid(() => {
    run('INSERT INTO MatchPeriod (MatchId, PeriodNumber, Label) VALUES (?, 1, ?)', [
      matchId,
      '1-й тайм',
    ]);
    run('INSERT INTO MatchPeriod (MatchId, PeriodNumber, Label) VALUES (?, 2, ?)', [
      matchId,
      '2-й тайм',
    ]);
  });
}

// --- Match lineup ---

export async function listMatchLineup(matchId: number): Promise<MatchLineup[]> {
  return all<Row>('SELECT * FROM MatchLineup WHERE MatchId = ? ORDER BY SortOrder', [matchId]).map(
    mapMatchLineup,
  );
}

export async function deleteMatchLineupForTeam(matchId: number, teamId: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM MatchLineup WHERE MatchId = ? AND TeamId = ?', [matchId, teamId]);
  });
}

export async function addMatchLineupRow(row: Omit<MatchLineup, 'id'>): Promise<number> {
  return withWrite(() =>
    insert(
      `INSERT INTO MatchLineup (MatchId, TeamId, PlayerId, Position, LineupRole, SortOrder)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [
        row.matchId,
        row.teamId,
        row.playerId,
        row.position ?? null,
        row.lineupRole,
        row.sortOrder,
      ],
    ),
  );
}

export async function updateMatchLineupRole(id: number, role: LineupRole): Promise<void> {
  return withWriteVoid(() => {
    run('UPDATE MatchLineup SET LineupRole = ? WHERE Id = ?', [role, id]);
  });
}

// --- Events ---

export async function listEventsByMatch(matchId: number): Promise<Event[]> {
  return all<Row>('SELECT * FROM Event WHERE MatchId = ? ORDER BY CreatedAt', [matchId]).map(
    mapEvent,
  );
}

export async function createEvent(
  data: Omit<Event, 'id' | 'createdAt'>,
): Promise<number> {
  return withWrite(() =>
    insert(
      `INSERT INTO Event (MatchId, PeriodNumber, TimestampSec, SubjectType, PlayerId, TeamId, ActionId, Outcome, Comment, CreatedAt)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
      [
        data.matchId,
        data.periodNumber,
        data.timestampSec,
        data.subjectType,
        data.playerId ?? null,
        data.teamId ?? null,
        data.actionId ?? null,
        data.outcome ?? null,
        data.comment ?? null,
      ],
    ),
  );
}

export async function updateEvent(id: number, patch: Partial<Event>): Promise<void> {
  return withWriteVoid(() => {
    const fields: string[] = [];
    const values: (string | number | null)[] = [];

    if (patch.periodNumber !== undefined) {
      fields.push('PeriodNumber = ?');
      values.push(patch.periodNumber);
    }
    if (patch.subjectType !== undefined) {
      fields.push('SubjectType = ?');
      values.push(patch.subjectType);
    }
    if ('playerId' in patch) {
      fields.push('PlayerId = ?');
      values.push(patch.playerId ?? null);
    }
    if ('teamId' in patch) {
      fields.push('TeamId = ?');
      values.push(patch.teamId ?? null);
    }
    if ('actionId' in patch) {
      fields.push('ActionId = ?');
      values.push(patch.actionId ?? null);
    }
    if ('outcome' in patch) {
      fields.push('Outcome = ?');
      values.push(patch.outcome ?? null);
    }
    if ('comment' in patch) {
      fields.push('Comment = ?');
      values.push(patch.comment ?? null);
    }

    if (fields.length === 0) return;
    values.push(id);
    run(`UPDATE Event SET ${fields.join(', ')} WHERE Id = ?`, values);
  });
}

export async function deleteEvent(id: number): Promise<void> {
  return withWriteVoid(() => {
    run('DELETE FROM Event WHERE Id = ?', [id]);
  });
}

// --- Categories lookup ---

export async function getCategory(id: number): Promise<Category | undefined> {
  const row = get<Row>('SELECT * FROM Category WHERE Id = ?', [id]);
  return row ? mapCategory(row) : undefined;
}

export async function listCategoriesByTemplateWithActions(templateId: number): Promise<{
  categories: Category[];
  actions: Record<number, Action[]>;
  comments: Record<number, CommentTemplate[]>;
}> {
  const categories = await listCategoriesByTemplate(templateId);
  const actions: Record<number, Action[]> = {};
  const comments: Record<number, CommentTemplate[]> = {};

  for (const cat of categories) {
    if (!cat.id) continue;
    const catActions = await listActionsByCategory(cat.id);
    actions[cat.id] = catActions;
    for (const act of catActions) {
      if (!act.id) continue;
      comments[act.id] = await listCommentsByAction(act.id);
    }
  }

  return { categories, actions, comments };
}
