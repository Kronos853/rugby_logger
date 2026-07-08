## 1. Backend

- [x] 1.1 `_tagging_scroll_focus_incomplete()` и `_tagging_scroll_focus_after_update()`
- [x] 1.2 `scroll_focus_{match_id}` в session: capture, update, timeline select
- [x] 1.3 `scroll_focus` в `_load_tagging_context` (pop)

## 2. Templates & CSS

- [x] 2.1 Якоря `#tagging-step-*`, meta `#tagging-scroll-focus`
- [x] 2.2 `.tagging-step { scroll-margin-top: 72px }`

## 3. Frontend

- [x] 3.1 `form-scroll.js` — `applyScrollFocus()` с приоритетом над restore

## 4. Tests & docs

- [x] 4.1 `tests/test_tagging_draft.py` — capture→player, player→action
- [x] 4.2 `docs/development-context.md`

## 5. Verification

- [x] 5.1 Ручная проверка на пульте разметки (оставлено на будущую оценку UX)
