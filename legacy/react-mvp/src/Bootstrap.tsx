import { useEffect, useState } from 'react';
import { initDb } from './db/sqlite';
import { ensureSeeded } from './db/seed';
import App from './App';

export default function Bootstrap() {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void initDb()
      .then(() => ensureSeeded())
      .then(() => setReady(true))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        console.error('Database init failed:', err);
        setError(message);
      });
  }, []);

  if (error) {
    return <p style={{ padding: 20, color: '#c00' }}>Ошибка инициализации БД: {error}</p>;
  }

  if (!ready) {
    return <p style={{ padding: 20 }}>Загрузка базы данных...</p>;
  }

  return <App />;
}
