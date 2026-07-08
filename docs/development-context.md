# Контекст разработки — Sports Video Logger

> **Назначение:** снимок состояния проекта для продолжения работы в новых чатах/сессиях.  
> Обновляйте этот файл при значимых архитектурных или продуктовых изменениях.

**Последнее обновление:** 2026-07-07 (tagging-step-scroll-focus: автоскролл к следующему шагу разметки)

---

## Что это за проект

Локальное **однопользовательское** веб-приложение для **постматчевой** разметки спортивной статистики по видео. Первый вид спорта — **Регби-7**, архитектура **мультиспорт** через шаблоны.

- Видео **не хранится** в БД — только локальный файл в браузере
- Два монитора: пульт разметки + видеоплеер (`BroadcastChannel`)
- Экспорт событий в CSV для внешнего анализа / ИИ (фаза 2 — встроенные отчёты и чат)

---

## Статус

| Область | Статус |
|---------|--------|
| Активный стек | **Flask + SQLite file + HTMX** |
| Legacy React MVP | **Только** `legacy/react-mvp/` (корневой `src/` удалён) |
| OpenSpec archived | `2026-07-04-sports-video-logger-mvp`, `2026-07-05-stack-python-htmx`, `2026-07-05-player-profile-fields` |
| Main specs | `openspec/specs/` (10 capabilities) |
| OpenSpec archived | incl. `2026-07-06-tournament-refactor`, `2026-07-06-phase2-reports` |
| Фаза 2 (отчёты, ИИ) | **Отчёты реализованы**; ИИ — не начат |

---

## Запуск и отладка

**Windows:** двойной клик по `start.bat` или `.\scripts\start.ps1` — создаётся `.venv`, ставятся Python зависимости и запускается Flask.

```bash
cd c:\IT\Analytic
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app
```

- Открывать `http://127.0.0.1:5000`
- БД хранится в `data/sports_logger.db`
- Legacy React-сборка (архив): `legacy/react-mvp/`

---

## Архитектура (текущая)

```
┌─────────────────────────────────────────────────────────────┐
│ Flask routes + Jinja templates + HTMX partial updates       │
└──────────────────────────┬──────────────────────────────────┘
                           │ backend/repository.py
┌──────────────────────────▼──────────────────────────────────┐
│ SQLite file: data/sports_logger.db                          │
└─────────────────────────────────────────────────────────────┘

Синхронизация окон: BroadcastChannel (`static/tagging.js`)
```

### Точка входа

`python -m backend.app` → `backend/app.py` (Flask factory, маршруты, шаблоны)

### База данных

| Файл | Роль |
|------|------|
| `docs/schema.sql` | Логическая схема (эталон, PascalCase) |
| `backend/db.py` | Подключение, init schema, миграции, backup |
| `backend/repository.py` | Все CRUD — **единственная точка SQL** |
| `backend/seed.py` | Сид Регби-7, `copy_squad_to_match_lineup` |

Миграции: `_pending_migrations()` / `_apply_migrations()` в `backend/db.py`. Перед DDL — автоматический backup.

---

## Маршруты (`backend/app.py`)

| Путь | Страница |
|------|----------|
| `/` | Главная |
| `/directories/templates` | Список шаблонов |
| `/directories/templates/<template_id>` | Категории, действия, подсказки |
| `/directories/teams` | Команды |
| `/directories/teams/<team_id>` | Игроки команды (IsActive, показ неактивных) |
| `/directories/teams/<team_id>/players/<player_id>/edit` | Профиль игрока |
| `/directories/squads` | Сохранённые составы |
| `/matches` | Список матчей |
| `/matches/<match_id>/setup` | Подготовка (составы, дата, турнир) |
| `/reports` | Отчёты (командный split-view + панель «По игрокам»; индивидуальный — отдельный режим) |
| `/settings` | Настройки (основная команда для отчётов) |
| `/tagging/<match_id>/control` | Пульт разметки |
| `/tagging/<match_id>/video` | Видео на 2-м мониторе |
| `/admin` | Экспорт/импорт `.db` |

---

## Модель данных (кратко)

Сущности: `SportTemplate` → `Category` → `Action` → `CommentTemplate`; `Tournament` (глобальный справочник); `Team` → `Player`; `Squad` → `SquadPlayer`; `Match` → `MatchLineup`, `MatchPeriod`, `Event`.

