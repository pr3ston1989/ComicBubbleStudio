import copy

import pytest
from PIL import Image

from tools.bubble_studio.framed_strip_order import refine, restore


def scene(direction="rtl", columns=2):
    panels = []
    groups = []
    for col in range(columns):
        x = 0.04 + col * 0.32
        group = []
        for row in range(5):
            y, h = (0.04, 0.05) if row == 0 else (0.12 + (row - 1) * 0.21, 0.18)
            pid = f"p{col}-{row}"
            panels.append(dict(id=pid, x=x, y=y, w=0.28, h=h))
            group.append(
                dict(
                    x=x + 0.05,
                    y=y + 0.01,
                    w=0.1,
                    h=0.02,
                    type="bubble",
                    panel_id=pid,
                    confidence=0.98,
                    tail_tip=dict(x=x + 0.10, y=y + 0.04),
                )
            )
        groups.append(group)
    bubbles = [groups[c][row] for row in range(5) for c in range(columns)]
    for i, b in enumerate(bubbles):
        b.update(id=f"b{i + 1}", order=i + 1)
    anchors = {b["id"]: {k: b[k] for k in ("x", "y", "w", "h")} for b in bubbles}
    return dict(
        result=dict(
            width=1000,
            height=1000,
            layout="auto",
            direction=direction,
            panels=panels,
            bubbles=bubbles,
            confidence=0.98,
        ),
        analysis=dict(
            reading_anchors=anchors,
            text_check=dict(
                regions=[
                    dict(
                        region_id=b["id"],
                        box=[
                            b["x"] * 1000,
                            b["y"] * 1000,
                            (b["x"] + b["w"]) * 1000,
                            (b["y"] + b["h"]) * 1000,
                        ],
                        ocr=[],
                    )
                    for b in bubbles
                ]
            ),
            tail_tips=dict(
                regions=[dict(region_id=b["id"], checked=True) for b in bubbles]
            ),
        ),
        review=dict(verified=False, flags=["Sprawdz b2"]),
    )


class Semantic:
    def __init__(self, answer=True):
        self.answer = answer
        self.calls = []

    def _ask(self, images, prompt):
        self.calls.append(dict(images=len(images), prompt=prompt))
        return dict(four_panel_strips=self.answer)


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
@pytest.mark.parametrize("columns", [2, 3])
def test_framed_title_and_entire_story_preserve_geometry_and_metadata(
    direction, columns
):
    im = Image.new("RGB", (1000, 1000))
    d = scene(direction, columns)
    before = copy.deepcopy(d)
    semantic = Semantic()
    a = refine(im, d, semantic)
    assert d == before and len(semantic.calls) == 1
    bs = a["result"]["bubbles"]
    xs = sorted({b["x"] for b in bs}, reverse=direction == "rtl")
    assert [b["x"] for b in bs] == [x for x in xs for _ in range(5)]
    mapping = a["analysis"]["framed_strip_order"]["mapping"]
    for b in before["result"]["bubbles"]:
        new = next(v for v in bs if v["id"] == mapping[b["id"]])
        assert {k: v for k, v in b.items() if k not in {"id", "order"}} == {
            k: v for k, v in new.items() if k not in {"id", "order"}
        }
        assert (
            a["analysis"]["reading_anchors"][new["id"]]
            == before["analysis"]["reading_anchors"][b["id"]]
        )
    assert a["result"]["panels"] == before["result"]["panels"]
    assert [b["id"] for b in bs] == [f"b{i + 1}" for i in range(5 * columns)]
    assert {r["region_id"] for r in a["analysis"]["tail_tips"]["regions"]} == set(
        mapping.values()
    )
    assert refine(im, a, semantic) == a and len(semantic.calls) == 1
    assert (
        restore(a)
        and a["result"] == before["result"]
        and a["review"] == before["review"]
    )
    assert a["analysis"]["text_check"] == before["analysis"]["text_check"]
    assert not restore(a)


@pytest.mark.parametrize("answer", [False, None, 1, "true"])
def test_geometric_grid_without_literal_visual_confirmation_is_unchanged(answer):
    d = scene()
    before = copy.deepcopy(d)
    s = Semantic(answer)
    assert refine(Image.new("RGB", (1000, 1000)), d, s) == before
    assert len(s.calls) == (2 if answer is False else 1)


@pytest.mark.parametrize(
    "kind",
    [
        "manual",
        "verified",
        "rows",
        "single",
        "four",
        "ordinary-five",
        "missing-title",
        "unassigned",
        "incomplete-anchors",
        "unequal-panels",
    ],
)
def test_uncertain_or_user_chosen_layout_never_queries_or_changes(kind):
    d = scene()
    if kind == "manual":
        d["result"]["bubbles"][0]["manual"] = True
    elif kind == "verified":
        d["review"]["verified"] = True
    elif kind in {"rows", "single"}:
        d["result"]["layout"] = kind
    elif kind == "four":
        d["result"]["panels"] = [
            p for p in d["result"]["panels"] if not p["id"].endswith("-0")
        ]
    elif kind == "ordinary-five":
        for p in d["result"]["panels"]:
            if p["id"].endswith("-0"):
                p["h"] = 0.18
    elif kind == "missing-title":
        d["result"]["bubbles"].pop(0)
    elif kind == "unassigned":
        d["result"]["bubbles"][-1]["x"] = 0.98
        d["analysis"]["reading_anchors"][d["result"]["bubbles"][-1]["id"]]["x"] = 0.98
    elif kind == "incomplete-anchors":
        d["analysis"]["reading_anchors"].pop("b1")
    elif kind == "unequal-panels":
        d["result"]["panels"][-1]["h"] = 0.04
    before = copy.deepcopy(d)
    s = Semantic()
    assert refine(Image.new("RGB", (1000, 1000)), d, s) == before and s.calls == []


def test_same_panel_dialogue_order_is_preserved():
    d = scene()
    b = copy.deepcopy(d["result"]["bubbles"][2])
    b.update(id="b11", order=11, x=b["x"] + 0.12)
    d["result"]["bubbles"].append(b)
    d["analysis"]["reading_anchors"]["b11"] = {k: b[k] for k in ("x", "y", "w", "h")}
    a = refine(Image.new("RGB", (1000, 1000)), d, Semantic())
    mapping = a["analysis"]["framed_strip_order"]["mapping"]
    assert int(mapping["b3"][1:]) < int(mapping["b11"][1:])


def test_semantic_failure_is_atomic_and_strict_mode_exposes_failure():
    class Broken:
        strict = False

        def _ask(self, *args):
            raise RuntimeError("offline failure")

    d = scene()
    before = copy.deepcopy(d)
    semantic = Broken()
    assert refine(Image.new("RGB", (1000, 1000)), d, semantic) == before
    semantic.strict = True
    with pytest.raises(RuntimeError):
        refine(Image.new("RGB", (1000, 1000)), d, semantic)
    assert d == before


def test_document_size_limit_preserves_original():
    d = scene()
    d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    before = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d, Semantic()) == before


@pytest.mark.parametrize("panels", [[], [dict(x=0, y=0, w=1, h=1, id="p1")]])
def test_silent_and_unframed_pages_are_left_untouched_in_strict_mode(panels):
    d = scene()
    d["result"]["panels"] = panels
    before = copy.deepcopy(d)
    semantic = Semantic()
    semantic.strict = True
    assert (
        refine(Image.new("RGB", (1000, 1000)), d, semantic) == before
        and semantic.calls == []
    )
