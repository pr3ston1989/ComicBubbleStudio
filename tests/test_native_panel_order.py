import copy
from unittest.mock import patch
import pytest
from PIL import Image, ImageDraw
from tools.bubble_studio import native_panel_order as stage
from tools.bubble_studio.geometry import rectangle
from tools.bubble_studio.quality_metrics import geometry_digest


def fixture(direction):
    width, height = 900, 1000
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for polygon in [
        [(30, 30), (250, 30), (350, 970), (30, 970)],
        [(270, 30), (580, 30), (610, 480), (320, 480)],
        [(600, 30), (870, 30), (870, 480), (630, 480)],
        [(340, 510), (870, 510), (870, 970), (370, 970)],
    ]:
        draw.polygon(polygon, fill="#aabbee", outline="black", width=4)
    panel_bounds = [
        ("p1", [30, 30, 350, 620]),
        ("p2", [30, 500, 350, 970]),
        ("p3", [270, 30, 610, 480]),
        ("p4", [600, 30, 870, 480]),
        ("p5", [340, 510, 870, 970]),
    ]
    specs = [
        ("b1", "p3", [410, 110, 480, 150]),
        ("b2", "p4", [730, 130, 800, 170]),
        ("b3", "p1", [100, 550, 190, 590]),
        ("b4", "p2", [150, 840, 240, 880]),
        ("b5", "p5", [590, 650, 680, 690]),
    ]
    if direction == "rtl":
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        panel_bounds = [
            (k, [width - c, b, width - a, d]) for k, (a, b, c, d) in panel_bounds
        ]
        specs = [(k, p, [width - c, b, width - a, d]) for k, p, (a, b, c, d) in specs]
    panels = []
    for k, box in panel_bounds:
        p = rectangle(box, width, height, 0.95, margin=0)
        p.update(id=k)
        panels.append(p)
    bodies = []
    anchors = {}
    diagnostics = []
    checks = []
    for index, (k, p, box) in enumerate(specs, 1):
        b = rectangle(box, width, height, 0.97, "text", margin=0)
        b.update(id=k, order=index, panel_id=p)
        bodies.append(b)
        anchors[k] = {v: b[v] for v in ("x", "y", "w", "h")}
        diagnostics.append(dict(supporting_texts=[dict(box=box, label=1, score=0.97)]))
        checks.append(
            dict(
                region_id=k,
                box=box,
                ocr=[dict(text=k, score=0.99, box=[0, 0, 1, 1])],
                uncertain=False,
            )
        )
    document = dict(
        result=dict(
            width=width,
            height=height,
            direction=direction,
            layout="auto",
            confidence=0.97,
            panels=panels,
            bubbles=bodies,
        ),
        analysis=dict(
            reading_anchors=anchors,
            balloons=diagnostics,
            text_check=dict(mode="review", regions=checks),
        ),
        review=dict(verified=False, flags=["Sprawdź b3 i b1"]),
    )
    return image, document


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
def test_native_frame_recovers_a_tall_panel_without_changing_geometry_or_words(
    direction,
):
    image, document = fixture(direction)
    before = copy.deepcopy(document)
    result = stage.refine(image, document)
    assert "native_panel_order_error" not in result["analysis"]
    mapping = result["analysis"]["native_panel_order"]["mapping"]
    assert mapping == {"b3": "b1", "b4": "b2", "b1": "b3", "b2": "b4", "b5": "b5"}
    old = {mapping[b["id"]]: geometry_digest(b) for b in before["result"]["bubbles"]}
    assert all(geometry_digest(b) == old[b["id"]] for b in result["result"]["bubbles"])
    assert result["result"]["direction"] == direction
    assert {
        r["ocr"][0]["text"] for r in result["analysis"]["text_check"]["regions"]
    } == {"b1", "b2", "b3", "b4", "b5"}
    assert result["result"]["panels"] == before["result"]["panels"]


def test_verified_and_four_koma_pages_keep_their_established_sequence():
    image, document = fixture("rtl")
    for mode in ["verified", "strip"]:
        d = copy.deepcopy(document)
        if mode == "verified":
            d["review"]["verified"] = True
        else:
            d["analysis"]["strip_reading"] = {"kind": "four-panel-strips"}
        before = copy.deepcopy(d)
        assert stage.refine(image, d) == before


def test_native_frame_failure_rolls_back_the_whole_page():
    image, document = fixture("ltr")
    before = copy.deepcopy(document)
    with patch.object(stage, "propose_order", side_effect=RuntimeError("unavailable")):
        result = stage.refine(image, document)
    assert result["result"] == before["result"]
    assert (
        result["analysis"]["reading_anchors"] == before["analysis"]["reading_anchors"]
    )
    assert result["analysis"]["native_panel_order_error"] == "RuntimeError"
