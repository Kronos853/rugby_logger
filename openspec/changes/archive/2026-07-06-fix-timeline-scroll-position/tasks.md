## 1. Scroll restore — расширение form-scroll.js

- [x] 1.1 Добавить селектор контейнера таймлайна (`.tagging-timeline-col .table-wrapper`)
- [x] 1.2 Расширить формат sessionStorage: `{ key, inputY, timelineY, timelineX? }` с обратной совместимостью для legacy `{ key, y }`
- [x] 1.3 При submit full-page форм на `body.tagging-control` сохранять scrollTop (и scrollLeft) обоих контейнеров
- [x] 1.4 При загрузке страницы восстанавливать оба scroll-позиции (двойной `requestAnimationFrame`, clamp timeline scroll)

## 2. Интеграция с tagging.js

- [x] 2.1 Убедиться, что `appScrollRestore.clear()` при отмене удаления по-прежнему сбрасывает сохранённую позицию
- [x] 2.2 Не добавлять `scrollIntoView` на `.timeline-row.selected` (избежать скачка)

## 3. Проверка

- [x] 3.1 Матч с длинным таймлайном: прокрутить в середину → клик строки → позиция сохранена после reload
- [x] 3.2 Прокрутить таймлайн → выбрать игрока/действие слева → позиция таймлайна сохранена
- [x] 3.3 Удаление события с подтверждением → позиция сохранена; при отмене confirm — сброс через clear()
