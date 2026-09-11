# Карты покрытия

> Документы генерируются. Не правь руками: `python tools/coverage.py`.

Всего в колоде **1182** карт.
Тренажёр: https://tsim0710.github.io/devops-anki/

| домен | jun | mid | sen | всего | подтем | статус |
|---|--:|--:|--:|--:|--:|---|
| [`k8s`](k8s-coverage.md) | 103 | 238 | 101 | **442** | 26 / 26 | закрыт |
| [`networks`](networks-coverage.md) | 54 | 90 | 66 | **210** | 20 / 20 | закрыт |
| [`terraform`](terraform-coverage.md) | 29 | 41 | 28 | **98** | 10 / 10 | закрыт |
| [`git`](git-coverage.md) | 23 | 42 | 29 | **94** | 9 / 9 | закрыт |
| [`ansible`](ansible-coverage.md) | 28 | 38 | 26 | **92** | 9 / 9 | закрыт |
| [`cicd`](cicd-coverage.md) | 22 | 39 | 30 | **91** | 10 / 10 | закрыт |
| [`linux`](linux-coverage.md) | 27 | 29 | 23 | **79** | 13 / 13 | закрыт |
| [`docker`](docker-coverage.md) | 26 | 27 | 23 | **76** | 10 / 10 | закрыт |
| `gcp` | — | — | — | — | 0 / 8 | не начат |
| `cloudflare` | — | — | — | — | 0 / 7 | не начат |
| `observability` | — | — | — | — | 0 / 8 | не начат |
| `security` | — | — | — | — | 0 / 8 | не начат |
| **итого** | 312 | 544 | 326 | **1182** | | |

---

## Как это устроено

- Цифры и таблицы считаются из `build/manifest.json`.
- Текстовая часть — `plans/notes.yaml`, по разделу на домен.
- Регенерация: `python build.py && python tools/coverage.py`.

Обновлено: 2026-09-11.
