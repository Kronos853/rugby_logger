## 1. Backend

- [x] 1.1 Добавить `GET /reports/player-panel` с режимами `empty` и `action-breakdown` (reuse `build_player_detail`)
- [x] 1.2 Пробрасывать фильтры: `teamId`, `dateFrom`, `dateTo`, `tournamentId`, `matchId` (optional)
- [x] 1.3 Перенаправить или заменить `/reports/player-detail` на panel endpoint в JS

## 2. Templates — layout

- [x] 2.1 В `reports.html`: при `report_type == 'team'` и `generated` — `.report-split`; при `individual` — один столбец как сейчас
- [x] 2.2 Сохранить «Тип отчёта», переключение команда/игрок, все фильтры
- [x] 2.3 Правая колонка `#report-player-panel` с placeholder «Выберите действие»

## 3. Templates — partials

- [x] 3.1 Создать `_report_player_panel.html` (placeholder + action breakdown с заголовком действия)
- [x] 3.2 Обновить `_report_results.html`: «По игрокам» (team only) → HTMX в панель; убрать inline player `<div>`
- [x] 3.3 `_report_player_detail.html` — строки игроков без ссылок на individual report

## 4. Frontend (JS + CSS)

- [x] 4.1 `reports.js`: active row для выбранного действия; toggle «По игрокам»; сброс панели при submit; `initReportFormFields` без изменений
- [x] 4.2 `app.css`: split-view, placeholder, active row — сверка с мокапом (team mode)

## 5. Specs & docs

- [x] 5.1 Визуальная приёмка team mode vs `mockup-team-player-split.png`
- [x] 5.2 Обновить `docs/development-context.md`

## 6. Verification

- [x] 6.1 test_client: team POST → split + placeholder
- [x] 6.2 test_client: individual POST → без split, как раньше
- [x] 6.3 test_client: `player-panel?mode=action-breakdown` → 200, таблица игроков (in-memory DB, `TEST_`)
