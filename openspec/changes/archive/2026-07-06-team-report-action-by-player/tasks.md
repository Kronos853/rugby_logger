## 1. Backend — данные

- [x] 1.1 Добавить `get_report_player_detail` в `repository.py` (агрегация по PlayerId / TeamId для actionId + фильтры)
- [x] 1.2 Добавить helper в `reports.py` для преобразования строк в метрики (переиспользовать `_enrich_action_row` или аналог)

## 2. Backend — маршрут

- [x] 2.1 Добавить `GET /reports/player-detail` в `app.py` (параметры как у comment-detail: actionId, subjectType=team, subjectId, dateFrom, dateTo, tournamentId, matchId)
- [x] 2.2 Валидация: только `subjectType=team`

## 3. UI

- [x] 3.1 Создать `templates/_report_player_detail.html` (колонки: Игрок/Команда + метрики)
- [x] 3.2 В `_report_results.html` — кнопка «По игрокам» и контейнер (только для team report)
- [x] 3.3 В `reports.js` — `toggleReportPlayer` по аналогии с `toggleReportComment`
- [x] 3.4 Стили подтаблицы в `app.css` (или рядом с `.report-comment-table`)

## 4. Проверка

- [x] 4.1 Командный отчёт: развернуть действие → сумма по игрокам совпадает с total строки
- [x] 4.2 Режим «по матчам»: breakdown внутри секции матча учитывает только этот матч
- [x] 4.3 Индивидуальный отчёт: кнопки «По игрокам» нет
