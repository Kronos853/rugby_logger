import initSqlJs from 'sql.js/dist/sql-wasm.js';
import type { Database, SqlValue } from 'sql.js';
import wasmUrl from 'sql.js/dist/sql-wasm.wasm?url';
import { SCHEMA_SQL } from './schema';

const IDB_NAME = 'SportsVideoLoggerStorage';
const IDB_STORE = 'sqlite';
const IDB_KEY = 'db';

let database: Database | null = null;
let initPromise: Promise<void> | null = null;
let persistChain: Promise<void> = Promise.resolve();

function openIdb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(IDB_NAME, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(IDB_STORE);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function normalizeIdbBlob(value: unknown): Uint8Array | null {
  if (!value) return null;
  if (value instanceof Uint8Array) return value;
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  return null;
}

async function loadDbBlob(): Promise<Uint8Array | null> {
  const idb = await openIdb();
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(IDB_STORE, 'readonly');
    const store = tx.objectStore(IDB_STORE);
    const req = store.get(IDB_KEY);
    req.onsuccess = () => resolve(normalizeIdbBlob(req.result));
    req.onerror = () => reject(req.error);
  });
}

async function saveDbBlob(data: Uint8Array): Promise<void> {
  const idb = await openIdb();
  return new Promise((resolve, reject) => {
    const tx = idb.transaction(IDB_STORE, 'readwrite');
    const store = tx.objectStore(IDB_STORE);
    store.put(data, IDB_KEY);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function initDb(): Promise<void> {
  if (initPromise) return initPromise;

  initPromise = (async () => {
    const SQL = await initSqlJs({ locateFile: () => wasmUrl });
    const saved = await loadDbBlob();
    database = saved ? new SQL.Database(saved) : new SQL.Database();
    database.exec(SCHEMA_SQL);
    await persist();
    registerPersistOnHide();
  })();

  return initPromise;
}

let persistOnHideRegistered = false;

function registerPersistOnHide(): void {
  if (persistOnHideRegistered || typeof document === 'undefined') return;
  persistOnHideRegistered = true;

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      void persist();
    }
  });
}

export function getDb(): Database {
  if (!database) throw new Error('Database not initialized');
  return database;
}

export async function persist(): Promise<void> {
  if (!database) return;

  persistChain = persistChain.then(async () => {
    if (!database) return;
    const data = database.export();
    await saveDbBlob(data);
  });

  return persistChain;
}

export function exportDatabaseBytes(): Uint8Array {
  return getDb().export();
}

export function run(sql: string, params: SqlValue[] = []): void {
  getDb().run(sql, params);
}

export function all<T extends Record<string, SqlValue>>(sql: string, params: SqlValue[] = []): T[] {
  const stmt = getDb().prepare(sql);
  stmt.bind(params);
  const rows: T[] = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject() as T);
  }
  stmt.free();
  return rows;
}

export function get<T extends Record<string, SqlValue>>(sql: string, params: SqlValue[] = []): T | undefined {
  return all<T>(sql, params)[0];
}

export function insert(sql: string, params: SqlValue[] = []): number {
  run(sql, params);
  const row = get<{ id: number }>('SELECT last_insert_rowid() AS id');
  return row?.id ?? 0;
}

export async function withWrite<T>(fn: () => T): Promise<T> {
  const result = fn();
  await persist();
  return result;
}

export async function withWriteVoid(fn: () => void): Promise<void> {
  fn();
  await persist();
}
