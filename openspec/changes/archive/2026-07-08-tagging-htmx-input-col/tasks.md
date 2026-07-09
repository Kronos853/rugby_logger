## 1. Templates — partials и разметка

- [x] 1.1 Создать `templates/tagging/_tagging_input_col.html` — вынести содержимое левой колонки из `control.html` (draft, шаги 1–3, meta)
- [x] 1.2 Создать `templates/tagging/_tagging_timeline_col.html` — счёт (`_score.html`) + `_timeline.html`
- [x] 1.3 Создать `templates/tagging/_htmx_swap.html` — primary body (input col) + OOB `#tagging-timeline-col`
- [x] 1.4 Обновить `control.html`: подключить HTMX CDN, обёртки `#tagging-input-col` / `#tagging-timeline-col`, include partials
- [x] 1.5 Добавить `hx-post` / `hx-target="#tagging-input-col"` / `hx-swap="innerHTML"` на все формы ввода, capture, period selector, timeline select/delete

## 2. Backend

- [x] 2.1 Переименовать/расширить `_render_tagging_partials()` → рендер `_htmx_swap.html` с полным tagging context
- [x] 2.2 Убедиться, что все tagging POST routes (`capture`, `update`, `select`, `delete`, `set-period`) возвращают HTMX-ответ при `HX-Request`
- [x] 2.3 Добавить HTMX-ветку для `tagging_set_period` (сейчас только redirect)

## 3. JavaScript

- [x] 3.1 Рефакторинг `tagging.js`: вынести `initTaggingTimeline()` (row click, delete confirm, selected-event-meta seek)
- [x] 3.2 Подписаться на `htmx:afterSwap` для re-init timeline handlers
- [x] 3.3 Обновить `form-scroll.js`: `htmx:beforeRequest` / `afterSwap` — save/restore scroll input col + timeline; scroll-focus после swap

## 4. Tests

- [x] 4.1 Тест: `tagging_capture` с `HX-Request` → 200, HTML содержит input col и timeline OOB
- [x] 4.2 Тест: `tagging_update_event` (player) с `HX-Request` → selection state в ответе (`.selected` / draft chips)
- [x] 4.3 Тест: POST без `HX-Request` → redirect (fallback)
- [x] 4.4 Тест: `tagging_set_period` с `HX-Request` → partial без redirect

## 5. Docs и ручная проверка

- [x] 5.1 Обновить `docs/development-context.md` — tagging использует HTMX partial swap
- [x] 5.2 Smoke: capture → player → action → outcome → comment без full reload; timeline select + delete; period switch; video seek
