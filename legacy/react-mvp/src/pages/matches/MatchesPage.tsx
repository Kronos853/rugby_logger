import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteMatch } from '../../db/cleanup';
import {
  createMatch,
  createMatchPeriods,
  listMatches,
  listSportTemplates,
  listTeams,
} from '../../db/repository';
import { ensureSeeded } from '../../db/seed';
import type { Match, Team } from '../../types';
import { calculateMatchScoreForMatch } from '../../lib/match-score';

export function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [templates, setTemplates] = useState<{ id: number; name: string }[]>([]);
  const [scores, setScores] = useState<Record<number, { home: number; away: number }>>({});

  const [sportTemplateId, setSportTemplateId] = useState<number | ''>('');
  const [homeTeamId, setHomeTeamId] = useState<number | ''>('');
  const [awayTeamId, setAwayTeamId] = useState<number | ''>('');
  const [matchDate, setMatchDate] = useState(new Date().toISOString().slice(0, 10));
  const [tournament, setTournament] = useState('');
  const [scoreHome, setScoreHome] = useState('');
  const [scoreAway, setScoreAway] = useState('');

  async function load() {
    await ensureSeeded();
    const tpls = await listSportTemplates();
    setTemplates(tpls.map((t) => ({ id: t.id!, name: t.name })));
    setTeams(await listTeams());
    const allMatches = await listMatches();
    setMatches(allMatches);

    const scoreEntries = await Promise.all(
      allMatches.map(async (m) => {
        if (!m.id) return null;
        const score = await calculateMatchScoreForMatch(m.id);
        return score ? ([m.id, score] as const) : null;
      }),
    );
    setScores(Object.fromEntries(scoreEntries.filter(Boolean) as [number, { home: number; away: number }][]));
    if (tpls[0]?.id && !sportTemplateId) setSportTemplateId(tpls[0].id);
  }

  useEffect(() => {
    void load();
  }, []);

  const teamName = (tid: number) => teams.find((t) => t.id === tid)?.name ?? '?';

  async function createMatchHandler(e: React.FormEvent) {
    e.preventDefault();
    if (!sportTemplateId || !homeTeamId || !awayTeamId) return;

    const matchId = await createMatch({
      sportTemplateId: Number(sportTemplateId),
      homeTeamId: Number(homeTeamId),
      awayTeamId: Number(awayTeamId),
      matchDate,
      tournament: tournament.trim() || undefined,
      scoreHome: scoreHome ? Number(scoreHome) : undefined,
      scoreAway: scoreAway ? Number(scoreAway) : undefined,
    });

    await createMatchPeriods(matchId);

    setTournament('');
    setScoreHome('');
    setScoreAway('');
    await load();
  }

  async function handleDeleteMatch(match: Match) {
    if (!match.id || !confirm('Удалить матч и всю его статистику?')) return;
    await deleteMatch(match.id);
    await load();
  }

  return (
    <div>
      <h1 className="page-title">Матчи</h1>

      <div className="card">
        <h3>Новый матч</h3>
        <form onSubmit={createMatchHandler}>
          <div className="form-row">
            <select
              value={sportTemplateId}
              onChange={(e) => setSportTemplateId(Number(e.target.value))}
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <input type="date" value={matchDate} onChange={(e) => setMatchDate(e.target.value)} />
            <input
              placeholder="Турнир"
              value={tournament}
              onChange={(e) => setTournament(e.target.value)}
            />
          </div>
          <div className="form-row">
            <select value={homeTeamId} onChange={(e) => setHomeTeamId(Number(e.target.value))}>
              <option value="">Домашняя команда</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <select value={awayTeamId} onChange={(e) => setAwayTeamId(Number(e.target.value))}>
              <option value="">Гостевая команда</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <input
              placeholder="Счёт (дом)"
              value={scoreHome}
              onChange={(e) => setScoreHome(e.target.value)}
              style={{ width: 80 }}
            />
            <input
              placeholder="Счёт (гост)"
              value={scoreAway}
              onChange={(e) => setScoreAway(e.target.value)}
              style={{ width: 80 }}
            />
            <button type="submit" className="btn btn-primary">
              Создать матч
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Турнир</th>
              <th>Матч</th>
              <th>Счёт</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {matches.map((m) => (
              <tr key={m.id}>
                <td>{m.matchDate}</td>
                <td>{m.tournament ?? '—'}</td>
                <td>
                  {teamName(m.homeTeamId)} — {teamName(m.awayTeamId)}
                </td>
                <td>
                  {m.id && scores[m.id] != null
                    ? `${scores[m.id].home}:${scores[m.id].away}`
                    : `${m.scoreHome ?? 0}:${m.scoreAway ?? 0}`}
                </td>
                <td>
                  <Link to={`/matches/${m.id}/setup`}>Подготовка</Link>
                  {' | '}
                  <Link to={`/tagging/${m.id}/control`}>Разметка</Link>
                  {' | '}
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => void handleDeleteMatch(m)}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
