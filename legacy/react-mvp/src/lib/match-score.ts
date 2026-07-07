import {
  getAction,
  getMatch,
  listEventsByMatch,
  listMatchLineup,
  listPlayers,
} from '../db/repository';
import type { Action, Event, Match, MatchLineup, Player } from '../types';

export interface MatchScore {
  home: number;
  away: number;
}

/** Латинизация визуально похожих кириллических букв (Сonversion → conversion). */
function latinizeHomoglyphs(text: string): string {
  const map: Record<string, string> = {
    '\u0430': 'a',
    '\u04d0': 'a',
    '\u0432': 'b',
    '\u0441': 'c',
    '\u0435': 'e',
    '\u0451': 'e',
    '\u043d': 'h',
    '\u043a': 'k',
    '\u043c': 'm',
    '\u043e': 'o',
    '\u043f': 'p',
    '\u0440': 'p',
    '\u0442': 't',
    '\u0445': 'x',
    '\u0443': 'y',
    '\u0456': 'i',
    '\u0457': 'i',
  };

  return text
    .trim()
    .toLowerCase()
    .replace(/./g, (ch) => map[ch] ?? ch);
}

function normalizeActionName(name: string): string {
  return latinizeHomoglyphs(name);
}

function normalizeOutcome(outcome?: string): string {
  return outcome?.trim().toLowerCase() ?? '';
}

function isTryAction(name: string): boolean {
  return normalizeActionName(name) === 'try';
}

/** conversion, Conversion, conversion (opp) и т.п. */
function isConversionAction(name: string): boolean {
  return normalizeActionName(name).startsWith('conversion');
}

function isFailureOutcome(outcome?: string): boolean {
  return normalizeOutcome(outcome) === 'failure';
}

/**
 * try — 5 очков (результат не важен).
 * conversion — 2 очка при Success или если результат не указан; 0 при Failure.
 */
export function getScoringPoints(actionName: string, outcome?: string): number {
  if (isTryAction(actionName)) return 5;

  if (isConversionAction(actionName)) {
    if (isFailureOutcome(outcome)) return 0;
    return 2;
  }

  return 0;
}

/** Определяет команду-автора очка: по teamId или по игроку (состав матча → roster). */
export function resolveEventTeamId(
  event: Event,
  match: Pick<Match, 'homeTeamId' | 'awayTeamId'>,
  lineups: MatchLineup[],
  players: Player[],
): number | null {
  if (event.teamId) {
    if (event.teamId === match.homeTeamId || event.teamId === match.awayTeamId) {
      return event.teamId;
    }
  }

  if (event.playerId) {
    const lineupRow = lineups.find((l) => l.playerId === event.playerId);
    if (lineupRow) {
      if (lineupRow.teamId === match.homeTeamId || lineupRow.teamId === match.awayTeamId) {
        return lineupRow.teamId;
      }
    }

    const player = players.find((p) => p.id === event.playerId);
    if (player) {
      if (player.teamId === match.homeTeamId || player.teamId === match.awayTeamId) {
        return player.teamId;
      }
    }
  }

  return null;
}

export function calculateMatchScore(
  events: Event[],
  actions: Action[],
  match: Pick<Match, 'homeTeamId' | 'awayTeamId'>,
  lineups: MatchLineup[],
  players: Player[],
): MatchScore {
  const actionById = new Map(actions.filter((a) => a.id).map((a) => [a.id!, a]));
  const score: MatchScore = { home: 0, away: 0 };

  for (const event of events) {
    if (!event.actionId) continue;

    const action = actionById.get(event.actionId);
    if (!action) continue;

    const points = getScoringPoints(action.name, event.outcome);
    if (points === 0) continue;

    const teamId = resolveEventTeamId(event, match, lineups, players);
    if (!teamId) continue;

    if (teamId === match.homeTeamId) score.home += points;
    else if (teamId === match.awayTeamId) score.away += points;
  }

  return score;
}

export async function calculateMatchScoreForMatch(matchId: number): Promise<MatchScore | null> {
  const match = await getMatch(matchId);
  if (!match?.id) return null;

  const [events, lineups, players] = await Promise.all([
    listEventsByMatch(matchId),
    listMatchLineup(matchId),
    listPlayers(),
  ]);

  const actionIds = [...new Set(events.map((e) => e.actionId).filter((id): id is number => id != null))];
  const actions = (await Promise.all(actionIds.map((id) => getAction(id)))).filter(
    (a): a is Action => a != null,
  );

  return calculateMatchScore(events, actions, match, lineups, players);
}
