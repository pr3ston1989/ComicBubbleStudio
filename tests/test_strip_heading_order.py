import copy
import hashlib
import json

import pytest
from PIL import Image

from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.strip_heading_order import confirmed, refine, restore
from tools.bubble_studio.strip_reader import STRIP_CONTEXT_PROMPT, STRIP_PROMPT


def scene(direction="rtl", columns=2, silent=False):
    panels = []
    headings = []
    bodies = []
    xs = sorted([0.04 + n * 0.32 for n in range(columns)], reverse=direction == "rtl")
    for c, x in enumerate(xs):
        for n in range(4):
            panels.append(dict(id=f"p{c}-{n}", x=x, y=0.12 + n * 0.21, w=0.28, h=0.18))
        headings.append(
            dict(
                rectangle(
                    [(x + 0.02) * 1000, 80, (x + 0.23) * 1000, 105],
                    1000,
                    1000,
                    0.99,
                    "text",
                    0,
                ),
                panel_id=None,
            )
        )
        if not (silent and c == 1):
            for n in range(4):
                bodies.append(
                    dict(
                        rectangle(
                            [
                                (x + 0.05) * 1000,
                                160 + n * 210,
                                (x + 0.15) * 1000,
                                200 + n * 210,
                            ],
                            1000,
                            1000,
                            0.95,
                            "bubble",
                            0,
                        ),
                        panel_id=f"p{c}-{n}",
                        tail_tip={"x": x + 0.1, "y": 0.20 + n * 0.21},
                    )
                )
    bubbles = headings + bodies
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
        ),
        analysis=dict(
            reading_anchors=anchors,
            strip_reading=dict(classification=dict(four_panel_strips=True)),
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


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
@pytest.mark.parametrize("columns", [2, 3])
@pytest.mark.parametrize("silent", [False, True])
def test_heading_follows_its_story_even_when_other_story_is_silent(
    direction, columns, silent
):
    d = scene(direction, columns, silent)
    before = copy.deepcopy(d)
    a = refine(Image.new("RGB", (1000, 1000)), d)
    assert d == before and a != d
    mapping = a["analysis"]["strip_heading_order"]["mapping"]
    original = {b["id"]: b for b in before["result"]["bubbles"]}
    for old, new in mapping.items():
        b = next(b for b in a["result"]["bubbles"] if b["id"] == new)
        assert {k: v for k, v in b.items() if k not in {"id", "order"}} == {
            k: v for k, v in original[old].items() if k not in {"id", "order"}
        }
    title_ids = a["analysis"]["strip_heading_order"]["proposal"]["headings"]
    original_body_order = [
        mapping[b["id"]]
        for b in before["result"]["bubbles"]
        if b["id"] not in title_ids
    ]
    assert [
        b["id"]
        for b in a["result"]["bubbles"]
        if b["id"] not in {mapping[i] for i in title_ids}
    ] == original_body_order
    ids = {b["id"] for b in a["result"]["bubbles"]}
    assert set(a["analysis"]["reading_anchors"]) == ids
    for field in ["text_check", "tail_tips"]:
        assert {v["region_id"] for v in a["analysis"][field]["regions"]} == ids
    assert refine(Image.new("RGB", (1000, 1000)), a) == a
    assert (
        restore(a)
        and a["result"] == before["result"]
        and a["review"] == before["review"]
    )
    for field in ["reading_anchors", "text_check", "tail_tips"]:
        assert a["analysis"][field] == before["analysis"][field]
    assert not restore(a)


@pytest.mark.parametrize("prompt", [STRIP_CONTEXT_PROMPT, STRIP_PROMPT])
def test_existing_positive_vision_call_authorizes_repair_after_old_stage_rolled_back(
    prompt,
):
    d = scene(silent=True)
    d["analysis"].pop("strip_reading")
    d["analysis"]["page_context"] = dict(
        calls=[
            dict(
                prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                answer=json.dumps(dict(four_panel_strips=True)),
            )
        ]
    )
    assert confirmed(d) and refine(Image.new("RGB", (1000, 1000)), d) != d


@pytest.mark.parametrize("answer", [False, 1, "true", None])
def test_geometry_and_non_boolean_answers_do_not_authorize_ordinary_grid(answer):
    d = scene()
    d["analysis"]["strip_reading"]["classification"]["four_panel_strips"] = answer
    d["analysis"]["page_context"] = dict(
        calls=[
            dict(
                prompt_sha256=hashlib.sha256(STRIP_CONTEXT_PROMPT.encode()).hexdigest(),
                answer=json.dumps(dict(four_panel_strips=answer)),
            )
        ]
    )
    assert refine(Image.new("RGB", (1000, 1000)), d) == d


def test_unrelated_positive_prompt_cannot_authorize_repair():
    d = scene()
    d["analysis"].pop("strip_reading")
    d["analysis"]["page_context"] = dict(
        calls=[dict(prompt_sha256="unrelated", answer='{"four_panel_strips":true}')]
    )
    assert not confirmed(d)


@pytest.mark.parametrize(
    "kind",
    [
        "verified",
        "manual",
        "rows",
        "single",
        "missing_anchor",
        "missing_panel",
        "crossing_text",
        "interleaved_dialogue",
        "missing_heading",
        "two_headings",
        "oversize",
    ],
)
def test_uncertainty_and_user_choices_preserve_input(kind):
    d = scene()
    if kind == "verified":
        d["review"]["verified"] = True
    if kind == "manual":
        d["result"]["bubbles"][-1]["manual"] = True
    if kind in {"rows", "single"}:
        d["result"]["layout"] = kind
    if kind == "missing_anchor":
        d["analysis"]["reading_anchors"].pop("b1")
    if kind == "missing_panel":
        d["result"]["panels"].pop()
    if kind == "crossing_text":
        d["analysis"]["reading_anchors"]["b3"].update(x=0.25, w=0.25)
        d["analysis"]["text_check"]["regions"][2]["ocr"] = []
    if kind == "interleaved_dialogue":
        d["result"]["bubbles"][3], d["result"]["bubbles"][6] = (
            d["result"]["bubbles"][6],
            d["result"]["bubbles"][3],
        )
    if kind == "missing_heading":
        d["result"]["bubbles"][1]["type"] = "bubble"
    if kind == "two_headings":
        b = copy.deepcopy(d["result"]["bubbles"][1])
        b.update(id="b11", order=11)
        d["result"]["bubbles"].append(b)
        d["analysis"]["reading_anchors"]["b11"] = copy.deepcopy(
            d["analysis"]["reading_anchors"]["b2"]
        )
    if kind == "oversize":
        d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    before = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d) == before and d == before


def test_malformed_evidence_rolls_back_without_mutation():
    d = scene()
    d["analysis"]["text_check"]["regions"][0]["box"] = None
    before = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d) == before and d == before
