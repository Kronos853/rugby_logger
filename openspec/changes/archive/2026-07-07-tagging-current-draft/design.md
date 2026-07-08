## Context

Пульт разметки (`/tagging/<id>/control`) — двухколоночный layout (ввод слева, таймлайн справа). До изменения: серая `status-bar` при отсутствии выбранного события; при выборе — кнопки активны, но нет единого резюме черновика.

Lazyweb-отчёт [Improve rugby tagging ergonomics](https://www.lazyweb.com/report/lazyweb/9c22676f-495d-4ece-b8fd-6446c8516817/?source=create), вариант **«Текущий Черновик»** — мокап `mockup-current-event-draft.png` в этой папке.

Стек: Flask + Jinja, без HTMX на шагах ввода (full POST + redirect). Session хранит `selected_event_{match_id}`.

## Goals / Non-Goals

**Goals:**

- Липкий блок **ТЕКУЩЕЕ СОБЫТИЕ** по мокапу: заголовок, бейдж, чипы, тайм
- Режим **НОВОЕ** / **РЕДАКТИРОВАНИЕ** через session `draft_mode_{match_id}`
- Убрать status-bar; контекст черновика всегда в блоке

**Non-Goals:**

- Степпер 1→4 (отклонён после ревью — лишняя высота)
- Ряд «Последние» действий (отклонён — занимает место)
- Полоса повтора под тулбаром (вариант Lazyweb #3)
- Палитра кода, hotkeys, таймлайн-центричный layout

## Decisions

### 1. Partial `_current_event_draft.html`

**Решение:** отдельный include вверху `.tagging-input-col`; данные из `_load_tagging_context`.

**Поля контекста:** `draft_mode`, `draft_player_label`, `draft_action_label`, `draft_outcome_label`, `selected_action` (для outcome-карточки ниже).

### 2. Режим draft в session

| Событие | `draft_mode_{match_id}` |
|---------|-------------------------|
| POST `/capture` | `new` |
| POST `/event/<id>/select` | `edit` |
| DELETE выбранного | ключ удаляется |

Бейдж: `НОВОЕ` если `selected_event` и mode ≠ `edit`; `РЕДАКТИРОВАНИЕ` если mode = `edit`.

### 3. Визуальная спецификация (мокап)

| Элемент | Copy / стиль |
|---------|----------------|
| Заголовок | `ТЕКУЩЕЕ СОБЫТИЕ` (uppercase, 12px bold) |
| Бейдж НОВОЕ | голубой pill `#cfe2ff` / `#084298` |
| Бейдж РЕДАКТИРОВАНИЕ | жёлтый pill `#fff3cd` / `#664d03` |
| Чипы | `[Игрок: …]`, `[Действие: …]`, `[Результат: …]` на сером фоне |
| Время | справа: `Тайм: {n} • {m-ss}`; без события — `Тайм: {period} • —` |
| Sticky | `position: sticky; top: 0` внутри `.tagging-input-col` |

**Не в мокапе финала:** степпер, «Последние» — явно исключены по решению продукта.

### 4. Backend helpers

`_tagging_event_subject_name()` — имя игрока или команды для чипа «Игрок».

Без `draft_step` / `recent_actions` — удалены после ревью.

## Risks / Trade-offs

| Риск | Митигация |
|------|-----------|
| Sticky-блок съедает высоту левой колонки | Компактный блок без степпера (~60px summary) |
| Full reload при каждом клике — блок мигает | Приемлемо в текущей архитектуре; HTMX out of scope |
| Session `draft_mode` рассинхрон при прямом URL | Fallback: при selected_event без mode → `edit` |

## Migration Plan

Нет миграции БД. Деплой — обновление шаблонов/CSS/backend. Откат — revert коммита.

## Open Questions

_(нет)_
