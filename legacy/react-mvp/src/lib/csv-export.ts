import {
  getAction,
  getCategory,
  getPlayer,
  getTeam,
  listEventsByMatch,
} from '../db/repository';
import type { Event } from '../types';

export interface CsvRow {
  period: number;
  time: number;
  subject: string;
  category: string;
  action: string;
  outcome: string;
  comment: string;
}

const CSV_HEADERS = [
  'Тайм',
  'Время',
  'Игрок/Команда',
  'Категория',
  'Действие',
  'Результат',
  'Комментарий',
] as const;

function escapeCsv(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export async function buildCsvRows(matchId: number): Promise<CsvRow[]> {
  const events = await listEventsByMatch(matchId);
  const rows: CsvRow[] = [];

  for (const event of events) {
    const action = event.actionId ? await getAction(event.actionId) : undefined;
    const category = action?.categoryId ? await getCategory(action.categoryId) : undefined;

    let subject = '';
    if (event.subjectType === 'player' && event.playerId) {
      const player = await getPlayer(event.playerId);
      subject = player?.name ?? '';
    } else if (event.subjectType === 'team' && event.teamId) {
      const team = await getTeam(event.teamId);
      subject = team?.name ?? '';
    }

    rows.push({
      period: event.periodNumber,
      time: event.timestampSec,
      subject,
      category: category?.name ?? '',
      action: action?.name ?? '',
      outcome: event.outcome ?? '',
      comment: event.comment ?? '',
    });
  }

  return rows;
}

export function rowsToCsv(rows: CsvRow[]): string {
  const lines = [CSV_HEADERS.join(',')];
  for (const row of rows) {
    lines.push(
      [
        String(row.period),
        String(row.time),
        escapeCsv(row.subject),
        escapeCsv(row.category),
        escapeCsv(row.action),
        escapeCsv(row.outcome),
        escapeCsv(row.comment),
      ].join(','),
    );
  }
  return lines.join('\n');
}

export async function exportMatchToCsv(matchId: number, filename: string): Promise<void> {
  const rows = await buildCsvRows(matchId);
  const csv = rowsToCsv(rows);
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

export async function getEventsForMatch(matchId: number): Promise<Event[]> {
  return listEventsByMatch(matchId);
}
