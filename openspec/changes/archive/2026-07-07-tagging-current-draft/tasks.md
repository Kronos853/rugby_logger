## 1. Backend

- [x] 1.1 Хелпер `_tagging_event_subject_name()` для чипа игрока/команды
- [x] 1.2 Расширить `_load_tagging_context`: `draft_mode`, `draft_*_label`, `selected_action`
- [x] 1.3 Session `draft_mode_{match_id}`: `new` на capture, `edit` на timeline select, clear на delete

## 2. Templates

- [x] 2.1 Создать `templates/tagging/_current_event_draft.html` по мокапу
- [x] 2.2 `control.html`: include draft-блока, убрать status-bar
- [x] 2.3 Убрать степпер 1→4 и ряд «Последние» (ревью после первой итерации)

## 3. CSS

- [x] 3.1 `tagging.css`: `.current-event-draft`, chips, badges, sticky

## 4. Tests & docs

- [x] 4.1 `tests/test_tagging_draft.py` — draft block, badges, без степпера/«Последних» (in-memory DB, `TEST_`)
- [x] 4.2 `docs/development-context.md`
- [x] 4.3 Delta spec `specs/video-tagging/spec.md` в change; main spec синхронизирован

## 5. Verification

- [x] 5.1 Визуальная сверка с `mockup-current-event-draft.png` (без степпера)
- [x] 5.2 `python -m unittest tests.test_tagging_draft -v`
