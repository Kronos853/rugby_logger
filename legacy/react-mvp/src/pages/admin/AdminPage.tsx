import { useState } from 'react';
import { downloadDatabaseFile } from '../../lib/db-export';

export function AdminPage() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      await downloadDatabaseFile();
      setMessage('Файл базы данных загружен.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выгрузить базу данных');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Администрирование</h1>

      <div className="card">
        <h3>Резервная копия базы данных</h3>
        <p className="muted">
          Скачайте полную копию SQLite-базы (.db) со всеми шаблонами, командами, матчами и
          событиями. Файл можно открыть в DB Browser for SQLite или использовать для переноса
          данных.
        </p>
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy}
          onClick={() => void handleExport()}
        >
          {busy ? 'Подготовка…' : 'Скачать базу данных (.db)'}
        </button>
        {message && <p style={{ marginTop: 12, color: '#198754' }}>{message}</p>}
        {error && <p style={{ marginTop: 12, color: '#c00' }}>{error}</p>}
      </div>
    </div>
  );
}
