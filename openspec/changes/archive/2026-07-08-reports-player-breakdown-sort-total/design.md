## Context

Командный отчёт: кнопка «По игрокам» на строке действия → HTMX загружает `_report_player_panel.html` → `_report_player_detail.html`.

Данные: `repo.get_report_player_detail()` → `build_player_detail()` → шаблон. Сейчас SQL: `ORDER BY SubjectLabel`.

Колонка «Всего» / «Кол-во» — поле `Total` / `row.total`.

## Goals / Non-Goals

**Goals:**

- Строки breakdown отсортированы по убыванию total
- При равном total — по алфавиту имени

**Non-Goals:**

- Интерактивная сортировка по клику на заголовок
- Изменение порядка в основной таблице отчёта или comment drill-down
- Сортировка в индивидуальном отчёте (там нет player breakdown)

## Decisions

### 1. Сортировка в SQL

**Решение:** `ORDER BY Total DESC, SubjectLabel ASC` в `get_report_player_detail`.

**Почему:** единственная точка данных; не дублировать в `build_player_detail`; пагинации нет.

**Альтернатива:** `sorted()` в Python — лишний слой без выгоды.

### 2. Tie-breaker

Имя субъекта ASC — предсказуемо при одинаковом количестве (например, 0 не попадает из-за `HAVING COUNT(*) > 0`).

### 3. Команда как строка

Строка `SubjectType='team'` сортируется наравне с игроками по total, не выносится отдельно.

## Risks / Trade-offs

| Риск | Митигация |
|------|-----------|
| Пользователь привык к алфавиту | осознанное UX-решение; откат — одна строка SQL |

## Migration Plan

Нет миграции БД. Деплой — только backend + тест.

## Open Questions

_(нет)_
