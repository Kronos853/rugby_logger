## 1. Toolbar

- [x] 1.1 Добавить `.tagging-toolbar` — одна горизонтальная полоса: счёт, матч, тайм, время видео, кнопка «Новое событие»
- [x] 1.2 Создать `<details>`-dropdown «⋮ Меню»: «Открыть видео», «Экспорт CSV», форма импорта CSV (file input + radio), «← Подготовка»
- [x] 1.3 Перенести flash-сообщения в toolbar (убрать отдельную card-секцию)

## 2. Viewport layout

- [x] 2.1 `.tagging-page`: `height: 100vh; display: flex; flex-direction: column; overflow: hidden`
- [x] 2.2 `.tagging-workspace`: `flex: 1; min-height: 0; display: flex; flex-direction: row; gap: 10px`
- [x] 2.3 Удалить `.tagging-sidebar` и его содержимое из `control.html`

## 3. Левая колонка (ввод)

- [x] 3.1 `.tagging-input-col`: `flex: 0 0 45%; overflow-y: auto; display: flex; flex-direction: column; gap: 10px`
- [x] 3.2 Переставить блоки в порядке: Игроки → Действия → Outcome → Комментарий
- [x] 3.3 Игроки: увеличить до 4–5 колонок, уменьшить padding кнопок (`padding: 5px 2px; font-size: 11px`)
- [x] 3.4 Действия: увеличить сетку до 5 колонок

## 4. Правая колонка (таймлайн)

- [x] 4.1 `.tagging-timeline-col`: `flex: 1; display: flex; flex-direction: column; min-height: 0`
- [x] 4.2 `.table-wrapper`: `overflow: auto; flex: 1` (горизонтальный + вертикальный scroll)
- [x] 4.3 `events-table`: добавить `min-width: 900px; white-space: nowrap`
- [x] 4.4 Длинные комментарии в td: `max-width: 180px; overflow: hidden; text-overflow: ellipsis` + `title="{{ ev.Comment }}"`

## 5. Компактные комментарии

- [x] 5.1 `.grid-comments`: заменить `flex-wrap: wrap` на `overflow-x: auto; white-space: nowrap; flex-wrap: nowrap`
- [x] 5.2 Пресеты-кнопки: `display: inline-block` (не grow)

## 6. form-scroll.js

- [x] 6.1 Обновить `form-scroll.js` — сохранять/восстанавливать `scrollTop` у `.tagging-input-col` вместо `window.scrollY`

## 7. Breakpoint

- [x] 7.1 `@media (max-width: 1199px)`: `.tagging-workspace { flex-direction: column }`, `.tagging-timeline-col { max-height: 40vh }`, `.tagging-input-col { flex: 1 }`

## 8. Верификация

- [x] 8.1 Открыть пульт на 1366×768 — таймлайн и зона ввода одновременно на экране
- [x] 8.2 Зафиксировать событие → таймлайн обновился без прокрутки страницы
- [x] 8.3 Провести горизонтальный scroll таймлайна — все колонки доступны, sticky header держится
- [x] 8.4 Проверить dropdown «⋮»: открытие видео, экспорт/импорт CSV, переход назад
- [x] 8.5 Breakpoint: уменьшить окно до <1200px — проверить stackable layout
