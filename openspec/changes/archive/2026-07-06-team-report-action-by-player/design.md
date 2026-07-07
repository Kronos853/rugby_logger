## Context

Страница `/reports` рендерит результаты через макрос `report_results` (`templates/_report_results.html`). Командный отчёт агрегирует события всех игроков команды + `SubjectType='team'` (`_report_subject_clause` в `repository.py`).

Уже реализован lazy drill-down «Комментарии»: кнопка → `htmx.ajax` → `GET /reports/comment-detail` → partial `_report_comment_detail.html`. Паттерн проверен, повторяем для разбивки по игрокам.

## Goals / Non-Goals

**Goals:**

- Разворот строки действия в командном отчёте → подтаблица «игрок / метрики»
- Те же фильтры, что у основного отчёта: даты, турнир, опционально `matchId` в режиме «по матчам»
- Строка «Команда» для событий с `SubjectType='team'`
- Сортировка игроков по имени; нулевые строки не показывать

**Non-Goals:**

- Drill-down по игрокам в индивидуальном отчёте
- Вложенность игрок → комментарии (достаточно двух независимых кнопок)
- Экспорт подтаблицы в CSV
- Игроки соперника (в командном отчёте только своя команда)

## Decisions

### 1. Lazy-load через HTMX (как комментарии)

**Решение:** `GET /reports/player-detail` + `toggleReportPlayer(btn)` в `reports.js`.

**Почему:** Не раздувает HTML при генерации отчёта с сотнями действий; консистентно с существующим UX.

### 2. Новый запрос `get_report_player_detail`

**Решение:** SQL с `GROUP BY` по `e.PlayerId` / `e.TeamId`, фильтр:

```sql
e.ActionId = ?
AND (player in team OR team event for team)
AND date/tournament/match filters
```

Возвращать: `SubjectLabel` (имя игрока или команды), `SubjectKind` (`player`|`team`), counts.

**Альтернатива отвергнута:** переиспользовать N вызовов `get_report_data(subject_type=player)` — N+1 запросов при каждом развороте.

### 3. UI: кнопка только для `report_ctx.subject_type == 'team'`

**Решение:** В `_report_results.html` обернуть кнопку «По игрокам» в `{% if report_ctx.subject_type == 'team' %}`.

### 4. Partial `_report_player_detail.html`

**Решение:** Та же структура колонок, что `_report_comment_detail.html`, но первая колонка «Игрок/Команда».

Переиспользовать `_enrich_action_row` из `reports.py` для расчёта `success_pct`.

### 5. Уникальные id контейнеров

**Решение:** `player-{scope}-{action_id}` — scope уже есть для per-match (`report_ctx.scope`).

## Risks / Trade-offs

- **[Risk] Игрок ушёл из команды, но события в периоде есть** → Показывать по `Player.TeamId` на момент запроса или по событиям в матчах команды; используем тот же subject clause, что и основной отчёт (игроки с `Player.TeamId = team`)
- **[Risk] Два открытых drill-down** → Независимые контейнеры; допустимо держать открытыми комментарии и игроков одновременно
- **[Risk] Длинный список игроков** → Подтаблица в `.report-player-table`; при необходимости позже — max-height + scroll

## Migration Plan

1. Repository + route + partial + JS + template
2. Ручная проверка: командный отчёт → развернуть Pass → сумма по игрокам = total строки
3. Откат: удалить endpoint и кнопку

## Open Questions

- Показывать ли игроков с 0 событий по данному действию? **Нет** — только `HAVING COUNT(*) > 0` (как в основном отчёте)
