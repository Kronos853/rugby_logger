import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  createEvent,
  deleteEvent,
  getMatch,
  listCategoriesByTemplateWithActions,
  listEventsByMatch,
  listMatchLineup,
  listPlayers,
  listTeams,
  updateEvent,
} from '../../db/repository';
import { createBroadcastChannel, postMessage, subscribe } from '../../lib/broadcast';
import { exportMatchToCsv } from '../../lib/csv-export';
import { formatTimestamp } from '../../lib/format-time';
import { calculateMatchScore, getScoringPoints } from '../../lib/match-score';
import type {
  Action,
  CommentTemplate,
  Event,
  Match,
  MatchLineup,
  Outcome,
  Player,
  Team,
} from '../../types';
import '../../tagging.css';
import { MatchScoreDisplay } from '../../components/MatchScoreDisplay';

type ActionWithCategory = Action & { categoryName: string };

export function ControlPanelPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const id = Number(matchId);

  const channelRef = useRef(createBroadcastChannel());

  const [match, setMatch] = useState<Match | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [lineups, setLineups] = useState<MatchLineup[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [actions, setActions] = useState<ActionWithCategory[]>([]);
  const [comments, setComments] = useState<Record<number, CommentTemplate[]>>({});
  const [events, setEvents] = useState<Event[]>([]);

  const [videoTime, setVideoTime] = useState(0);
  const [connected, setConnected] = useState(false);
  const [period, setPeriod] = useState(1);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [commentText, setCommentText] = useState('');

  const selectedEvent = events.find((e) => e.id === selectedEventId) ?? null;

  const loadData = useCallback(async () => {
    const m = await getMatch(id);
    setMatch(m ?? null);
    if (!m) return;

    const [allTeams, allPlayers, lineupRows, matchEvents, templateData] = await Promise.all([
      listTeams(),
      listPlayers(),
      listMatchLineup(id),
      listEventsByMatch(id),
      listCategoriesByTemplateWithActions(m.sportTemplateId),
    ]);

    setTeams(allTeams);
    setPlayers(allPlayers);
    setLineups(lineupRows);
    setEvents(matchEvents);
    setComments(templateData.comments);

    const catMap = new Map(templateData.categories.map((c) => [c.id!, c.name]));
    const allActions: ActionWithCategory[] = [];
    for (const cat of templateData.categories) {
      if (!cat.id) continue;
      for (const act of templateData.actions[cat.id] ?? []) {
        allActions.push({ ...act, categoryName: catMap.get(cat.id) ?? '' });
      }
    }
    setActions(allActions);
  }, [id]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    const channel = channelRef.current;
    postMessage(channel, { type: 'CONNECTED' });

    return subscribe(channel, (msg) => {
      if (msg.type === 'TIME_UPDATE') {
        setVideoTime(msg.time);
        setConnected(true);
      }
      if (msg.type === 'CONNECTED') setConnected(true);
    });
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (
        e.code === 'Space' &&
        e.target instanceof HTMLInputElement === false &&
        e.target instanceof HTMLTextAreaElement === false
      ) {
        e.preventDefault();
        postMessage(channelRef.current, { type: 'TOGGLE_PLAY' });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const matchTeams = useMemo(() => {
    if (!match) return [];
    return teams.filter((t) => t.id === match.homeTeamId || t.id === match.awayTeamId);
  }, [match, teams]);

  const lineupPlayers = useMemo(() => {
    const playerIds = new Set(lineups.map((l) => l.playerId));
    return players.filter((p) => p.id && playerIds.has(p.id));
  }, [lineups, players]);

  const starters = lineups.filter((l) => l.lineupRole === 'starter');
  const substitutes = lineups.filter((l) => l.lineupRole === 'substitute');

  const playerById = (playerId: number) => players.find((p) => p.id === playerId);
  const teamById = (teamId: number) => teams.find((t) => t.id === teamId);
  const actionById = (actionId: number) => actions.find((a) => a.id === actionId);

  async function captureEvent() {
    postMessage(channelRef.current, { type: 'PAUSE' });

    const eventId = await createEvent({
      matchId: id,
      periodNumber: period,
      timestampSec: Math.floor(videoTime),
      subjectType: 'player',
    });

    await loadData();
    setSelectedEventId(eventId);
  }

  async function updateSelectedEvent(patch: Partial<Event>) {
    if (!selectedEventId) return;
    await updateEvent(selectedEventId, patch);
    await loadData();
  }

  async function selectPlayer(playerId: number) {
    await updateSelectedEvent({ subjectType: 'player', playerId, teamId: undefined });
  }

  async function selectTeam(teamId: number) {
    await updateSelectedEvent({ subjectType: 'team', teamId, playerId: undefined });
  }

  async function selectAction(action: ActionWithCategory) {
    if (!action.id) return;
    await updateSelectedEvent({ actionId: action.id, outcome: undefined });
    setCommentText('');
  }

  async function selectOutcome(outcome: Outcome | undefined) {
    await updateSelectedEvent({ outcome });
  }

  async function appendComment(text: string) {
    const next = commentText ? `${commentText}; ${text}` : text;
    setCommentText(next);
    await updateSelectedEvent({ comment: next });
  }

  async function saveComment() {
    await updateSelectedEvent({ comment: commentText });
  }

  async function deleteEventHandler(eventId: number, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm('Удалить запись?')) return;
    await deleteEvent(eventId);
    if (selectedEventId === eventId) setSelectedEventId(null);
    await loadData();
  }

  function seekToEvent(event: Event) {
    setSelectedEventId(event.id ?? null);
    postMessage(channelRef.current, { type: 'SEEK', time: event.timestampSec });
  }

  async function handleExport() {
    const m = match;
    if (!m?.id) return;
    const home = teamById(m.homeTeamId)?.name ?? 'home';
    const away = teamById(m.awayTeamId)?.name ?? 'away';
    await exportMatchToCsv(m.id, `Match_${home}_vs_${away}.csv`);
  }

  const selectedAction = selectedEvent?.actionId
    ? actionById(selectedEvent.actionId)
    : undefined;
  const actionComments = selectedAction?.id ? comments[selectedAction.id] ?? [] : [];

  const displayEvents = [...events].reverse();

  const matchScore = useMemo(() => {
    if (!match) return { home: 0, away: 0 };
    return calculateMatchScore(events, actions, match, lineups, players);
  }, [events, actions, match, lineups, players]);

  if (!match) return <p>Матч не найден</p>;

  return (
    <div className="tagging-page">
      <div className="tagging-sidebar">
        <div className="card">
          <h3>Управление</h3>
          <p className="muted" style={{ fontSize: 11, margin: 0 }}>
            Откройте видео на 2-м мониторе
          </p>
          <a
            className="btn"
            href={`/tagging/${id}/video`}
            target="_blank"
            rel="noreferrer"
            style={{ display: 'block', textAlign: 'center', marginTop: 8 }}
          >
            Открыть видео
          </a>
          <Link to={`/matches/${id}/setup`} style={{ display: 'block', marginTop: 8 }}>
            ← Подготовка матча
          </Link>
        </div>
        <div className="card">
          <button
            type="button"
            className="btn btn-success"
            style={{ width: '100%' }}
            onClick={() => void handleExport()}
          >
            Экспорт в CSV
          </button>
        </div>
      </div>

      <div className="tagging-main">
        <MatchScoreDisplay
          homeName={teamById(match.homeTeamId)?.name ?? 'Домашние'}
          awayName={teamById(match.awayTeamId)?.name ?? 'Гости'}
          score={matchScore}
        />

        <div className="meta-grid">
          <div className="meta-block">
            <span>МАТЧ</span>
            <span>
              {teamById(match.homeTeamId)?.name} — {teamById(match.awayTeamId)?.name}
            </span>
          </div>
          <div className="meta-block">
            <span>ТЕКУЩИЙ ТАЙМ</span>
            <div className="half-selector">
              <label>
                <input
                  type="radio"
                  name="period"
                  checked={period === 1}
                  onChange={() => setPeriod(1)}
                />{' '}
                1-й
              </label>
              <label>
                <input
                  type="radio"
                  name="period"
                  checked={period === 2}
                  onChange={() => setPeriod(2)}
                />{' '}
                2-й
              </label>
            </div>
          </div>
        </div>

        <button type="button" className="btn-capture" onClick={() => void captureEvent()}>
          НОВОЕ СОБЫТИЕ: Фиксировать время (Пауза)
        </button>

        <div className="status-bar">
          {connected
            ? `Связь установлена. Время видео: ${formatTimestamp(videoTime)} (${Math.floor(videoTime)} сек.)`
            : 'Ожидание подключения окна видео...'}
        </div>

        <div className="tagging-row">
          <div className="card">
            <h3>1. Игрок / Команда</h3>
            <p className="section-label">Основной состав</p>
            <div className="grid-players">
              {starters.map((l) => {
                const p = playerById(l.playerId);
                if (!p) return null;
                return (
                  <button
                    key={l.id}
                    type="button"
                    className={`tag-btn player-btn ${selectedEvent?.playerId === p.id ? 'selected' : ''}`}
                    onClick={() => void selectPlayer(p.id!)}
                  >
                    {p.name}
                  </button>
                );
              })}
            </div>
            <p className="section-label">Замена</p>
            <div className="grid-players">
              {substitutes.map((l) => {
                const p = playerById(l.playerId);
                if (!p) return null;
                return (
                  <button
                    key={l.id}
                    type="button"
                    className={`tag-btn player-btn substitute ${selectedEvent?.playerId === p.id ? 'selected' : ''}`}
                    onClick={() => void selectPlayer(p.id!)}
                  >
                    {p.name}
                  </button>
                );
              })}
            </div>
            <p className="section-label">Команда</p>
            <div className="grid-players">
              {matchTeams.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={`tag-btn team-btn ${selectedEvent?.teamId === t.id ? 'selected' : ''}`}
                  onClick={() => void selectTeam(t.id!)}
                >
                  {t.name}
                </button>
              ))}
            </div>
            {lineupPlayers.length === 0 && (
              <p className="muted">Назначьте состав в подготовке матча</p>
            )}
          </div>

          <div className="card wide">
            <h3>2. Действие</h3>
            <div className="grid-actions">
              {actions.map((act) => (
                <button
                  key={act.id}
                  type="button"
                  className={`tag-btn action-${act.colorClass ?? 'handling'} ${selectedEvent?.actionId === act.id ? 'selected' : ''}`}
                  onClick={() => void selectAction(act)}
                >
                  {act.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {selectedAction?.hasOutcome && (
          <div className="card" style={{ padding: '8px 12px' }}>
            <div className="grid-outcome">
              <button
                type="button"
                className="tag-btn outcome-btn success"
                onClick={() => void selectOutcome('Success')}
              >
                SUCCESS
              </button>
              <button
                type="button"
                className="tag-btn outcome-btn failure"
                onClick={() => void selectOutcome('Failure')}
              >
                FAILURE
              </button>
              <button
                type="button"
                className="tag-btn outcome-btn none"
                onClick={() => void selectOutcome(undefined)}
              >
                БЕЗ РЕЗУЛЬТАТА
              </button>
            </div>
          </div>
        )}

        {selectedEvent && (
          <div className="card">
            <h3>3. Комментарий</h3>
            <div className="grid-comments">
              {actionComments.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="tag-btn"
                  onClick={() => void appendComment(c.text)}
                >
                  {c.text}
                </button>
              ))}
            </div>
            <div className="form-row">
              <input
                className="comment-input"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                onBlur={() => void saveComment()}
                placeholder="Ручной ввод..."
              />
            </div>
          </div>
        )}

        <div className="card">
          <h3>Таймлайн матча (свежие сверху)</h3>
          <div className="table-wrapper">
            <table className="events-table">
              <thead>
                <tr>
                  <th>Тайм</th>
                  <th>Время</th>
                  <th>Игрок/Команда</th>
                  <th>Категория</th>
                  <th>Действие</th>
                  <th>Результат</th>
                  <th>Комментарий</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {displayEvents.map((ev) => {
                  const act = ev.actionId ? actionById(ev.actionId) : undefined;
                  let subject = '—';
                  if (ev.subjectType === 'player' && ev.playerId) {
                    subject = playerById(ev.playerId)?.name ?? '—';
                  } else if (ev.subjectType === 'team' && ev.teamId) {
                    subject = teamById(ev.teamId)?.name ?? '—';
                  }
                  const isScoringEvent =
                    act != null && getScoringPoints(act.name, ev.outcome) > 0;
                  return (
                    <tr
                      key={ev.id}
                      className={[
                        ev.id === selectedEventId ? 'selected' : '',
                        isScoringEvent ? 'scoring-event' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      onClick={() => seekToEvent(ev)}
                    >
                      <td>{ev.periodNumber}</td>
                      <td>{formatTimestamp(ev.timestampSec)}</td>
                      <td>{subject}</td>
                      <td>{act?.categoryName ?? '—'}</td>
                      <td>{act?.name ?? '—'}</td>
                      <td>{ev.outcome ?? '—'}</td>
                      <td>{ev.comment ?? '—'}</td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-danger"
                          onClick={(e) => void deleteEventHandler(ev.id!, e)}
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
