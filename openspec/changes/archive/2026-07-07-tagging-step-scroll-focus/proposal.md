## Why

После каждого шага разметки (capture → игрок → действие → итог → комментарий) левая колонка длинная, а `form-scroll.js` восстанавливал прежнюю позицию скролла — оператору приходилось крутить панель вручную. Нужен автоматический переход к следующему незаполненному шагу без UI-степпера (отклонён ранее).

## What Changes

- **Session `scroll_focus_{match_id}`** — цель после workflow POST: `player` | `action` | `outcome` | `comment`
- **Якоря** `#tagging-step-player`, `#tagging-step-action`, `#tagging-step-outcome`, `#tagging-step-comment`
- **`form-scroll.js`** — scroll-focus имеет приоритет над restore из sessionStorage
- **Правила:** capture → player; player → action; action → outcome (если `HasOutcome`) или comment; outcome → comment; comment save — без фокуса; timeline select — фокус только на первое незаполненное поле

## Capabilities

### New Capabilities

_(нет)_

### Modified Capabilities

- `video-tagging`: requirement «Tagging Step Scroll Focus»

## Impact

- `backend/app.py` — `_tagging_scroll_focus_*`, session на capture/update/select
- `templates/tagging/control.html` — якоря, `#tagging-scroll-focus`
- `static/form-scroll.js`, `static/tagging.css`
- `tests/test_tagging_draft.py` — тесты focus meta
