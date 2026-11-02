import copy
import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from tools.bubble_studio.config import (
    reading_settings_path,
    save_reading_mode,
    series_settings,
)
from tools.bubble_studio.framed_strip_order import refine
from tools.bubble_studio.runner import process_comic
from test_framed_strip_order import scene, Semantic


def test_title_override_does_not_change_neighbouring_archive(tmp_path):
    root = tmp_path / "Manga"
    root.mkdir()
    a = root / "Pierwsza.cbz"
    b = root / "Druga.cbz"
    a.touch()
    b.touch()
    (root / "bubble-studio.json").write_text(
        json.dumps(dict(quality="fast", reading_mode="four_panel_strips")),
        encoding="utf8",
    )
    save_reading_mode(a, "auto", "ltr")
    assert series_settings(a, root)["reading_mode"] == "auto"
    assert series_settings(a, root)["direction"] == "ltr"
    assert series_settings(b, root)["reading_mode"] == "four_panel_strips"
    assert series_settings(b, root)["direction"] == "rtl"
    assert series_settings(a, root)["quality"] == "fast"
    assert reading_settings_path(a).name == "Pierwsza.cbz.bubble-studio.json"


def test_folder_setting_is_inherited_and_preserves_other_options(tmp_path):
    source = tmp_path / "Seria"
    source.mkdir()
    book = source / "tom.cbz"
    book.touch()
    settings = source / "bubble-studio.json"
    settings.write_text(
        json.dumps(dict(quality="fast", include_free_text=True)), encoding="utf8"
    )
    save_reading_mode(source, "four_panel_strips", "rtl")
    got = series_settings(book, tmp_path)
    assert (
        got["quality"] == "fast"
        and got["include_free_text"]
        and got["reading_mode"] == "four_panel_strips"
        and got["direction"] == "rtl"
    )


@pytest.mark.parametrize(
    "values",
    [
        dict(reading_mode="4koma"),
        dict(reading_mode=True),
        dict(reading_mode=[]),
        dict(unknown=True),
    ],
)
def test_bad_title_settings_are_rejected_without_overwrite(tmp_path, values):
    source = tmp_path / "book.cbz"
    source.touch()
    p = reading_settings_path(source)
    p.write_text(json.dumps(values), encoding="utf8")
    raw = p.read_bytes()
    with pytest.raises(ValueError):
        series_settings(source, tmp_path)
    with pytest.raises(ValueError):
        save_reading_mode(source, "four_panel_strips")
    assert p.read_bytes() == raw


@pytest.mark.parametrize("framed", [False, True])
@pytest.mark.parametrize("direction", ["ltr", "rtl"])
def test_declared_4koma_needs_no_semantic_model_and_preserves_local_dialogues(
    framed, direction
):
    d = scene(direction)
    before = copy.deepcopy(d)
    if not framed:
        d["result"]["panels"] = [
            p for p in d["result"]["panels"] if not p["id"].endswith("-0")
        ]
        for b in d["result"]["bubbles"]:
            if b["panel_id"].endswith("-0"):
                b.update(type="text", panel_id=None)
    before = copy.deepcopy(d)
    semantic = Semantic(False)
    a = refine(Image.new("RGB", (1000, 1000)), d, semantic, declared=True)
    assert a != before and d == before and not semantic.calls
    assert (
        a["analysis"]["framed_strip_order"]["classification"]["source"]
        == "user-declaration"
    )
    xs = sorted({b["x"] for b in a["result"]["bubbles"]}, reverse=direction == "rtl")
    assert [b["x"] for b in a["result"]["bubbles"]] == [x for x in xs for _ in range(5)]


@pytest.mark.parametrize("kind", ["manual", "verified", "unassigned", "incomplete"])
def test_declaration_does_not_override_unsafe_or_user_edited_geometry(kind):
    d = scene()
    if kind == "manual":
        d["result"]["bubbles"][0]["manual"] = True
    elif kind == "verified":
        d["review"]["verified"] = True
    elif kind == "unassigned":
        d["analysis"]["reading_anchors"]["b1"]["x"] = 0.99
    elif kind == "incomplete":
        d["result"]["panels"].pop()
    before = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d, None, declared=True) == before


def test_changing_title_mode_invalidates_checkpoint_and_keeps_verified_pages(tmp_path):
    source = tmp_path / "book.cbz"
    buff = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(buff, format="PNG")
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("page.png", buff.getvalue())

    class Analyzer:
        def __init__(self):
            self.modes = []

        def analyze(self, image, **kwargs):
            self.modes.append(kwargs.get("reading_mode", "auto"))
            return dict(
                result=dict(
                    width=100,
                    height=100,
                    direction="rtl",
                    layout="auto",
                    panels=[],
                    bubbles=[],
                    confidence=0,
                ),
                review=dict(verified=False, flags=[]),
                analysis={},
            )

    model = Analyzer()
    out = tmp_path / "out"
    work = tmp_path / "work"
    process_comic(source, Path("book.cbz"), out, work, model, direction="rtl")
    process_comic(
        source,
        Path("book.cbz"),
        out,
        work,
        model,
        direction="rtl",
        reading_mode="four_panel_strips",
    )
    process_comic(
        source,
        Path("book.cbz"),
        out,
        work,
        model,
        direction="rtl",
        reading_mode="four_panel_strips",
    )
    assert model.modes == ["auto", "four_panel_strips"]
    from web.backend.comic_bubble_package import load_package, package_path

    p = load_package(out / "book.cbz")
    assert p.manifest["config"]["reading_mode"] == "four_panel_strips"
    with zipfile.ZipFile(package_path(out / "book.cbz")) as z:
        manifest = json.loads(z.read("manifest.json"))
        doc = json.loads(z.read("pages/00000.json"))
    doc["review"]["verified"] = True
    from tools.bubble_studio.runner import write_package

    write_package(package_path(out / "book.cbz"), manifest, [doc])
    process_comic(
        source, Path("book.cbz"), out, work, model, direction="rtl", reading_mode="auto"
    )
    assert model.modes == ["auto", "four_panel_strips"]
    with zipfile.ZipFile(package_path(out / "book.cbz")) as archive:
        assert json.loads(archive.read("pages/00000.json"))["review"]["verified"]
