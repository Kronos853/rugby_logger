import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteSquad } from '../../db/cleanup';
import {
  addSquadPlayer,
  createSquad,
  deleteSquadPlayer,
  getSquad,
  listPlayersByTeam,
  listSquads,
  listSquadPlayers,
  listTeams,
  updateSquad,
  updateSquadPlayerRole,
} from '../../db/repository';
import type { LineupRole, Player, Squad, SquadPlayer, Team } from '../../types';

export function SquadsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [squads, setSquads] = useState<Squad[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<number | ''>('');
  const [squadName, setSquadName] = useState('');
  const [tournament, setTournament] = useState('');

  const [editingSquadId, setEditingSquadId] = useState<number | null>(null);
  const [editSquadName, setEditSquadName] = useState('');
  const [editSquadTournament, setEditSquadTournament] = useState('');
  const [squadPlayers, setSquadPlayers] = useState<SquadPlayer[]>([]);
  const [teamPlayers, setTeamPlayers] = useState<Player[]>([]);

  async function load() {
    setTeams(await listTeams());
    setSquads(await listSquads());
  }

  useEffect(() => {
    void load();
  }, []);

  async function openSquad(squadId: number) {
    setEditingSquadId(squadId);
    const squad = await getSquad(squadId);
    if (!squad) return;
    setEditSquadName(squad.name);
    setEditSquadTournament(squad.tournament ?? '');
    setTeamPlayers(await listPlayersByTeam(squad.teamId));
    setSquadPlayers(await listSquadPlayers(squadId));
  }

  async function saveSquadMeta() {
    if (!editingSquadId) return;
    const name = editSquadName.trim();
    if (!name) return;
    await updateSquad(editingSquadId, {
      name,
      tournament: editSquadTournament.trim() || null,
    });
    await load();
    await openSquad(editingSquadId);
  }

  async function createSquadHandler(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTeamId || !squadName.trim()) return;
    await createSquad(Number(selectedTeamId), squadName.trim(), tournament.trim() || undefined);
    setSquadName('');
    setTournament('');
    await load();
  }

  async function addPlayerToSquad(playerId: number) {
    if (!editingSquadId) return;
    const exists = squadPlayers.some((sp) => sp.playerId === playerId);
    if (exists) return;
    await addSquadPlayer(editingSquadId, playerId, squadPlayers.length);
    await openSquad(editingSquadId);
  }

  async function toggleRole(sp: SquadPlayer) {
    if (!sp.id || !editingSquadId) return;
    const role: LineupRole = sp.lineupRole === 'starter' ? 'substitute' : 'starter';
    await updateSquadPlayerRole(sp.id, role);
    await openSquad(editingSquadId);
  }

  async function removeFromSquad(sp: SquadPlayer) {
    if (!sp.id || !editingSquadId) return;
    await deleteSquadPlayer(sp.id);
    await openSquad(editingSquadId);
  }

  async function handleDeleteSquad(squad: Squad) {
    if (!squad.id || !confirm(`Удалить состав «${squad.name}»?`)) return;
    await deleteSquad(squad.id);
    if (editingSquadId === squad.id) setEditingSquadId(null);
    await load();
  }

  const editingSquad = squads.find((s) => s.id === editingSquadId);
  const playerName = (pid: number) => teamPlayers.find((p) => p.id === pid)?.name ?? '?';
  const teamName = (tid: number) => teams.find((t) => t.id === tid)?.name ?? '?';

  return (
    <div>
      <h1 className="page-title">Сохранённые составы</h1>

      <div className="card">
        <form className="form-row" onSubmit={createSquadHandler}>
          <select
            value={selectedTeamId}
            onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">Команда</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Название состава"
            value={squadName}
            onChange={(e) => setSquadName(e.target.value)}
          />
          <input
            placeholder="Турнир (опц.)"
            value={tournament}
            onChange={(e) => setTournament(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Создать состав
          </button>
        </form>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Список составов</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Команда</th>
                <th>Состав</th>
                <th>Турнир</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {squads.map((s) => (
                <tr key={s.id}>
                  <td>{teamName(s.teamId)}</td>
                  <td>{s.name}</td>
                  <td>{s.tournament ?? '—'}</td>
                  <td>
                    <button type="button" className="btn" onClick={() => void openSquad(s.id!)}>
                      Редактировать
                    </button>
                    {' '}
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => void handleDeleteSquad(s)}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {editingSquad && (
          <div className="card">
            <h3>{teamName(editingSquad.teamId)}</h3>
            <div className="form-row">
              <input
                placeholder="Название состава"
                value={editSquadName}
                onChange={(e) => setEditSquadName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void saveSquadMeta();
                }}
              />
              <input
                placeholder="Турнир (опц.)"
                value={editSquadTournament}
                onChange={(e) => setEditSquadTournament(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void saveSquadMeta();
                }}
              />
              <button type="button" className="btn btn-primary" onClick={() => void saveSquadMeta()}>
                Сохранить
              </button>
            </div>
            <p className="muted">Добавьте игроков и отметьте основной / замена</p>

            <div className="form-row">
              {teamPlayers
                .filter((p) => !squadPlayers.some((sp) => sp.playerId === p.id))
                .map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className="btn"
                    onClick={() => void addPlayerToSquad(p.id!)}
                  >
                    + {p.name}
                  </button>
                ))}
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th>Игрок</th>
                  <th>Роль</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {squadPlayers.map((sp) => (
                  <tr key={sp.id}>
                    <td>{playerName(sp.playerId)}</td>
                    <td>
                      <button type="button" className="btn" onClick={() => void toggleRole(sp)}>
                        {sp.lineupRole === 'starter' ? 'Основной' : 'Замена'}
                      </button>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-danger"
                        onClick={() => void removeFromSquad(sp)}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p>
        <Link to="/matches">Перейти к матчам →</Link>
      </p>
    </div>
  );
}
