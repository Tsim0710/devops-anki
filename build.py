#!/usr/bin/env python3
"""
cards/**/*.yaml -> build/devops.apkg

Инварианты, на которых держится пайплайн (см. CLAUDE.md):
  * GUID заметки считается ТОЛЬКО из card["id"] -> правка текста не плодит дубли,
    смена id обнуляет историю повторений.
  * model_id / deck_id детерминированы из имени -> импорт не создаёт новые notetype и деки.
  * Дек = DevOps::<domain>. Вся остальная навигация — теги.
Режимы:
  python build.py                 сборка build/devops.apkg + build/drill.html + manifest
  python build.py --validate      только валидация (для CI)
  python build.py --index [dom]   индекс существующих карт (читать ПЕРЕД генерацией темы)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import genanki
import jsonschema
import markdown
import yaml

ROOT = Path(__file__).parent
CARDS_DIR = ROOT / "cards"
BUILD_DIR = ROOT / "build"
LOCK_PATH = ROOT / "ids.lock"

DECK_ROOT = "DevOps"
BASIC_MODEL_NAME = "DevOps Anki — Basic"
MCQ_MODEL_NAME = "DevOps Anki — MCQ"

# Бюджет карт (CLAUDE.md, раздел 5). Превышение — warning, не fail.
MAX_PER_SUBTOPIC = 25
MAX_PER_DOMAIN = 400
MAX_TOTAL = 1500
SIMILARITY_WARN = 0.85


# --------------------------------------------------------------------------- ids

def stable_id(kind: str, name: str) -> int:
    """Детерминированный id модели/дека. НИКОГДА не random: случайный id на каждой
    сборке создаёт новый notetype и новый дек при каждом импорте."""
    h = hashlib.sha1(f"{kind}:{name}".encode()).hexdigest()
    return (int(h, 16) % (1 << 30)) + (1 << 30)


# ---------------------------------------------------------------------- rendering

_CODE_RE = re.compile(r"(```.*?```|``.+?``|`[^`\n]+`)", re.DOTALL)


def _escape_outside_code(text: str) -> str:
    """Экранирует HTML в прозе, не трогая код: внутри code-регионов это сделает
    сам markdown. Без этого `<pending>` или `A && B` из конспекта исчезают с карты."""
    parts = _CODE_RE.split(text)
    return "".join(p if i % 2 else html.escape(p, quote=False) for i, p in enumerate(parts))


def render(text: str) -> str:
    """Markdown -> HTML. Поля Anki это HTML: без этого переносы схлопываются,
    а списки и блоки кода приезжают сырым текстом."""
    if not text:
        return ""
    md = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists"])
    return md.convert(_escape_outside_code(text.strip()))


# ------------------------------------------------------------------------- models

CSS = """
.card {
  font-family: -apple-system, "Helvetica Neue", sans-serif;
  font-size: 19px; line-height: 1.5;
  text-align: left; color: #1a1a1a; background: #fdfdfd;
  padding: 4px 2px;
}
.nightMode.card, .card.nightMode { color: #e8e8e8; background: #2a2a2a; }

code, pre {
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.85em;
}
code { background: #f0f0f2; padding: 1px 5px; border-radius: 4px; }
pre {
  background: #f4f4f6; padding: 10px 12px; border-radius: 6px;
  border-left: 3px solid #c8c8d0;
  white-space: pre-wrap; word-wrap: break-word; overflow-x: auto;
}
pre code { background: none; padding: 0; }
.nightMode code { background: #3a3a40; }
.nightMode pre { background: #1e1e22; border-left-color: #4a4a55; }

hr#answer { border: none; border-top: 2px solid #d0d0d8; margin: 16px 0 12px; }
.nightMode hr#answer { border-top-color: #4a4a55; }

.opts { margin-top: 14px; }
.opts p { margin: 6px 0; }
.answer { font-weight: 600; }
.letter {
  display: inline-block; min-width: 1.6em; text-align: center;
  background: #2f6f4f; color: #fff; border-radius: 4px;
  padding: 0 4px; margin-right: 6px; font-weight: 700;
}
.expl { margin-top: 14px; font-weight: 400; }
.lbl {
  font-size: 0.7em; letter-spacing: 0.08em; text-transform: uppercase;
  color: #8a8a95; margin-bottom: 4px;
}
.meta { margin-top: 18px; font-size: 0.62em; color: #a0a0aa; }
ul, ol { margin: 8px 0; padding-left: 22px; }
"""

BASIC_MODEL = genanki.Model(
    stable_id("model", BASIC_MODEL_NAME),
    BASIC_MODEL_NAME,
    # Поля фиксированы. Добавление поля позже = schema change при импорте на устройстве,
    # поэтому Meta заведено сразу.
    fields=[{"name": "Prompt"}, {"name": "Answer"}, {"name": "Explanation"}, {"name": "Meta"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Prompt}}",
        "afmt": '{{FrontSide}}<hr id=answer>'
                '<div class="answer">{{Answer}}</div>'
                '{{#Explanation}}<div class="expl"><div class="lbl">Почему</div>{{Explanation}}</div>{{/Explanation}}'
                '<div class="meta">{{Meta}}</div>',
    }],
    css=CSS,
)

MCQ_MODEL = genanki.Model(
    stable_id("model", MCQ_MODEL_NAME),
    MCQ_MODEL_NAME,
    fields=[{"name": "Prompt"}, {"name": "Options"}, {"name": "AnswerLetter"},
            {"name": "AnswerText"}, {"name": "Explanation"}, {"name": "Meta"}],
    templates=[{
        "name": "Card 1",
        "qfmt": '{{Prompt}}<div class="opts">{{Options}}</div>',
        # На обороте буква И полный текст варианта: одна буква запоминается как
        # позиция, а не как факт.
        "afmt": '{{FrontSide}}<hr id=answer>'
                '<div class="answer"><span class="letter">{{AnswerLetter}}</span>{{AnswerText}}</div>'
                '{{#Explanation}}<div class="expl"><div class="lbl">Почему</div>{{Explanation}}</div>{{/Explanation}}'
                '<div class="meta">{{Meta}}</div>',
    }],
    css=CSS,
)


# -------------------------------------------------------------------------- ids.lock

def read_lock() -> dict[str, dict]:
    entries: dict[str, dict] = {}
    if not LOCK_PATH.exists():
        return entries
    for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            entries[parts[0]] = {"first_seen": parts[1], "status": parts[2]}
    return entries


def write_lock(entries: dict[str, dict]) -> None:
    header = (
        "# Append-only реестр всех id, когда-либо существовавших в колоде.\n"
        "# Формат: <id> <first_seen> <active|retired>\n"
        "# retired = карта удалена из YAML. Такой id переиспользовать НЕЛЬЗЯ:\n"
        "# GUID заметки считается из id, и новая карта склеится с историей повторений старой.\n"
        "# Файл обновляется build.py автоматически. Руками не редактировать.\n"
    )
    body = "".join(
        f"{cid} {e['first_seen']} {e['status']}\n" for cid, e in sorted(entries.items())
    )
    LOCK_PATH.write_text(header + body, encoding="utf-8")


# --------------------------------------------------------------------------- load

def load_taxonomy() -> dict[str, list[str]]:
    return yaml.safe_load((ROOT / "taxonomy.yaml").read_text(encoding="utf-8")) or {}


def load_schema() -> dict:
    return json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))


def load_cards() -> list[tuple[Path, int, dict]]:
    """-> [(файл, индекс в файле, карта)] для внятных сообщений об ошибках."""
    out: list[tuple[Path, int, dict]] = []
    for path in sorted(CARDS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data is None:
            continue
        if not isinstance(data, list):
            raise SystemExit(f"{path}: файл должен быть списком карт, получено {type(data).__name__}")
        for i, card in enumerate(data):
            out.append((path.relative_to(ROOT), i, card))
    return out


# ----------------------------------------------------------------------- validate

def normalize(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.lower()).strip()


def validate(cards, taxonomy, schema) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    lock = read_lock()

    seen_ids: dict[str, str] = {}
    prompts: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for path, idx, card in cards:
        where = f"{path}[{idx}]"
        if not isinstance(card, dict):
            errors.append(f"{where}: карта должна быть маппингом")
            continue
        cid = card.get("id", "<нет id>")
        where = f"{path} {cid}"

        for err in sorted(validator.iter_errors(card), key=lambda e: list(e.path)):
            loc = ".".join(str(p) for p in err.path) or "<корень>"
            errors.append(f"{where}: schema: {loc}: {err.message}")

        domain, subtopic = card.get("domain"), card.get("subtopic")
        if domain in taxonomy and subtopic not in taxonomy[domain]:
            errors.append(
                f"{where}: subtopic '{subtopic}' нет в taxonomy.yaml для домена '{domain}'. "
                f"Сначала добавь его в taxonomy.yaml."
            )

        if cid in seen_ids:
            errors.append(f"{where}: дубликат id, уже есть в {seen_ids[cid]}")
        else:
            seen_ids[cid] = str(path)

        if lock.get(cid, {}).get("status") == "retired":
            errors.append(
                f"{where}: id переиспользован — он помечен retired в ids.lock. "
                f"Возьми новый номер: GUID считается из id, эта карта склеится с историей удалённой."
            )

        if card.get("type") == "mcq":
            opts = card.get("options") or {}
            if card.get("answer") not in opts:
                errors.append(f"{where}: answer '{card.get('answer')}' не входит в options {sorted(opts)}")

        if card.get("prompt"):
            prompts[card.get("domain", "?")].append((cid, normalize(card["prompt"])))

    # точные дубли prompt — fail; близкие — warning про интерференцию
    for domain, items in prompts.items():
        by_text: dict[str, list[str]] = defaultdict(list)
        for cid, text in items:
            by_text[text].append(cid)
        for text, ids in by_text.items():
            if len(ids) > 1:
                errors.append(f"{domain}: одинаковый prompt у карт {', '.join(ids)}")
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (id_a, a), (id_b, b) = items[i], items[j]
                if a == b or abs(len(a) - len(b)) > max(len(a), len(b)) * 0.5:
                    continue
                ratio = SequenceMatcher(None, a, b).ratio()
                if ratio >= SIMILARITY_WARN:
                    warnings.append(
                        f"{domain}: prompt похожи на {ratio:.0%} — {id_a} / {id_b}. "
                        f"Риск интерференции, посмотри глазами."
                    )

    live = [c for _, _, c in cards if isinstance(c, dict) and not c.get("deprecated")]
    per_sub = Counter((c.get("domain"), c.get("subtopic")) for c in live)
    per_dom = Counter(c.get("domain") for c in live)
    for (dom, sub), n in sorted(per_sub.items()):
        if n > MAX_PER_SUBTOPIC:
            warnings.append(f"бюджет: {dom}/{sub} — {n} карт (потолок {MAX_PER_SUBTOPIC})")
    for dom, n in sorted(per_dom.items()):
        if n > MAX_PER_DOMAIN:
            warnings.append(f"бюджет: домен {dom} — {n} карт (потолок {MAX_PER_DOMAIN})")
    if len(live) > MAX_TOTAL:
        warnings.append(f"бюджет: всего {len(live)} активных карт (целевой потолок {MAX_TOTAL})")

    return errors, warnings


def sync_lock(cards) -> list[str]:
    """Новые id -> active. Пропавшие active -> retired (их id больше не выдаём)."""
    notes: list[str] = []
    lock = read_lock()
    today = dt.date.today().isoformat()
    current = {c["id"] for _, _, c in cards if isinstance(c, dict) and "id" in c}
    for cid in sorted(current - set(lock)):
        lock[cid] = {"first_seen": today, "status": "active"}
    for cid, entry in lock.items():
        if entry["status"] == "active" and cid not in current:
            entry["status"] = "retired"
            notes.append(
                f"{cid}: карта пропала из YAML -> помечена retired. "
                f"Напоминание: на устройстве она осталась, чистить надо через tag:deprecated."
            )
    write_lock(lock)
    return notes


# -------------------------------------------------------------------------- build

def card_tags(card: dict) -> list[str]:
    tags = [f"topic::{card['subtopic']}", f"difficulty::{card['difficulty']}"]
    src = card["source"]
    for s in ([src] if isinstance(src, str) else src):
        tags.append(f"source::{s}")
    if card.get("situational"):
        tags.append("situational")
    if not card.get("verified", False):
        tags.append("unverified")
    if card.get("deprecated"):
        tags.append("deprecated")
    return tags


def render_options(options: dict[str, str]) -> str:
    rows = "".join(
        f'<p><b>{letter})</b> {render(text).removeprefix("<p>").removesuffix("</p>")}</p>'
        for letter, text in sorted(options.items())
    )
    return rows


def make_note(card: dict) -> genanki.Note:
    meta = html.escape(card["id"])
    if card.get("ref"):
        meta += " · " + html.escape(card["ref"])

    if card.get("type") == "mcq":
        opts = card["options"]
        fields = [
            render(card["prompt"]),
            render_options(opts),
            card["answer"] + ")",
            render(opts[card["answer"]]),
            render(card["explanation"]),
            meta,
        ]
        model = MCQ_MODEL
    else:
        fields = [
            render(card["prompt"]),
            render(card["answer"]),
            render(card["explanation"]),
            meta,
        ]
        model = BASIC_MODEL

    return genanki.Note(
        model=model,
        fields=fields,
        # ЕДИНСТВЕННЫЙ источник GUID — id. Правка текста карту не пересоздаёт.
        guid=genanki.guid_for(card["id"]),
        tags=card_tags(card),
    )


def build(cards) -> dict:
    decks: dict[str, genanki.Deck] = {}
    manifest_cards = []

    for _, _, card in cards:
        deck_name = f"{DECK_ROOT}::{card['domain']}"
        if deck_name not in decks:
            decks[deck_name] = genanki.Deck(stable_id("deck", deck_name), deck_name)
        note = make_note(card)
        decks[deck_name].add_note(note)
        manifest_cards.append({
            "id": card["id"],
            "guid": note.guid,
            "deck": deck_name,
            "tags": note.tags,
            "type": card.get("type", "basic"),
            "content_sha": hashlib.sha256(
                "\x1f".join(note.fields).encode("utf-8")
            ).hexdigest()[:16],
        })

    BUILD_DIR.mkdir(exist_ok=True)
    genanki.Package(list(decks.values())).write_to_file(BUILD_DIR / "devops.apkg")

    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "count": len(manifest_cards),
        "decks": sorted(decks),
        "cards": sorted(manifest_cards, key=lambda c: c["id"]),
    }
    (BUILD_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


# ----------------------------------------------------------------------- веб-тренажёр

def web_payload(cards) -> list[dict]:
    """Те же карты, что в .apkg, но для веб-тренажёра. Рендер общий с Anki —
    один источник правды на разметку."""
    out = []
    for _, _, card in cards:
        if card.get("deprecated"):
            continue
        src = card["source"]
        item = {
            "id": card["id"],
            "domain": card["domain"],
            "subtopic": card["subtopic"],
            "difficulty": card["difficulty"],
            "source": [src] if isinstance(src, str) else src,
            "type": card.get("type", "basic"),
            "situational": bool(card.get("situational")),
            "verified": bool(card.get("verified")),
            "prompt": render(card["prompt"]),
            "explanation": render(card["explanation"]),
        }
        if item["type"] == "mcq":
            item["options"] = {k: render(v) for k, v in card["options"].items()}
            item["answer"] = card["answer"]
        else:
            item["answer"] = render(card["answer"])
        if card.get("ref"):
            item["ref"] = card["ref"]
        out.append(item)
    return out


PAGE_HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="DevOps Drill">
<meta name="theme-color" content="#e9edf0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#12171b" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#127919;</text></svg>">
{title}
</head>
<body>
"""


def build_web(cards) -> int:
    """Две сборки одной страницы:
      build/drill.html — фрагмент для Artifact (там свой doctype и head);
      build/index.html — самостоятельный документ для GitHub Pages.
    Карты вшиты внутрь, за данными страница никуда не ходит."""
    template = (ROOT / "web" / "drill.html").read_text(encoding="utf-8")
    payload = web_payload(cards)
    marker = "/*__CARDS__*/[]"
    if marker not in template:
        raise SystemExit("web/drill.html: не найден маркер для подстановки карт")
    page = template.replace(marker, json.dumps(payload, ensure_ascii=False))

    BUILD_DIR.mkdir(exist_ok=True)
    (BUILD_DIR / "drill.html").write_text(page, encoding="utf-8")

    title = re.search(r"<title>.*?</title>", page)
    (BUILD_DIR / "index.html").write_text(
        PAGE_HEAD.format(title=title.group(0) if title else "<title>DevOps Drill</title>")
        + page + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    return len(payload)


# -------------------------------------------------------------------------- index

def print_index(cards, domain: str | None) -> None:
    rows = [c for _, _, c in cards if not domain or c.get("domain") == domain]
    rows.sort(key=lambda c: (c.get("domain", ""), c.get("subtopic", ""), c.get("id", "")))
    if not rows:
        print(f"карт нет{f' в домене {domain}' if domain else ''}")
        return
    for c in rows:
        flags = "".join([
            "D" if c.get("deprecated") else ".",
            "S" if c.get("situational") else ".",
            "V" if c.get("verified") else ".",
        ])
        head = " ".join(c.get("prompt", "").split())[:80]
        print(f"{c.get('id',''):<28} {c.get('subtopic',''):<22} {c.get('difficulty',''):<7} {flags}  {head}")
    print(f"\nвсего: {len(rows)}")


# ---------------------------------------------------------------------------- cli

def main() -> int:
    ap = argparse.ArgumentParser(description="Сборка колоды DevOps Anki")
    ap.add_argument("--validate", action="store_true", help="только валидация")
    ap.add_argument("--index", nargs="?", const="", metavar="DOMAIN",
                    help="индекс карт (читать перед генерацией темы)")
    args = ap.parse_args()

    cards = load_cards()

    if args.index is not None:
        print_index(cards, args.index or None)
        return 0

    errors, warnings = validate(cards, load_taxonomy(), load_schema())
    for w in warnings:
        print(f"WARN  {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"FAIL  {e}", file=sys.stderr)
        print(f"\n{len(errors)} ошибок валидации", file=sys.stderr)
        return 1

    if args.validate:
        print(f"OK: {len(cards)} карт валидны ({len(warnings)} warnings)")
        return 0

    for note in sync_lock(cards):
        print(f"NOTE  {note}", file=sys.stderr)

    manifest = build(cards)
    n_web = build_web(cards)
    print(f"OK: {manifest['count']} карт -> build/devops.apkg")
    print(f"    деки: {', '.join(manifest['decks'])}")
    print(f"    {n_web} карт -> build/drill.html + build/index.html (тренажёр)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
