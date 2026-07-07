## Context

Пульт разметки (`templates/tagging/control.html`) использует двухколоночный layout: слева — ввод (игроки, действия), справа — таймлайн событий. Таймлайн рендерится в `#timeline-panel` → `.table-wrapper` с `overflow: auto`; события отсортированы «свежие сверху» (`events|reverse`).

Выбор строки таймлайна отправляет POST `tagging_select_event` через пустую форму `.timeline-select-form` (full-page submit + redirect). Аналогично — удаление события и обновление полей слева.

`static/form-scroll.js` уже сохраняет `scrollTop` левой колонки (`.tagging-input-col`) в `sessionStorage` перед submit и восстанавливает после reload. Прокрутка таймлайна не сохраняется — после reload `.table-wrapper` возвращается к `scrollTop = 0`, что визуально выглядит как «перескок» к верхней (самой свежей) части списка.

## Goals / Non-Goals

**Goals:**

- Сохранять вертикальную позицию прокрутки таймлайна при любом full-page POST с пульта разметки
- Восстанавливать позицию до отрисовки (или сразу после) без заметного мерцания
- Не ломать существующее восстановление прокрутки левой колонки

**Non-Goals:**

- Переход таймлайна на HTMX/partial swap (отдельная задача)
- Горизонтальная прокрутка (сохраняется браузером вместе с `scrollLeft`, если записывать оба значения)
- Автоскролл к выбранной строке при первом открытии матча

## Decisions

### 1. Расширить `form-scroll.js`, а не писать отдельный модуль

**Решение:** Добавить в существующий scroll-restore второй контейнер — `.tagging-timeline-col .table-wrapper` (или `#timeline-panel .table-wrapper`).

**Почему:** Один механизм для всех full-page форм на странице; `control.html` уже подключает `form-scroll.js`. Альтернатива — логика только в `tagging.js`, но тогда дублирование sessionStorage и двойные слушатели submit.

### 2. Формат sessionStorage

**Решение:** Расширить JSON: `{ key, inputY, timelineY }` (обратная совместимость: если только `y` — трактовать как `inputY`).

**Почему:** Два независимых scroll-контейнера требуют двух координат. Отдельные ключи (`app-scroll-restore` / `app-timeline-scroll`) усложняют атомарность пары при одном submit.

### 3. Когда сохранять

**Решение:** На `submit` любой формы с full-page POST на странице `body.tagging-control` — сохранять оба scrollTop (input + timeline), как сейчас для input.

**Почему:** Пользователь может прокрутить таймлайн, затем нажать кнопку игрока слева — позиция таймлайна тоже должна сохраниться. Ограничение только таймлайн-формами было бы неполным.

### 4. Восстановление

**Решение:** `requestAnimationFrame` × 2 (как сейчас для input) для обоих контейнеров после `DOMContentLoaded`.

**Альтернатива отвергнута:** `scrollIntoView` на `.timeline-row.selected` — как раз вызывает нежелательный скачок, если строка далеко от текущей позиции.

## Risks / Trade-offs

- **[Risk] Контейнер не найден** → Mitigation: optional chaining; если нет `.table-wrapper`, сохранять только input
- **[Risk] Мерцание при restore** → Mitigation: двойной rAF уже используется; при жалобах — `overflow: hidden` на wrapper до restore
- **[Risk] Устаревший scroll после удаления строк** → Mitigation: clamp `scrollTop` к `scrollHeight - clientHeight` при restore

## Migration Plan

1. Изменить `form-scroll.js`
2. Ручная проверка на матче с 50+ событиями: прокрутка в середину → клик строки → позиция сохранена
3. Откат: revert одного файла

## Open Questions

- Нужно ли сохранять `scrollLeft` для горизонтальной прокрутки широкой таблицы? (рекомендация: да, записывать `timelineX` заодно — низкая стоимость)
