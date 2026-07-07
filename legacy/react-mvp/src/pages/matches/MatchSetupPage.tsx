import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  getMatch,
  listEventsByMatch,
  listCategoriesByTemplateWithActions,
  listMatchLineup,
  listPlayers,
  listSquads,
  listTeams,
  updateMatchLineupRole,
} from '../../db/repository';
import { copySquadToMatchLineup } from '../../db/seed';
import { MatchScoreDisplay } from '../../components/MatchScoreDisplay';
import { calculateMatchScore } from '../../lib/match-score';
import type { Action, Event, LineupRole, Match, MatchLineup, Player, Squad, Team } from '../../types';

export function MatchSetupPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const id = Number(matchId);

  const [match, setMatch] = useState<Match | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [squads, setSquads] = useState<Squad[]>([]);
  const [lineups, setLineups] = useState<MatchLineup[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [homeSquadId, setHomeSquadId] = useState<number | ''>('');
  const [awaySquadId, setAwaySquadId] = useState<number | ''>('');

  async function load() {
    const m = await getMatch(id);
    setMatch(m ?? null);
    if (!m) return;

    setTeams(await listTeams());
    setSquads(await listSquads());
    setLineups(await listMatchLineup(id));
    setPlayers(await listPlayers());
    setEvents(await listEventsByMatch(id));
    const templateData = await listCategoriesByTemplateWithActions(m.sportTemplateId);
    setActions(Object.values(templateData.actions).flat());
    setHomeSquadId(m.homeSquadId ?? '');
    setAwaySquadId(m.awaySquadId ?? '');
  }

  useEffect(() => {
    if (id) void load();
  }, [id]);

  const teamName = (teamId: number) => teams.find((t) => t.id === teamId)?.name ?? '?';
  const playerName = (playerId: number) => players.find((p) => p.id === playerId)?.name ?? '?';
  const squadsForTeam = (teamId: number) => squads.filter((s) => s.teamId === teamId);

  async function applySquad(side: 'home' | 'away') {
    const squadId = side === 'home' ? homeSquadId : awaySquadId;
    if (!squadId || !match?.id) return;
    await copySquadToMatchLineup(match.id, Number(squadId), side);
    await load();
  }

  async function toggleLineupRole(row: MatchLineup) {
    if (!row.id) return;
    const role: LineupRole = row.lineupRole === 'starter' ? 'substitute' : 'starter';
    await updateMatchLineupRole(row.id, role);
    await load();
  }

  const matchScore = useMemo(() => {
    if (!match) return { home: 0, away: 0 };
    return calculateMatchScore(events, actions, match, lineups, players);
  }, [events, actions, match, lineups, players]);

  if (!match) return <p>Матч не найден</p>;

  const homeLineup = lineups.filter((l) => l.teamId === match.homeTeamId);
  const awayLineup = lineups.filter((l) => l.teamId === match.awayTeamId);

  return (
    <div>
      <p>
        <Link to="/matches">← Матчи</Link>
      </p>
      <h1 className="page-title">
        Подготовка: {teamName(match.homeTeamId)} — {teamName(match.awayTeamId)}
      </h1>

      <div className="card">
        <MatchScoreDisplay
          homeName={teamName(match.homeTeamId)}
          awayName={teamName(match.awayTeamId)}
          score={matchScore}
          compact
        />
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Домашняя: {teamName(match.homeTeamId)}</h3>
          <div className="form-row">
            <select
              value={homeSquadId}
              onChange={(e) => setHomeSquadId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">Выберите состав</option>
              {squadsForTeam(match.homeTeamId).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <button type="button" className="btn btn-primary" onClick={() => void applySquad('home')}>
              Применить состав
            </button>
          </div>
          <LineupTable lineup={homeLineup} playerName={playerName} onToggle={toggleLineupRole} />
        </div>

        <div className="card">
          <h3>Гостевая: {teamName(match.awayTeamId)}</h3>
          <div className="form-row">
            <select
              value={awaySquadId}
              onChange={(e) => setAwaySquadId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">Выберите состав</option>
              {squadsForTeam(match.awayTeamId).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <button type="button" className="btn btn-primary" onClick={() => void applySquad('away')}>
              Применить состав
            </button>
          </div>
          <LineupTable lineup={awayLineup} playerName={playerName} onToggle={toggleLineupRole} />
        </div>
      </div>

      <div className="card">
        <Link className="btn btn-success" to={`/tagging/${match.id}/control`}>
          Перейти к разметке →
        </Link>
        {' '}
        <a
          className="btn"
          href={`/tagging/${match.id}/video`}
          target="_blank"
          rel="noreferrer"
        >
          Открыть видео на 2-м мониторе
        </a>
      </div>
    </div>
  );
}

function LineupTable({
  lineup,
  playerName,
  onToggle,
}: {
  lineup: MatchLineup[];
  playerName: (id: number) => string;
  onToggle: (row: MatchLineup) => void;
}) {
  if (lineup.length === 0) return <p className="muted">Состав не назначен</p>;

  const starters = lineup.filter((l) => l.lineupRole === 'starter');
  const subs = lineup.filter((l) => l.lineupRole === 'substitute');

  return (
    <>
      <p className="section-label">Основной состав</p>
      <table className="data-table">
        <tbody>
          {starters.map((row) => (
            <tr key={row.id}>
              <td>{playerName(row.playerId)}</td>
              <td>{row.position ?? '—'}</td>
              <td>
                <button type="button" className="btn" onClick={() => onToggle(row)}>
                  → Замена
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="section-label">Замена</p>
      <table className="data-table">
        <tbody>
          {subs.map((row) => (
            <tr key={row.id}>
              <td>{playerName(row.playerId)}</td>
              <td>{row.position ?? '—'}</td>
              <td>
                <button type="button" className="btn" onClick={() => onToggle(row)}>
                  → Основной
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
