## Why

В командном отчёте разбивка «По игрокам» сейчас раскрывается inline под строкой действия — при длинном отчёте это теряется в скролле. Lazyweb-вариант **«Связка Команда+Игрок»** ([отчёт](https://www.lazyweb.com/report/lazyweb/bcb6e9aa-f0ef-4407-a524-8cbe50a37c92/?source=create), мокап: `mockup-team-player-split.png`) предлагает вынести разбивку в правую панель рядом с командным отчётом. Полный индивидуальный отчёт остаётся отдельным режимом формы — в панели показывается только расшифровка выбранного действия по игрокам.

## What Changes

- **Двухколоночный layout** только для **командного** отчёта: слева «Отчёт команды» (~65%), справа «Панель игрока» (~35%)
- **Перенести drill-down «По игрокам»** из inline-подтаблицы в **правую панель** (HTMX)
- **Правая панель** — только разбивка по игрокам для выбранного действия; строки игроков **не** ведут к полному индивидуальному отчёту
- **Сохранить** dropdown «Тип отчёта» (Командный / Индивидуальный) и существующий режим индивидуального отчёта (одна колонка, без split)
- **Сохранить** кнопку «Комментарии» inline слева; фильтры (период, турнир, «В разрезе матчей»)
- **Плейсхолдер** правой панели: «Выберите действие» (не «…или игрока»)
- **Визуальная спецификация** split-layout — мокап Lazyweb; отклонение: тип отчёта и индивидуальный режим остаются по решению продукта

## Capabilities

### New Capabilities

_(нет)_

### Modified Capabilities

- `reporting`: split-view и панель разбивки по действию в командном отчёте; индивидуальный отчёт без изменений

## Impact

- `templates/reports.html` — split только при `report_type=team` и `generated`; individual — как сейчас
- `templates/_report_results.html` — «По игрокам» → правая панель (team only)
- `templates/_report_player_panel.html` — новый partial (placeholder + action breakdown)
- `static/reports.js` — active row; сброс панели при submit; `initReportFormFields` без изменений
- `static/app.css` — стили split-layout
- `backend/app.py` — `GET /reports/player-panel` (`empty`, `action-breakdown`); `/reports/player-detail` → панель или alias
- `openspec/specs/reporting/spec.md` — delta при архивации
