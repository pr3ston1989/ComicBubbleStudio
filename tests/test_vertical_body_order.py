import copy

import pytest
from PIL import Image

from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.vertical_body_order import refine, restore


def scene(direction="rtl"):
    upper = dict(
        rectangle([120, 150, 280, 260], 1000, 1000, 0.98, "bubble", 0),
        id="b2",
        order=2,
        panel_id="p1",
        tail_tip=dict(x=0.25, y=0.25),
    )
    lower = dict(
        rectangle([130, 290, 290, 380], 1000, 1000, 0.98, "bubble", 0),
        id="b1",
        order=1,
        panel_id="p1",
        tail_tip=dict(x=0.25, y=0.37),
    )
    bs = [lower, upper]
    for b in bs:
        b["polygons"] = [[dict(x=0,y=0),dict(x=1,y=0),dict(x=1,y=1),dict(x=0,y=1)]]
    return dict(
        result=dict(
            width=1000,
            height=1000,
            layout="auto",
            direction=direction,
            panels=[dict(id="p1", x=0.05, y=0.05, w=0.8, h=0.8)],
            bubbles=bs,
        ),
        analysis=dict(
            reading_anchors={
                b["id"]: {k: b[k] for k in ("x", "y", "w", "h")} for b in bs
            },
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
                    for b in bs
                ]
            ),
            tail_tips=dict(regions=[dict(region_id=b["id"], checked=True) for b in bs]),
        ),
        review=dict(verified=False, flags=["Sprawdz b2"]),
    )


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
def test_same_column_is_read_top_to_bottom_without_geometry_or_text_changes(direction):
    d = scene(direction)
    original = copy.deepcopy(d)
    a = refine(Image.new("RGB", (1000, 1000)), d)
    assert d == original and a != d
    mapping = a["analysis"]["vertical_body_order"]["mapping"]
    assert mapping == dict(b2="b1", b1="b2")
    for old in original["result"]["bubbles"]:
        new = next(b for b in a["result"]["bubbles"] if b["id"] == mapping[old["id"]])
        assert {k: v for k, v in old.items() if k not in {"id", "order"}} == {
            k: v for k, v in new.items() if k not in {"id", "order"}
        }
        assert (
            a["analysis"]["reading_anchors"][new["id"]]
            == original["analysis"]["reading_anchors"][old["id"]]
        )
    assert a["result"]["panels"] == original["result"]["panels"]
    assert a["review"]["flags"] == ["Sprawdz b1"]
    assert [r["region_id"] for r in a["analysis"]["tail_tips"]["regions"]] == [
        "b2",
        "b1",
    ]
    assert refine(Image.new("RGB", (1000, 1000)), a) == a
    assert (
        restore(a)
        and a["result"] == original["result"]
        and a["review"] == original["review"]
    )
    assert not restore(a)


@pytest.mark.parametrize(
    "kind",
    [
        "manual",
        "verified",
        "different-panel",
        "orphan",
        "rows",
        "single",
        "missing-anchor",
        "no-contour",
        "multiple-contours",
        "outside-panel",
        "body-overlap",
        "far-apart",
        "different-column",
        "text-conflict",
    ],
)
def test_uncertainty_or_user_choice_preserves_existing_order(kind):
    d = scene()
    lower, upper = d["result"]["bubbles"]
    if kind == "manual":
        lower["manual"] = True
    elif kind == "verified":
        d["review"]["verified"] = True
    elif kind == "different-panel":
        upper["panel_id"] = "p2"
    elif kind == "orphan":
        upper["panel_id"] = None
    elif kind in {"rows", "single"}:
        d["result"]["layout"] = kind
    elif kind == "missing-anchor":
        d["analysis"]["reading_anchors"].pop("b1")
    elif kind == "no-contour":
        upper.pop("polygons")
    elif kind == "multiple-contours":
        upper["polygons"].append(copy.deepcopy(upper["polygons"][0]))
    elif kind == "outside-panel":
        d["result"]["panels"][0]["x"] = 0.5
    elif kind == "body-overlap":
        lower["y"] = 0.2
    elif kind == "far-apart":
        lower["y"] = 0.6
    elif kind == "different-column":
        lower["x"] = 0.5
    elif kind == "text-conflict":
        d["analysis"]["reading_anchors"]["b2"].update(y=0.31)
    original = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d) == original


def test_intervening_speaker_is_not_crossed():
    d = scene()
    b = copy.deepcopy(d["result"]["bubbles"][0])
    b.update(id="b3", x=0.6, order=2)
    d["result"]["bubbles"].insert(1, b)
    d["analysis"]["reading_anchors"]["b3"] = {k: b[k] for k in ("x", "y", "w", "h")}
    original = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d) == original


def test_oversized_audit_is_atomic():
    d = scene()
    d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    original = copy.deepcopy(d)
    assert refine(Image.new("RGB", (1000, 1000)), d) == original
