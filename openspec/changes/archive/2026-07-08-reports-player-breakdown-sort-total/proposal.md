## Why

В правой панели «По игрокам» (разбивка по действию в командном отчёте) строки сейчас отсортированы по имени (`ORDER BY SubjectLabel`). Тренеру удобнее сразу видеть лидеров по объёму — сортировка по колонке **«Всего»** (или **«Кол-во»** для действий без outcome) по убыванию.

## What Changes

- **Сортировка** таблицы разбивки по игрокам: `total` DESC
- **Вторичный ключ** при равном total: имя субъекта ASC (стабильный порядок)
- Затрагивает панель `/reports/player-panel?mode=action-breakdown` и legacy `/reports/player-detail` (один SQL-запрос)

## Capabilities

### New Capabilities

_(нет)_

### Modified Capabilities

- `reporting`: requirement «Player Drill-Down in Team Report» — порядок строк в breakdown

## Impact

- `backend/repository.py` — `get_report_player_detail`: `ORDER BY Total DESC, SubjectLabel`
- `tests/test_reports_split.py` — проверка порядка строк
- `openspec/specs/reporting/spec.md` — delta при архивации