| Решение | Деталь |
|---------|--------|
| `LineupRole` | `starter` / `substitute` — только UX, не в CSV |
| Виртуальные команды | `subjectType: 'team'` в Event |
| CSV колонки | `Тайм, Время, Игрок/Команда, Категория, Действие, Результат, Комментарий` |
| Автосчёт (Регби-7) | try = 5; conversion* = 2 (*не Failure); `backend/match_score.py` |
| Счёт в БД | Отображаемый счёт — из событий |

Полные требования: `docs/exploration.md`

---

## Реализованный функционал

- CRUD справочников, матчи, составы, разметка с draft-событиями
- Пульт разметки: липкий блок **«ТЕКУЩЕЕ СОБЫТИЕ»** (режим НОВОЕ/РЕДАКТИРОВАНИЕ, чипы Игрок→Действие→Результат, тайм); **scroll-focus** к следующему шагу после capture/update
- Профиль игрока (FullName, BirthDay), деактивация (IsActive)
- Автосчёт, жирные scoring-строки в таймлайне
- CSV импорт/экспорт на пульте (legacy-формат + стандартные колонки)
- Двухоконная синхронизация видео, seek по клику на строку
- `/admin` — экспорт/импорт SQLite `.db`
- `/reports` — командный отчёт в двух колонках (слева действия, справа разбивка по игрокам для выбранного действия); индивидуальный отчёт — отдельный режим формы
- Статистика игрока за 5 матчей (таблица по категориям/действиям)
- ShowInReport / PeriodCount в шаблонах спорта
- Автосид «Регби-7» при пустой БД
- Запуск: `start.bat`, `scripts/start.ps1`

---

## Фаза 2 (backlog)

- Встроенные отчёты (матч / сезон, success/failure)
- Конструктор отчётов
- ИИ-чат через API
- Другие шаблоны спорта

---

## Конвенции кода

- UI **не пишет SQL** — только `backend/repository.py`
- PascalCase в SQL как в `docs/schema.sql`
- Минимальный diff; не переусложнять
- Стили: `static/app.css`, `static/tagging.css`
- Legacy-прототипы в корне: `control_panel.html`, `video_screen.html`, `analyse.html` — **не трогать** без запроса

### Тестирование и тестовые данные

- **Запрещено** писать/удалять/обновлять записи в `data/sports_logger.db` при автоматических проверках агентом
- **Не трогать** существующие данные пользователя — тестировать только на **новых** записях с именами вида `TEST_*` в изолированной БД
- Допустимо: `app.test_client()`, `sqlite3.connect(':memory:')`, копия БД в `%TEMP%` или `data/import_test.db`
- После теста — удалить все `TEST_*` записи и временные файлы

### Backup перед изменением структуры БД

- Перед DDL/миграцией — **автоматический backup** в `ensure_db()` → `backup_database_file()`
- Файлы: `data/sports_logger.backup-pre-migrate-YYYY-MM-DD-HHMMSS.db`
- Ручной экспорт: `/admin`; при импорте — safety backup `sports_logger.backup-YYYY-MM-DD.db`

---

## OpenSpec

- Main specs: `openspec/specs/`
- Архив changes: `openspec/changes/archive/`
- Команды Cursor: `/opsx-apply`, `/opsx-archive`, `/opsx-propose`, `/opsx-explore`

---

## Карта исходников

```
backend/
├── app.py              # Flask routes
├── db.py               # schema init, migrations, backup
├── repository.py       # all SQL
├── seed.py
├── match_score.py
├── csv_export.py
├── csv_import.py
└── format_time.py

templates/              # Jinja pages + HTMX partials
static/                 # app.css, tagging.css/js, form-scroll.js
legacy/react-mvp/       # archived React MVP (reference only)
```

---

## Ссылки

| Документ | Содержание |
|----------|------------|
| [README.md](../README.md) | Быстрый старт |
| [exploration.md](./exploration.md) | Требования, UX, решения |
| [schema.sql](./schema.sql) | SQL-схема |

---

## Чеклист для новой сессии

1. Прочитать этот файл
2. `python -m backend.app` — проверить что приложение открывается на `:5000`
3. При изменении схемы — обновить `docs/schema.sql` и миграции в `backend/db.py`
4. После крупных фич — обновить этот документ
