## Context

The application stores sport templates, teams, squads, matches, and tagging events locally in the browser. The team has strong MS SQL experience; the logical schema is defined in `docs/schema.sql`.

## Goals / Non-Goals

**Goals:**
- Provide robust local data persistence using **relational SQL** in the browser.
- Reuse the existing logical schema (tables, FKs, constraints) with minimal adaptation for SQLite.
- Keep the React UI and BroadcastChannel video sync unchanged.
- Persist the database file between sessions; **export `.db` backup via administration page**.
- Show **live match score** during tagging and on match pages (computed from events).

**Non-Goals:**
- Local Node/Postgres server in this phase.
- Cloud sync.
- Persisting auto-score into `Match.scoreHome` / `Match.scoreAway` (manual fields at match creation remain optional; displayed score is event-driven).

## Decisions

1. **Local Database: SQLite WASM (sql.js)**
   - *Rationale*: True SQL (JOINs, constraints, migrations) without a backend. Fits MS SQL mental model. `docs/schema.sql` maps almost 1:1 to SQLite DDL.
   - *Persistence*: sql.js in-memory DB serialized to IndexedDB after each write batch.
   - *Alternatives rejected*: Dexie/IndexedDB (no SQL), local API + SQLite (extra process), Postgres (needs server).

2. **Data access layer: `repository.ts`**
   - *Rationale*: Pages call typed repository functions; SQL stays in one place. Easier to swap persistence later than scattering queries in UI.
   - *Queries*: Parameterized SQL only (`?` placeholders).

3. **Schema: SQLite DDL with `PRAGMA foreign_keys = ON`**
   - *Rationale*: CASCADE deletes for categories → actions → comments; manual checks for template/team in use by matches.
   - *Naming*: PascalCase table/column names aligned with `docs/schema.sql` for Postgres migration later.

4. **Two-Screen Synchronization: BroadcastChannel API** (unchanged)

5. **Video Handling: Local File Selection** (unchanged)

6. **App bootstrap: `Bootstrap.tsx`**
   - *Rationale*: `initDb()` → `ensureSeeded()` before rendering `App`; never mutate `#root` with `innerHTML` before `createRoot`.
   - *sql.js + Vite*: import `sql.js/dist/sql-wasm.js`; `optimizeDeps.include`; apply DDL via `database.exec(SCHEMA_SQL)`.

7. **Match score: `src/lib/match-score.ts`**
   - *Rules (Rugby-7 MVP)*: `try` → 5 pts; action name starting with `conversion` (after homoglyph normalization) → 2 pts unless `outcome === Failure`.
   - *Team attribution*: `event.teamId` if set; else `event.playerId` → match lineup team, fallback to player's roster team.
   - *Homoglyphs*: Cyrillic lookalikes (e.g. «С» in «Сonversion») normalized to Latin before matching action names.
   - *UI*: `MatchScoreDisplay` on tagging control panel, match setup, matches list; scoring rows bold in timeline.

8. **Administration & DB backup: `/admin`**
   - *Rationale*: Single-user local app; no auth. Full backup via `database.export()` after `persist()`.
   - *Download*: `src/lib/db-export.ts`; default filename `SportsVideoLogger_YYYY-MM-DD.db`.
   - *Import*: Phase 2 (restore from `.db` file).

9. **DB init single-flight & persist safety**
   - *Problem*: React StrictMode could run `initDb()` twice, reassigning `database` and overwriting IndexedDB with an empty instance.
   - *Fix*: `initPromise` guard; normalize IDB blob (`ArrayBuffer` → `Uint8Array`); persist on `visibilitychange` hidden.
   - *Note*: IndexedDB is per origin — `localhost:5173` ≠ `localhost:5175`; use a consistent dev URL.

10. **Tech Stack**
   - *Build*: Vite + TypeScript
   - *UI*: React + React Router
   - *Local DB*: **sql.js (SQLite WASM)** + repository layer
   - *Validation*: Zod
   - *Window sync*: BroadcastChannel
   - *Phase 2*: SQL-based reports; Chart.js; LLM API

11. **Future: Postgres**
   - Same schema; replace sql.js repository with API + Postgres (Drizzle/Prisma).
   - CSV export remains; `.db` backup compatible with SQLite tools.

## Risks / Trade-offs

- **[Risk] sql.js loads entire DB into memory**
  - *Mitigation*: Dataset is small (single-user stats); acceptable for MVP.
- **[Risk] IndexedDB persistence of DB blob**
  - *Mitigation*: Encourage periodic `.db` export from administration page; CSV per match as secondary backup.
- **[Risk] WASM load time on first open**
  - *Mitigation*: ~1–2s once; loading state in `Bootstrap.tsx`.
- **[Risk] Action names with Cyrillic homoglyphs break score rules**
  - *Mitigation*: `latinizeHomoglyphs()` in `match-score.ts`; recommend Latin names in templates.
- **[Risk] Score rules hardcoded for Rugby-7**
  - *Mitigation*: Acceptable for MVP; Phase 2 can move rules to sport template metadata.
