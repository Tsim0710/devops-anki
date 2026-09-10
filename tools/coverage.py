#!/usr/bin/env python3
"""
Генерация карт покрытия: plans/<domain>-coverage.md и plans/README.md.

Цифры и таблицы берутся из build/manifest.json, текстовая часть — из
plans/notes.yaml. Смысл в том, чтобы документы нельзя было забыть обновить:
они полностью перегенерируются, а не правятся руками.

    python tools/coverage.py
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "build" / "manifest.json"
NOTES = ROOT / "plans" / "notes.yaml"
PLANS = ROOT / "plans"
SITE = "https://tsim0710.github.io/devops-anki/"
LEVELS = ("junior", "middle", "senior")


def plural(n: int, one: str, few: str, many: str) -> str:
    """Русское склонение после числительного: 1 карта, 2 карты, 5 карт."""
    if 11 <= n % 100 <= 14:
        return many
    last = n % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


def tags_of(card: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = collections.defaultdict(list)
    for tag in card["tags"]:
        if "::" in tag:
            key, value = tag.split("::", 1)
            out[key].append(value)
    return out


def load() -> tuple[dict, dict]:
    if not MANIFEST.exists():
        sys.exit("нет build/manifest.json — сначала выполни python build.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    notes = yaml.safe_load(NOTES.read_text(encoding="utf-8")) or {}
    return manifest, notes


def collect(manifest: dict) -> dict[str, dict]:
    """domain -> {subtopics: {name: Counter}, levels: Counter, sources: Counter}"""
    data: dict[str, dict] = collections.defaultdict(
        lambda: {
            "subtopics": collections.defaultdict(collections.Counter),
            "levels": collections.Counter(),
            "sources": collections.Counter(),
            "flags": collections.Counter(),
        }
    )
    for card in manifest["cards"]:
        t = tags_of(card)
        domain = card["deck"].split("::")[-1]
        d = data[domain]
        level = t["difficulty"][0]
        d["subtopics"][t["topic"][0]][level] += 1
        d["levels"][level] += 1
        for s in t["source"]:
            d["sources"][s] += 1
        if "unverified" in card["tags"]:
            d["flags"]["unverified"] += 1
        if "deprecated" in card["tags"]:
            d["flags"]["deprecated"] += 1
        if card["type"] == "mcq":
            d["flags"]["mcq"] += 1
    return data


def taxonomy() -> dict[str, list[str]]:
    return yaml.safe_load((ROOT / "taxonomy.yaml").read_text(encoding="utf-8")) or {}


def level_row(counter: collections.Counter) -> str:
    return "".join(f" {counter[l]} |" for l in LEVELS)


def domain_doc(domain: str, d: dict, note: dict, tax: list[str]) -> str:
    title = note.get("title", domain)
    total = sum(d["levels"].values())
    closed = len(d["subtopics"]) >= len(tax)

    lines = [
        f"# {domain} — карта покрытия",
        "",
        f"> Документ генерируется. Не правь руками: `python tools/coverage.py`.",
        "",
        f"**{title}.** {total} {plural(total, 'карта', 'карты', 'карт')},"
        f" {len(d['subtopics'])} {plural(len(d['subtopics']), 'подтема', 'подтемы', 'подтем')}"
        f" из {len(tax)} в `taxonomy.yaml`"
        + (" — домен закрыт." if closed else "."),
        "",
        f"Уровни: {d['levels']['junior']} junior / {d['levels']['middle']} middle"
        f" / {d['levels']['senior']} senior."
        f" Из них MCQ: {d['flags']['mcq']}."
        f" Не вычитано: {d['flags']['unverified']}.",
        "",
        f"Карты: `cards/{domain}/<subtopic>.yaml`. Тренажёр: {SITE}",
        "",
        "---",
        "",
        "## Покрытие по подтемам",
        "",
        "| подтема | jun | mid | sen | всего |",
        "|---|--:|--:|--:|--:|",
    ]
    for name in sorted(d["subtopics"]):
        c = d["subtopics"][name]
        lines.append(f"| `{name}` |{level_row(c)} **{sum(c.values())}** |")
    lines.append(f"| **итого** |{level_row(d['levels'])} **{total}** |")

    missing = [s for s in tax if s not in d["subtopics"]]
    if missing:
        lines += ["", "**Не покрыто:** " + ", ".join(f"`{s}`" for s in missing) + "."]

    lines += ["", "---", "", "## Происхождение", "", "| источник | карт |", "|---|--:|"]
    meaning = {
        "theory": "из конспектов `sources/`",
        "core": "по официальной документации",
        "interview": "формулировки реальных собесовых вопросов",
        "web": "тема из веб-подборки, ответ по докам",
    }
    for src, n in d["sources"].most_common():
        lines.append(f"| `{src}` — {meaning.get(src, '')} | {n} |")

    for key, header in (
        ("pillars", "На чём держится домен"),
        ("audit", "Что нашли аудиты"),
        ("notes", "Отдельно"),
    ):
        text = (note.get(key) or "").strip()
        if text:
            lines += ["", "---", "", f"## {header}", "", text]

    return "\n".join(lines) + "\n"


def index_doc(data: dict, notes: dict, tax: dict, manifest: dict) -> str:
    lines = [
        "# Карты покрытия",
        "",
        "> Документы генерируются. Не правь руками: `python tools/coverage.py`.",
        "",
        f"Всего в колоде **{manifest['count']}** карт.",
        f"Тренажёр: {SITE}",
        "",
        "| домен | jun | mid | sen | всего | подтем | статус |",
        "|---|--:|--:|--:|--:|--:|---|",
    ]
    totals = collections.Counter()
    for domain in sorted(tax, key=lambda d: -sum(data[d]["levels"].values()) if d in data else 1):
        d = data.get(domain)
        subs = len(tax[domain])
        if not d:
            lines.append(f"| `{domain}` | — | — | — | — | 0 / {subs} | не начат |")
            continue
        totals.update(d["levels"])
        have = len(d["subtopics"])
        status = "закрыт" if have >= subs else "в работе"
        link = f"[`{domain}`]({domain}-coverage.md)"
        lines.append(
            f"| {link} |{level_row(d['levels'])} **{sum(d['levels'].values())}**"
            f" | {have} / {subs} | {status} |"
        )
    lines.append(f"| **итого** |{level_row(totals)} **{sum(totals.values())}** | | |")
    lines += [
        "",
        "---",
        "",
        "## Как это устроено",
        "",
        "- Цифры и таблицы считаются из `build/manifest.json`.",
        "- Текстовая часть — `plans/notes.yaml`, по разделу на домен.",
        "- Регенерация: `python build.py && python tools/coverage.py`.",
        "",
        f"Обновлено: {dt.date.today().isoformat()}.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    manifest, notes = load()
    data = collect(manifest)
    tax = taxonomy()

    written = []
    for domain in sorted(data):
        path = PLANS / f"{domain}-coverage.md"
        path.write_text(
            domain_doc(domain, data[domain], notes.get(domain, {}), tax.get(domain, [])),
            encoding="utf-8",
        )
        written.append(path.name)

    (PLANS / "README.md").write_text(index_doc(data, notes, tax, manifest), encoding="utf-8")
    written.append("README.md")

    missing_notes = [d for d in data if d not in notes]
    if missing_notes:
        print("WARN  нет раздела в plans/notes.yaml:", ", ".join(missing_notes), file=sys.stderr)

    print(f"OK: {len(written)} документов в plans/ ({manifest['count']} карт)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
