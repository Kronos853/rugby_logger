import { exportDatabaseBytes, persist } from '../db/sqlite';

function defaultBackupFilename(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `SportsVideoLogger_${date}.db`;
}

export async function downloadDatabaseFile(filename?: string): Promise<void> {
  await persist();
  const data = exportDatabaseBytes();
  const blob = new Blob([data], { type: 'application/x-sqlite3' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename ?? defaultBackupFilename();
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}
