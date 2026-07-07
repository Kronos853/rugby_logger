# React MVP (архив)

Снимок реализации **Sports Video Logger** до миграции на Python + HTMX.

**Дата бэкапа:** 2026-07-04

## Стек

- React 19 + Vite + TypeScript
- sql.js (SQLite WASM) → IndexedDB
- React Router

## Запуск (если нужно поднять старую версию)

Из корня репозитория:

```bash
cd legacy/react-mvp
npm install
npm run dev
```

Либо скопировать `src/` и конфиги обратно в корень и запустить `npm start` из корня (как было до миграции).

## Содержимое

| Путь | Назначение |
|------|------------|
| `src/` | UI, repository, seed, CSV export, tagging |
| `index.html`, `vite.config.ts` | Сборка Vite |
| `package.json` | Зависимости React MVP |

Активная разработка ведётся в `backend/`, `templates/`, `static/` (см. change `stack-python-htmx`).
