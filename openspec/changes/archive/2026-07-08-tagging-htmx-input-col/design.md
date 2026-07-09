## Context

Пульт разметки (`templates/tagging/control.html`) — standalone-страница без `base.html`, HTMX не подключён. Все формы левой колонки и toolbar делают POST → redirect → full HTML reload.

Backend (`backend/app.py`) уже содержит ветки `HX-Request` для `tagging_capture`, `tagging_update_event`, `tagging_select_event`, `tagging_delete_event`, `tagging_import_csv` и функцию `_render_tagging_partials()`. Текущий partial (`_htmx_refresh.html`) возвращает только score + timeline — **без левой колонки (selection state)**.

Спека `video-tagging` требует HTMX для incremental updates; реализация отстаёт после change'ей `tagging-current-draft` и `tagging-step-scroll-focus` (full POST + session scroll).

Стек: Flask + Jinja + HTMX (CDN на других страницах), `tagging.js` (BroadcastChannel, timeline click), `form-scroll.js` (scroll restore).

## Goals / Non-Goals

**Goals:**
- Убрать full page reload при кликах в левой колонке ввода и при «НОВОЕ СОБЫТИЕ»
- Обновлять selection state (`.selected`, черновик, условные блоки outcome/comment) без мигания
- Синхронно обновлять правую колонку (счёт + таймлайн) в том же HTMX-ответе
- Сохранить scroll-focus, scroll restore, timeline row click, delete confirm, video seek
- Toolbar (видео-время, nav) не перерисовывается

**Non-Goals:**
- HTMX на импорт CSV (flash в toolbar — full reload)
- Alpine.js / optimistic UI
- HTMX на видео-странице
- Переход всего приложения на единый `base.html` для tagging
- `hx-indicator` / debounce (можно позже)

## Decisions

### 1. OOB swap: левая + правая колонки

**Решение:** формы с `hx-post` и `hx-target="#tagging-input-col"`; ответ сервера содержит два фрагмента с `hx-swap-oob="innerHTML"`:
- `#tagging-input-col` — draft + шаги 1–3 + meta (`scroll-focus`, `selected-event-meta`)
- `#tagging-timeline-col` — счёт + `_timeline.html`

**Почему:** пользовательская боль — левая колонка; правая должна оставаться актуальной. OOB — один round-trip, toolbar не трогаем.

**Альтернатива:** swap `#tagging-workspace` целиком — проще шаблон, но менее явное разделение; принята OOB для соответствия формулировке «input col primary».

### 2. Новый partial `_tagging_input_col.html`

**Решение:** вынести содержимое `.tagging-input-col` из `control.html` в partial; использовать в full page и в HTMX-ответе.

**Почему:** DRY, один источник для selection state.

### 3. Унификация счёта

**Решение:** правая колонка всегда рендерит через `_score.html` + `_timeline.html`; убрать дублирующую inline-разметку счёта из `control.html`.

**Почему:** сейчас partial и full page расходятся (`tagging-timeline-score` vs `#score-panel.card`).

### 4. HTMX CDN на control.html

**Решение:** `<script src="https://unpkg.com/htmx.org@1.9.12">` в `<head>` control.html (та же версия, что в `base.html`).

### 5. Атрибуты на формах

**Решение:** на все формы в `_tagging_input_col.html` + `#capture-form` + `half-selector` (тайм):
```html
hx-post="{{ url_for(...) }}"
hx-target="#tagging-input-col"
hx-swap="innerHTML"
```
Формы timeline select/delete — тот же паттерн (клик по строке сабмитит hidden form).

**Почему:** единый target; сервер всегда отдаёт полный input col + OOB timeline col.

### 6. `_render_tagging_partials()` → `_render_tagging_htmx_response()`

**Решение:** рендерить шаблон `tagging/_htmx_swap.html`:
```jinja
<div id="tagging-input-col" hx-swap-oob="innerHTML">{% include input col %}</div>
<div id="tagging-timeline-col" hx-swap-oob="innerHTML">{% include score + timeline %}</div>
<div id="tagging-input-col">{% include input col %}</div>  {# primary swap body #}
```

HTMX: primary response идёт в `hx-target`; OOB элементы обновляют вторую колонку.

**Примечание:** при `hx-target="#tagging-input-col"` основной ответ — содержимое input col (без обёртки id) ИЛИ полный элемент с id — проверить по документации HTMX: для `innerHTML` target получает innerHTML ответа. OOB — отдельные элементы с id.

Стандартный паттерн:
- Response body: inner content for target
- OOB: `<div id="tagging-timeline-col" hx-swap-oob="innerHTML">...</div>`

### 7. `tagging.js` re-init

**Решение:** слушатель `document.body.addEventListener("htmx:afterSwap", ...)` вызывает `initTaggingTimeline()` (row click, delete confirm, selected-event-meta seek). Вынести инициализацию в именованные функции.

### 8. `form-scroll.js` и HTMX

**Решение:**
- `htmx:beforeRequest` на tagging-control: сохранить `scrollTop` input col и timeline wrapper в замыкание/module state
- `htmx:afterSwap`: если есть `#tagging-scroll-focus` → `applyScrollFocus()`; иначе восстановить сохранённые позиции
- Формы с `hx-post` уже не триггерят `saveScrollPosition` на submit (существующая логика)

### 9. Fallback redirect

**Решение:** без `HX-Request` — поведение как сейчас (redirect). Тесты и прямой POST без JS остаются рабочими.

## Risks / Trade-offs

| Риск | Митигация |
|------|-----------|
| Двойной OOB + primary — ошибка в шаблоне ломает swap | Интеграционный test с `HX-Request`; smoke на capture → player → action |
| Timeline listeners не переинициализируются | `htmx:afterSwap` в `tagging.js` |
| Scroll сбрасывается при swap input col | `beforeRequest`/`afterSwap` save-restore; scroll-focus приоритетнее |
| Комментарий: фокус в input при swap | Приемлемо; full reload тоже сбрасывал |
| `set-period` меняет период выбранного события | Включить в HTMX; обновлять draft time в partial |
| Импорт CSV без HTMX — таймлайн устареет до reload | Оставить full reload по design |

## Migration Plan

1. Добавить partials и HTMX-шаблон ответа
2. Подключить HTMX + атрибуты на формах
3. Обновить JS scroll/listeners
4. Тесты `HX-Request`
5. Ручная проверка: capture → player → action → outcome → comment; timeline select; delete; period switch; video seek после select

Rollback: убрать `hx-*` атрибуты и CDN — revert к redirect-only.

## Open Questions

- Нужен ли `hx-disabled-elt="button"` на формах ввода для защиты от double-click при медленном SQLite? (отложить)
- Переключатель тайма: обновлять только draft block или весь input col? → весь input col (проще, единый partial)
