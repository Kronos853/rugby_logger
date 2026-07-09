## Why

Каждый клик на пульте разметки (игрок, действие, outcome, комментарий, «НОВОЕ СОБЫТИЕ») вызывает full POST + redirect и перерисовку всей страницы. Левая колонка ввода мигает, скачет скролл, условные блоки (outcome, комментарий) появляются с задержкой. Backend уже отдаёт HTMX-partials для tagging, но `control.html` не подключён к HTMX — спека `video-tagging` (Server-Side Event Draft) фактически не выполняется.

## What Changes

- Подключить HTMX на странице `tagging/control.html`
- Добавить `hx-post` на формы левой колонки ввода и форму «НОВОЕ СОБЫТИЕ» в toolbar
- Расширить partial-ответ сервера: левая колонка (черновик, шаги 1–3, selection state) + правая колонка (счёт, таймлайн) в одном ответе через OOB swap
- Переинициализация `tagging.js` и сохранение scroll после HTMX swap
- Унифицировать разметку счёта между full page и partial
- Переключатель тайма в toolbar — HTMX (без full reload)
- Импорт CSV и навигационные ссылки — остаются full page (flash, file upload)

## Capabilities

### New Capabilities

_(нет — поведение уже описано в main spec)_

### Modified Capabilities

- `video-tagging`: уточнить и зафиксировать HTMX partial-update для левой колонки ввода (selection state) и синхронное обновление timeline/score; scroll-focus после capture через partial

## Impact

- `templates/tagging/control.html` — HTMX CDN, `hx-*` на формах, обёртки с id для swap
- `templates/tagging/_htmx_refresh.html` — расширить или заменить на workspace/input partials
- Новые partials: `_tagging_input_col.html`, возможно `_tagging_timeline_col.html`
- `backend/app.py` — `_render_tagging_partials()` возвращает полный фрагмент (input + timeline OOB)
- `static/tagging.js` — `htmx:afterSwap` re-init (timeline click, delete confirm, video seek meta)
- `static/form-scroll.js` — scroll save/restore при HTMX на tagging (input col + timeline table)
- `static/tagging.css` — при необходимости выровнять разметку счёта
- `tests/` — Flask test_client с заголовком `HX-Request: true`
