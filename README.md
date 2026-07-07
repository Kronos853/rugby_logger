# Sports Video Logger

Локальное веб-приложение для разметки спортивной статистики по видео.

## Стек

- Python 3.11+ + Flask
- SQLite на диске: `data/sports_logger.db`
- Jinja2 + HTMX (+ Alpine.js CDN)
- BroadcastChannel + `static/tagging.js` для двух окон

## Запуск

### Быстрый старт (Windows)

Дважды кликните **`start.bat`** в корне проекта — создаст `.venv`, установит зависимости и запустит сервер.

Или в PowerShell:

```powershell
.\scripts\start.ps1
```

### Вручную

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app
```

Откройте `http://127.0.0.1:5000`.

## Основные маршруты

- `/directories/templates` — шаблоны спорта, категории, действия, подсказки
- `/directories/teams` — команды и игроки
- `/directories/squads` — сохранённые составы
- `/matches` — матчи и подготовка составов
- `/tagging/<match_id>/control` — пульт разметки (импорт/экспорт CSV)
- `/tagging/<match_id>/video` — видео окно на 2-й монитор
- `/admin` — экспорт/импорт SQLite базы

## Прототипы (legacy)

`control_panel.html`, `video_screen.html`, `analyse.html`

## Legacy React MVP backup

Предыдущая реализация сохранена в `legacy/react-mvp/`.

## Контекст для разработки

Полный снимок состояния проекта, архитектуры и backlog: [`docs/development-context.md`](docs/development-context.md)
