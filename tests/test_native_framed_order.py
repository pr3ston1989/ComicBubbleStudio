import copy
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image
from tools.bubble_studio import native_framed_order as stage
from tools.bubble_studio.geometry import rectangle
from web.backend.comic_bubble_package import validate_result


def fixture(direction="rtl", ratio=1):
    rgb = np.full((900, 900, 3), 175, np.uint8)
    rgb[:, 268:271] = 0
    rgb[:, 271:277] = 255
    rgb[447:450, 277:] = 0
    rgb[450:459, 277:] = 255
    # Current panel assignment incorrectly joins the top of the tall left
    # panel to the upper-right panel; lower-left speech remains unassigned.
    positions = [
        (760, 100),
        (600, 140),
        (170, 100),
        (400, 280),
        (140, 700),
        (760, 550),
        (600, 600),
        (400, 700),
    ]
    bodies = []
    for n, (x, y) in enumerate(positions, 1):
        b = rectangle([x - 30, y - 20, x + 30, y + 20], 900, 900, 0.98, margin=0)
        b.update(
            id=f"b{n}", order=n, panel_id="p1" if n <= 4 else (None if n == 5 else "p2")
        )
        bodies.append(b)
    polygon = [dict(x=0, y=0), dict(x=1, y=0), dict(x=1, y=1), dict(x=0, y=1)]
    bodies[2].update(
        polygon=polygon,
        polygons=[polygon],
        tail_tip=dict(
            x=bodies[2]["x"] + bodies[2]["w"],
            y=bodies[2]["y"],
            confidence=0.95,
            kind="visible-outline",
        ),
    )
    d = dict(
        result=dict(
            width=900,
            height=900,
            direction=direction,
            layout="auto",
            confidence=0.98,
            panels=[
                dict(
                    rectangle([0, 0, 900, 450], 900, 900, 0.9, margin=0),
                    id="p1",
                    order=1,
                ),
                dict(
                    rectangle([277, 459, 900, 900], 900, 900, 0.9, margin=0),
                    id="p2",
                    order=2,
                ),
            ],
            bubbles=bodies,
        ),
        review=dict(verified=False, flags=["check b3"]),
        analysis=dict(
            reading_anchors={
                b["id"]: {k: b[k] for k in ("x", "y", "w", "h")} for b in bodies
            },
            text_check=dict(
                regions=[
                    dict(region_id=b["id"], status="text", box=[0, 0, 900, 900], ocr=[])
                    for b in bodies
                ]
            ),
            tail_tips=dict(regions=[dict(region_id="b3", method="existing")]),
            historical=dict(region_id="b3"),
        ),
    )
    image = Image.fromarray(rgb)
    if ratio != 1:
        image = image.resize((round(900 * ratio), round(900 * ratio)))
        d["result"].update(width=image.width, height=image.height)
    return image, d


@pytest.mark.parametrize(
    "direction,expected",
    [("rtl", [1, 2, 4, 6, 7, 8, 3, 5]), ("ltr", [3, 5, 1, 2, 4, 6, 7, 8])],
)
@pytest.mark.parametrize("ratio", [1, 1.6])
def test_tall_panel_and_stacked_neighbors_keep_each_scene_contiguous(
    direction, expected, ratio
):
    im, d = fixture(direction, ratio)
    original = copy.deepcopy(d)
    out = stage.refine(im, d)
    assert d == original
    assert out is not d
    order = [f"b{n}" for n in expected]
    assert out["analysis"]["native_framed_order"]["proposal"]["ids"] == order
    for actual, identity in zip(out["result"]["bubbles"], order):
        previous = next(b for b in d["result"]["bubbles"] if b["id"] == identity)
        assert {k: v for k, v in actual.items() if k not in {"id", "order"}} == {
            k: v for k, v in previous.items() if k not in {"id", "order"}
        }
    target = f"b{order.index('b3') + 1}"
    assert out["analysis"]["tail_tips"]["regions"][0]["region_id"] == target
    assert out["review"]["flags"] == ["check " + target]
    assert out["analysis"]["historical"] == d["analysis"]["historical"]
    assert validate_result(out["result"])["bubbles"] == out["result"]["bubbles"]
    assert stage.restore(out)
    out["analysis"].pop("native_framed_order")
    assert out == d


@pytest.mark.parametrize(
    "case",
    [
        "no-frame",
        "broken-frame",
        "single-cut",
        "text-crosses",
        "columns",
        "single",
        "strip",
        "verified",
        "manual",
        "no-conflict",
        "missing-anchor",
    ],
)
def test_unsupported_or_user_selected_order_stays_unchanged(case):
    im, d = fixture()
    rgb = np.array(im)
    if case == "no-frame":
        rgb[:, 268:271] = 175
        rgb[447:450, 277:] = 175
    if case == "broken-frame":
        rgb[180:400, 268:271] = 175
    if case == "single-cut":
        rgb[447:459, 277:] = 175
    if case == "text-crosses":
        d["analysis"]["reading_anchors"]["b3"].update(x=0.27, w=0.1)
    if case in {"columns", "single"}:
        d["result"]["layout"] = case
    if case == "strip":
        d["analysis"]["strip_reading"] = {"method": "4koma"}
    if case == "verified":
        d["review"]["verified"] = True
    if case == "manual":
        d["result"]["bubbles"][0]["manual"] = True
    if case == "no-conflict":
        for b in d["result"]["bubbles"]:
            b["panel_id"] = None
    if case == "missing-anchor":
        d["analysis"]["reading_anchors"].pop("b2")
    original = copy.deepcopy(d)
    assert stage.refine(Image.fromarray(rgb), d) is d
    assert d == original


def test_exception_and_package_size_limit_roll_back_without_partial_ids():
    im, d = fixture()
    original = copy.deepcopy(d)
    with patch.object(stage, "propose", side_effect=RuntimeError("unavailable")):
        assert stage.refine(im, d) is d
    assert d == original
    d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    assert stage.refine(im, d) is d


def test_repeated_application_does_not_add_a_second_reorder_audit():
    im, d = fixture()
    out = stage.refine(im, d)
    assert out is not d
    assert stage.refine(im, out) is out
