## Why

На пульте разметки оператор не видит явного статуса «что сейчас кодирую»: кнопки шагов приглушены, серая подсказка «Сначала зафиксируйте время…» не даёт контекста черновика. Lazyweb-вариант **«Текущий Черновик»** ([отчёт](https://www.lazyweb.com/report/lazyweb/9c22676f-495d-4ece-b8fd-6446c8516817/?source=create), мокап: `mockup-current-event-draft.png`) предлагает липкий блок **ТЕКУЩЕЕ СОБЫТИЕ** с режимом, резюме полей и таймом — меньше ошибок при выборе игрока/действия.

После ревью отклонены элементы того же отчёта: полоса повтора, степпер 1→4, ряд «Последние» действий (занимал место).

## What Changes

- **Добавить** липкий блок «ТЕКУЩЕЕ СОБЫТИЕ» над шагами ввода (левая колонка)
- **Бейдж режима:** `НОВОЕ` после capture, `РЕДАКТИРОВАНИЕ` при выборе строки таймлайна
- **Резюме:** чипы `[Игрок: …]`, `[Действие: …]`, `[Результат: …]` + `Тайм: {период} • {время}`
- **Убрать** серую status-bar «Сначала зафиксируйте время…»
- **Session:** `draft_mode_{match_id}` = `new` | `edit` (capture vs timeline select)
- **Не внедрять:** степпер подсказок, ряд «Последние», полосу повтора

## Capabilities

### New Capabilities

_(нет)_

### Modified Capabilities

- `video-tagging`: requirement «Current Event Draft Panel» — явный блок черновика на пульте

## Impact

- `templates/tagging/_current_event_draft.html` — новый partial
- `templates/tagging/control.html` — include draft-блока, удаление status-bar
- `static/tagging.css` — стили `.current-event-draft`
- `backend/app.py` — контекст draft labels, `draft_mode` в session
- `tests/test_tagging_draft.py` — изолированные тесты
- `docs/development-context.md`, `openspec/specs/video-tagging/spec.md`
