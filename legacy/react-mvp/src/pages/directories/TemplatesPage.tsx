import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteSportTemplate } from '../../db/cleanup';
import {
  createSportTemplate,
  listSportTemplates,
} from '../../db/repository';
import { ensureSeeded, seedRugbyTemplate } from '../../db/seed';
import type { SportTemplate } from '../../types';

export function TemplatesPage() {
  const [templates, setTemplates] = useState<SportTemplate[]>([]);
  const [name, setName] = useState('');

  async function load() {
    await ensureSeeded();
    setTemplates(await listSportTemplates());
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await createSportTemplate(name.trim());
    setName('');
    await load();
  }

  async function handleSeedRugby() {
    await seedRugbyTemplate();
    await load();
  }

  async function handleDelete(template: SportTemplate) {
    if (!template.id || !confirm(`Удалить шаблон «${template.name}»?`)) return;
    try {
      await deleteSportTemplate(template.id);
      await load();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Не удалось удалить шаблон');
    }
  }

  return (
    <div>
      <h1 className="page-title">Шаблоны спорта</h1>

      <div className="card">
        <form className="form-row" onSubmit={handleAdd}>
          <input
            placeholder="Название шаблона"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Добавить
          </button>
          <button type="button" className="btn" onClick={() => void handleSeedRugby()}>
            Загрузить Регби-7
          </button>
        </form>
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
            {templates.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td>
                  <Link to={`/directories/templates/${t.id}`}>Редактировать →</Link>
                  {' | '}
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => void handleDelete(t)}
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
