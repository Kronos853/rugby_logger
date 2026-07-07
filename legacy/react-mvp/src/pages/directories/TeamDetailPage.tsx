import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { deletePlayer } from '../../db/cleanup';
import { createPlayer, getTeam, listPlayersByTeam } from '../../db/repository';
import type { Player, Team } from '../../types';

export function TeamDetailPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const id = Number(teamId);

  const [team, setTeam] = useState<Team | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [name, setName] = useState('');
  const [position, setPosition] = useState('');

  async function load() {
    setTeam((await getTeam(id)) ?? null);
    setPlayers(await listPlayersByTeam(id));
  }

  useEffect(() => {
    if (id) void load();
  }, [id]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await createPlayer(id, name.trim(), position.trim() || undefined);
    setName('');
    setPosition('');
    await load();
  }

  async function handleDelete(player: Player) {
    if (!player.id || !confirm(`Удалить игрока «${player.name}»?`)) return;
    await deletePlayer(player.id);
    await load();
  }

  if (!team) return <p>Команда не найдена</p>;

  return (
    <div>
      <p>
        <Link to="/directories/teams">← Команды</Link>
      </p>
      <h1 className="page-title">{team.name}</h1>

      <div className="card">
        <form className="form-row" onSubmit={handleAdd}>
          <input
            placeholder="Имя игрока"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            placeholder="Позиция (опц.)"
            value={position}
            onChange={(e) => setPosition(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Добавить игрока
          </button>
        </form>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Позиция</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {players.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.defaultPosition ?? '—'}</td>
                <td>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => void handleDelete(p)}
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
