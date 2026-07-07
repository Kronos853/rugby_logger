## 7. SQLite WASM migration

- [x] 7.1 Update design/proposal for sql.js decision
- [x] 7.2 Add sql.js, SQLite schema DDL, init + IndexedDB persistence
- [x] 7.3 Implement SQL repository layer (replace Dexie `database.ts`)
- [x] 7.4 Migrate seed, cleanup, and all pages to repository
- [x] 7.5 Remove Dexie dependency; verify build

## 8. Post-MVP polish (session 2026-06)

- [x] 8.1 Fix app bootstrap: `Bootstrap.tsx`, sql.js Vite import (`sql.js/dist/sql-wasm.js`), `database.exec()` for DDL
- [x] 8.2 Add Windows launch scripts: `start.bat`, `scripts/start.ps1`, `npm start`
- [x] 8.3 Add `docs/development-context.md` and `.cursor/rules/project-context.mdc`
- [x] 8.4 Edit action name in template detail (`updateActionName`)
- [x] 8.5 Edit squad name/tournament when editing squad (`updateSquad`)
- [x] 8.6 Auto match score from events (`src/lib/match-score.ts`, `MatchScoreDisplay`)
- [x] 8.7 Score on matches list, match setup, and tagging control panel
- [x] 8.8 Highlight scoring events (try, conversion) in bold on tagging timeline
- [x] 8.9 Homoglyph-safe action name matching for score (Cyrillic «С» in «Сonversion»)

## 9. Administration — database export

- [x] 9.1 OpenSpec: `administration` capability spec, proposal/design updates
- [x] 9.2 `exportDatabaseFile()` in sqlite layer + `src/lib/db-export.ts`
- [x] 9.3 Administration page `/admin` with download button
- [x] 9.4 Navigation link (Layout, HomePage)

## 10. Data persistence fix

- [x] 10.1 Single-flight `initDb()` to prevent StrictMode race wiping IndexedDB
- [x] 10.2 Normalize IndexedDB blob (ArrayBuffer → Uint8Array)
- [x] 10.3 Persist on tab hide (`visibilitychange`)