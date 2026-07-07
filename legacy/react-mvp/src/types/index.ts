export type LineupRole = 'starter' | 'substitute';
export type SubjectType = 'player' | 'team';
export type Outcome = 'Success' | 'Failure';

export interface SportTemplate {
  id?: number;
  name: string;
  createdAt: Date;
}

export interface Category {
  id?: number;
  sportTemplateId: number;
  name: string;
  sortOrder: number;
}

export interface Action {
  id?: number;
  categoryId: number;
  name: string;
  hasOutcome: boolean;
  sortOrder: number;
  colorClass?: string;
}

export interface CommentTemplate {
  id?: number;
  actionId: number;
  text: string;
  sortOrder: number;
}

export interface Team {
  id?: number;
  name: string;
  createdAt: Date;
}

export interface Player {
  id?: number;
  teamId: number;
  name: string;
  defaultPosition?: string;
  isActive: boolean;
}

export interface Squad {
  id?: number;
  teamId: number;
  name: string;
  tournament?: string;
  note?: string;
  createdAt: Date;
}

export interface SquadPlayer {
  id?: number;
  squadId: number;
  playerId: number;
  position?: string;
  lineupRole: LineupRole;
  sortOrder: number;
}

export interface Match {
  id?: number;
  sportTemplateId: number;
  homeTeamId: number;
  awayTeamId: number;
  matchDate: string;
  tournament?: string;
  scoreHome?: number;
  scoreAway?: number;
  homeSquadId?: number;
  awaySquadId?: number;
  createdAt: Date;
}

export interface MatchLineup {
  id?: number;
  matchId: number;
  teamId: number;
  playerId: number;
  position?: string;
  lineupRole: LineupRole;
  sortOrder: number;
}

export interface MatchPeriod {
  id?: number;
  matchId: number;
  periodNumber: number;
  label?: string;
}

export interface Event {
  id?: number;
  matchId: number;
  periodNumber: number;
  timestampSec: number;
  subjectType: SubjectType;
  playerId?: number;
  teamId?: number;
  actionId?: number;
  outcome?: Outcome;
  comment?: string;
  createdAt: Date;
}

export type BroadcastMessage =
  | { type: 'TIME_UPDATE'; time: number }
  | { type: 'PAUSE' }
  | { type: 'TOGGLE_PLAY' }
  | { type: 'SEEK'; time: number }
  | { type: 'CONNECTED' };
