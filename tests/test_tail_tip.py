import copy
from unittest.mock import patch
import cv2, numpy as np, pytest
from PIL import Image
from tools.bubble_studio import tail_tip as stage
from tools.bubble_studio.geometry import contour_box, rectangle
from web.backend.comic_bubble_package import validate_result


def fixture(turn=0, other_tail=False, shape="oval"):
    size = 600
    mask = np.zeros((size, size), np.uint8)
    if shape in {"rectangle", "box-tail"}:
        cv2.rectangle(mask, (190, 220), (410, 380), 1, -1)
    else:
        cv2.ellipse(mask, (300, 280), (110, 85), 0, 0, 360, 1, -1)
    if shape == "box-tail":
        cv2.fillPoly(mask, [np.array([[400, 260], [400, 310], [490, 320]])], 1)
    if shape == "tail":
        cv2.fillPoly(mask, [np.array([[300, 350], [340, 340], [370, 460]])], 1)
        if other_tail:
            cv2.fillPoly(mask, [np.array([[260, 215], [300, 205], [230, 110]])], 1)
    glyph = np.zeros_like(mask)
    cv2.rectangle(glyph, (235, 255), (345, 290), 1, -1)
    mask = np.rot90(mask, turn).copy()
    glyph = np.rot90(glyph, turn).copy()
    yy, xx = np.nonzero(glyph)
    text = [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
    rgb = np.full((size, size, 3), (65, 95, 125), np.uint8)
    rgb[mask > 0] = 0
    rgb[cv2.erode(mask, np.ones((5, 5), np.uint8)) > 0] = 255
    image = Image.fromarray(rgb)
    b = contour_box(mask, (0, 0), size, size, 0.98, epsilon=0.1, max_vertices=2048)
    b.update(id="b1", order=1, panel_id=None)
    anchor = rectangle(text, size, size, 1, margin=0)
    d = dict(
        result=dict(
            width=size,
            height=size,
            direction="ltr",
            layout="auto",
            confidence=0.98,
            panels=[],
            bubbles=[b],
        ),
        review=dict(verified=False, flags=[]),
        analysis=dict(
            reading_anchors=dict(b1={k: anchor[k] for k in ("x", "y", "w", "h")}),
            balloons=[dict(supporting_texts=[dict(box=text, label=1, score=0.99)])],
        ),
    )
    return image, d


@pytest.mark.parametrize("turn", [0, 1, 2, 3])
def test_clear_endpoint_in_all_four_orientations_without_changing_input(turn):
    image, d = fixture(turn, shape="tail")
    before = copy.deepcopy(d)
    out = stage.annotate_tail_tips(image, d)
    assert d == before
    tip = out["result"]["bubbles"][0]["tail_tip"]
    p = np.array([370.0, 460.0])
    for _ in range(turn):
        p = np.array([p[1], 599 - p[0]])
    assert np.linalg.norm(np.array([tip["x"], tip["y"]]) * 600 - p) < 3
    stripped = copy.deepcopy(out)
    stripped["result"]["bubbles"][0].pop("tail_tip")
    stripped["analysis"].pop("tail_tips")
    assert stripped == before
    assert validate_result(out["result"])["bubbles"][0]["tail_tip"] == tip


@pytest.mark.parametrize("shape", ["oval", "rectangle"])
def test_rounded_body_and_narration_corners_are_not_tail_tips(shape):
    im, d = fixture(shape=shape)
    assert stage.annotate_tail_tips(im, d) == d


def test_two_real_tails_are_ambiguous_and_retain_existing_behavior():
    im, d = fixture(other_tail=True, shape="tail")
    assert stage.annotate_tail_tips(im, d) == d


def test_verified_and_manual_regions_remain_untouched():
    im, d = fixture(shape="tail")
    d["review"]["verified"] = True
    assert stage.annotate_tail_tips(im, d) == d
    d["review"]["verified"] = False
    d["result"]["bubbles"][0]["manual"] = True
    assert stage.annotate_tail_tips(im, d) == d


def test_optional_failure_rolls_back_entire_stage():
    im, d = fixture(shape="tail")
    with patch.object(stage, "endpoint", side_effect=RuntimeError("failure")):
        assert stage.annotate_tail_tips(im, d) == d


def test_optional_audit_cannot_push_page_above_reader_budget():
    im, d = fixture(shape="tail")
    d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    assert stage.annotate_tail_tips(im, d) == d


@pytest.mark.parametrize(
    "bad",
    [
        None,
        False,
        [],
        {},
        dict(x=float("nan"), y=0.5, confidence=0.95, kind="visible-outline"),
        dict(x=True, y=0.5, confidence=0.95, kind="visible-outline"),
        dict(x=0.5, y=0.5, confidence=0.95, kind="visible-outline"),
        dict(x=0, y=0, confidence=0.95, kind="visible-outline"),
        dict(x=0.5, y=0.5, confidence=0.1, kind="visible-outline"),
        dict(x=0.5, y=0.5, confidence=0.95, kind="invented-speaker"),
    ],
)
def test_invalid_optional_point_is_ignored_without_rejecting_page(bad):
    im, d = fixture(shape="tail")
    base = validate_result(d["result"])
    d["result"]["bubbles"][0]["tail_tip"] = bad
    assert validate_result(d["result"]) == base


def test_free_text_evidence_does_not_invent_a_speech_tail():
    im, d = fixture(shape="tail")
    d["analysis"]["balloons"][0]["supporting_texts"][0]["label"] = 2
    assert stage.annotate_tail_tips(im, d) == d


def test_frame_or_caption_with_a_corner_point_does_not_become_a_speech_anchor():
    im, d = fixture(shape="box-tail")
    assert stage.annotate_tail_tips(im, d) == d
