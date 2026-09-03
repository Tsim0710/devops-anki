# devops-anki

Колода Anki для подготовки к DevOps-собесам. Источник правды — YAML в `cards/`,
сборка `.apkg` автоматическая через GitHub Actions.

Спецификация проекта — [`CLAUDE.md`](CLAUDE.md). Она же инструкция для Claude Code.

---

## Как устроено

| Что | Где |
|---|---|
| Карты | `cards/<domain>.yaml` |
| Разрешённые subtopic | `taxonomy.yaml` |
| Форма карты | `schema.json` |
| Реестр id (append-only) | `ids.lock` |
| Снапшоты конспектов | `sources/` |
| Сборка | `build.py` |

**Дек = `DevOps::<domain>`** (12 штук). Вся остальная навигация — теги:
`topic::<subtopic>`, `difficulty::junior|middle|senior`, `source::theory|interview|web`,
`situational`, `unverified`, `deprecated`.

Деки не дробятся до subtopic сознательно: импорт `.apkg` не переносит уже существующие
карты в другой дек, поэтому дек-на-тему означал бы, что любое переименование темы
навсегда оставляет карту в старом деке.

---

## Локально

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python build.py --validate
```

```bash
.venv/bin/python build.py
```

```bash
.venv/bin/python -m pytest tests/ -q
```

Индекс существующих карт (читать **перед** генерацией новой темы, чтобы не плодить дубли):

```bash
.venv/bin/python build.py --index k8s
```

---

## Как попадает на телефон

1. Пушнул тег `vN` → CI собирает и кладёт `devops.apkg` в релиз.
   На обычный push колода собирается в artifact (проверить, что не сломалось).
2. **Синк AnkiWeb.**
3. Импорт `.apkg`.
4. **Синк AnkiWeb ещё раз.**

Пункты 2 и 4 не опциональны: импорт на несинхронизированной коллекции даёт
«one-way sync required» и теряет то, что накопилось на другой стороне.

```bash
git tag v1 && git push origin v1
```

## Как учить

Тема и уровень задаются filtered deck (Tools → Create Filtered Deck):

```
deck:DevOps::k8s tag:topic::probes tag:difficulty::middle -tag:deprecated
```

```
deck:DevOps::networks tag:difficulty::junior -tag:deprecated
```

```
tag:situational -tag:deprecated
```

**Рычаг перегрузки.** Если повторений становится слишком много — в браузере карт
выбрать `tag:difficulty::senior` → Suspend. Колода сжимается почти вдвое, прогресс
не теряется, перед собесом возвращается. Саспенд переживает импорт, но **новые карты
приезжают активными** — после крупной генерации пересаспендить.

---

## Правила, которые легко нарушить

- `id` карты **вечен**. Из него считается GUID заметки — единственное, что связывает
  карту в репо с историей повторений на телефоне. Сменил `id` → потерял прогресс.
  Переехала тема — меняется поле `subtopic`, `id` остаётся старым.
- **Удаления через YAML не существует.** `.apkg` аддитивен: убранная из YAML карта
  остаётся на телефоне навсегда. Вывод из оборота — `deprecated: true`, потом ручная
  чистка `tag:deprecated` в Anki.
- Многострочные поля — только `|`. `>` склеивает строки и ломает отступы в коде.
- `verified: false` по умолчанию. Флаг снимает только человек, после вычитки.
