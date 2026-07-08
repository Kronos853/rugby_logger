## 1. Backend

- [x] 1.1 В `get_report_player_detail`: `ORDER BY Total DESC, SubjectLabel ASC` вместо `ORDER BY SubjectLabel`

## 2. Tests

- [x] 2.1 Расширить `tests/test_reports_split.py`: два игрока с разным total — в HTML первым идёт игрок с большим count
- [x] 2.2 При равном total — порядок по имени (опционально, если легко засеять)

## 3. Docs

- [x] 3.1 При архивации — sync `openspec/specs/reporting/spec.md`

## 4. Verification

- [x] 4.1 `python -m unittest tests.test_reports_split -v`
