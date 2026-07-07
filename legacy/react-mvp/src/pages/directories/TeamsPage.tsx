import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteTeam } from '../../db/cleanup';
import { createTeam, listTeams } from '../../db/repository';
import type { Team } from '../../types';

export function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState('');

  async function load() {
    setTeams(await listTeams());
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await createTeam(name.trim());
    setName('');
    await load();
  }

  async function handleDelete(team: Team) {
    if (!team.id || !confirm(`Удалить команду «${team.name}»?`)) return;
    try {
      await deleteTeam(team.id);
      await load();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Не удалось удалить команду');
    }
  }

  return (
    <div>
      <h1 className="page-title">Команды</h1>

      <div className="card">
        <form className="form-row" onSubmit={handleAdd}>
          <input
            placeholder="Название команды"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Добавить
          </button>
        </form>
        <p className="muted">
          Команда может быть без игроков — для соперника или командных действий.
        </p>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Название</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {teams.map((team) => (
              <tr key={team.id}>
                <td>{team.name}</td>
                <td>
                  <Link to={`/directories/teams/${team.id}`}>Игроки →</Link>
                  {' | '}
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => void handleDelete(team)}
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
