"""
Тесты на инварианты пайплайна. Всё, что здесь проверяется, ломает колоду молча:
дубли карт при импорте, потеря истории повторений, съеденный HTML в коде.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build as B  # noqa: E402


# --------------------------------------------------------------------- helpers

def card(**over):
    base = dict(
        id="k8s-probes-999",
        domain="k8s",
        subtopic="probes",
        difficulty="middle",
        source="theory",
        type="basic",
        prompt="Вопрос про пробы?",
        answer="Ответ.",
        explanation="Потому что так устроен kubelet.",
    )
    base.update(over)
    return base


def notes_from_apkg(path: Path):
    """(guid, tags, fields) из реального .apkg — а не из внутренних структур."""
    with zipfile.ZipFile(path) as z:
        name = "collection.anki21" if "collection.anki21" in z.namelist() else "collection.anki2"
        with tempfile.TemporaryDirectory() as d:
            z.extract(name, d)
            con = sqlite3.connect(os.path.join(d, name))
            rows = con.execute("select guid, tags, flds from notes").fetchall()
            con.close()
    return sorted(rows)


# ----------------------------------------------------------------- GUID / дубли

def test_two_builds_produce_identical_notes():
    """Повторная сборка обязана дать те же GUID: иначе каждый импорт плодит дубли.
    Сравниваем извлечённое содержимое, а не хеш файла — .apkg это zip+sqlite,
    побайтово он не воспроизводим."""
    def run():
        subprocess.run([sys.executable, "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        manifest = json.loads((ROOT / "build" / "manifest.json").read_text("utf-8"))
        return notes_from_apkg(ROOT / "build" / "devops.apkg"), manifest

    notes_a, man_a = run()
    notes_b, man_b = run()

    assert notes_a == notes_b
    assert [(c["id"], c["guid"], c["content_sha"]) for c in man_a["cards"]] == \
           [(c["id"], c["guid"], c["content_sha"]) for c in man_b["cards"]]


def test_guid_survives_content_edit():
    """Правка текста не должна пересоздавать карту — иначе теряется история повторений."""
    a = B.make_note(card())
    b = B.make_note(card(explanation="Совершенно другое объяснение, гораздо длиннее.",
                         answer="Другой ответ."))
    assert a.guid == b.guid


def test_guid_depends_on_id_only():
    assert B.make_note(card()).guid != B.make_note(card(id="k8s-probes-998")).guid
    # поля, не входящие в id, на GUID не влияют
    assert B.make_note(card()).guid == B.make_note(card(subtopic="pods")).guid


def test_model_and_deck_ids_are_stable():
    """Случайные id моделей/деков создают новый notetype при каждом импорте."""
    assert B.stable_id("model", B.BASIC_MODEL_NAME) == B.BASIC_MODEL.model_id
    assert B.stable_id("deck", "DevOps::k8s") == B.stable_id("deck", "DevOps::k8s")
    assert B.stable_id("deck", "DevOps::k8s") != B.stable_id("deck", "DevOps::linux")
    assert 1 << 30 <= B.BASIC_MODEL.model_id < 1 << 31


# ------------------------------------------------------------------- рендеринг

def test_html_in_prose_is_escaped():
    """`<pending>` из конспекта не должен исчезнуть как неизвестный тег."""
    out = B.render("Service type LoadBalancer вечно висит в <pending>")
    assert "&lt;pending&gt;" in out
    assert "<pending>" not in out


def test_ampersand_in_prose_survives():
    assert "&amp;&amp;" in B.render("Условие A && B")


def test_fenced_code_becomes_pre_and_keeps_newlines():
    out = B.render("Смотри:\n\n```bash\nkubectl get po\nkubectl get svc\n```")
    assert "<pre>" in out and "<code" in out
    assert "kubectl get po\nkubectl get svc" in out


def test_angle_brackets_inside_code_are_escaped_not_swallowed():
    out = B.render("Команда: `kubectl get po <name>`")
    assert "&lt;name&gt;" in out
    assert "<name>" not in out


def test_inline_code_renders_as_code_tag():
    assert "<code>readinessProbe</code>" in B.render("Проверь `readinessProbe` в спеке")


# ------------------------------------------------------------------------ теги

def test_source_list_gives_one_tag_per_source():
    tags = B.card_tags(card(source=["theory", "interview"]))
    assert "source::theory" in tags and "source::interview" in tags


def test_core_is_a_valid_source(ctx):
    """core = карта добавлена для полноты покрытия, вне конспектов и собесов."""
    assert B.validate(wrap(card(source="core")), *ctx)[0] == []
    assert "source::core" in B.card_tags(card(source="core"))


def test_unknown_source_fails(ctx):
    assert B.validate(wrap(card(source="chatgpt")), *ctx)[0]


def test_default_tags():
    tags = B.card_tags(card())
    assert "topic::probes" in tags
    assert "difficulty::middle" in tags
    assert "unverified" in tags          # verified не проставлен
    assert "deprecated" not in tags


def test_verified_and_deprecated_flags():
    assert "unverified" not in B.card_tags(card(verified=True))
    assert "deprecated" in B.card_tags(card(deprecated=True))


def test_tags_have_no_spaces():
    """Anki режет теги по пробелам — тег с пробелом развалится на два."""
    for tag in B.card_tags(card(source=["theory", "web"], situational=True)):
        assert " " not in tag


# -------------------------------------------------------------------- MCQ / поля

def test_mcq_back_shows_letter_and_full_text():
    note = B.make_note(card(
        type="mcq",
        options={"a": "Перезапустится", "b": "Выпадет из endpoints", "c": "Ничего"},
        answer="b",
    ))
    assert note.fields[2] == "b)"
    assert "Выпадет из endpoints" in note.fields[3]


def test_meta_field_carries_id():
    assert "k8s-probes-999" in B.make_note(card()).fields[-1]


# ------------------------------------------------------------------- валидация

@pytest.fixture
def ctx():
    return B.load_taxonomy(), B.load_schema()


def wrap(*cards):
    return [(Path("cards/test.yaml"), i, c) for i, c in enumerate(cards)]


def test_subtopic_outside_taxonomy_fails(ctx):
    errors, _ = B.validate(wrap(card(subtopic="liveness-probe")), *ctx)
    assert any("taxonomy.yaml" in e for e in errors)


def test_duplicate_id_fails(ctx):
    errors, _ = B.validate(wrap(card(), card(prompt="Другой вопрос совсем?")), *ctx)
    assert any("дубликат id" in e for e in errors)


def test_identical_prompt_fails(ctx):
    errors, _ = B.validate(wrap(card(), card(id="k8s-probes-998")), *ctx)
    assert any("одинаковый prompt" in e for e in errors)


def test_mcq_answer_outside_options_fails(ctx):
    errors, _ = B.validate(
        wrap(card(type="mcq", options={"a": "x", "b": "y", "c": "z"}, answer="d")), *ctx)
    assert errors


def test_bad_difficulty_fails(ctx):
    assert B.validate(wrap(card(difficulty="hard")), *ctx)[0]


def test_basic_card_with_options_fails(ctx):
    assert B.validate(wrap(card(options={"a": "x", "b": "y", "c": "z"})), *ctx)[0]


def test_situational_mcq_fails(ctx):
    errors, _ = B.validate(wrap(card(
        situational=True, type="mcq",
        options={"a": "x", "b": "y", "c": "z"}, answer="a")), *ctx)
    assert errors


def test_retired_id_reuse_fails(ctx, monkeypatch):
    monkeypatch.setattr(B, "read_lock",
                        lambda: {"k8s-probes-999": {"first_seen": "2026-01-01",
                                                    "status": "retired"}})
    errors, _ = B.validate(wrap(card()), *ctx)
    assert any("retired" in e for e in errors)


def test_similar_prompts_warn(ctx):
    _, warnings = B.validate(wrap(
        card(prompt="Что делает readinessProbe при провале проверки в поде?"),
        card(id="k8s-probes-998",
             prompt="Что делает readinessProbe при провале проверки у пода?"),
    ), *ctx)
    assert any("интерференции" in w for w in warnings)


def test_repo_cards_are_valid(ctx):
    errors, _ = B.validate(B.load_cards(), *ctx)
    assert errors == []
