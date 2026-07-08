## Context

Пульт разметки: full POST + redirect на каждый клик. Левая колонка `.tagging-input-col` с `overflow-y: auto`. Блок «ТЕКУЩЕЕ СОБЫТИЕ» — sticky сверху. `form-scroll.js` сохраняет scroll при submit и восстанавливает после reload.

## Goals / Non-Goals

**Goals:**

- После capture/update вести взгляд к следующему шагу без ручного скролла
- Не ломать restore позиции таймлайна при выборе готового события
- Минимальный diff (без HTMX)

**Non-Goals:**

- Степпер UI, hotkeys, HTMX partials
- Smooth-scroll анимации
- Фокус после сохранения комментария

## Decisions

### 1. Server-driven focus через session

POST handler выставляет `session[f"scroll_focus_{match_id}"]`, GET `_load_tagging_context` делает `pop` и передаёт в шаблон `scroll_focus`. Одноразовый сигнал — не засоряет URL.

### 2. Приоритет focus над restore

`form-scroll.js`: при наличии `#tagging-scroll-focus[data-target]` скроллит `.tagging-input-col` к `offsetTop` шага; иначе — прежний restore input + timeline.

### 3. Логика целей

| Триггер | `scroll_focus` |
|---------|----------------|
| `/capture` | `player` |
| update `subjectType` | `action` |
| update `actionId` + HasOutcome | `outcome` |
| update `actionId` без outcome | `comment` |
| update `outcome` | `comment` |
| update `comment` | _(нет)_ |
| timeline select | первое незаполненное или _(нет)_ |

### 4. CSS

`.tagging-step { scroll-margin-top: 72px }` — учёт sticky draft (запас под будущий `scrollIntoView`).

## Risks / Trade-offs

| Риск | Митигация |
|------|-----------|
| `offsetTop` до layout | double `requestAnimationFrame` |
| Outcome-блок ещё не в DOM | focus `outcome` только после action с HasOutcome (блок рендерится) |
| Пользователю не нравится | откат изолирован в 4 файлах |

## Migration Plan

Нет. Деплой — шаблоны/JS/backend.

## Open Questions

- Нужен ли smooth scroll или подсветка активной карточки — отложено («посмотрим в будущем»)
