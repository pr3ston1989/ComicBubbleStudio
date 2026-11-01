import copy
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from PIL import Image

from tools.bubble_studio import control_buttons as stage
from tools.bubble_studio.geometry import rectangle
from web.backend.comic_bubble_package import validate_result


class Checker:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def locate_context(self, image):
        self.calls += 1
        return self.rows


def fixture(glyphs=None, offset=(0, 0), diameter=40):
    image = np.full((800, 800, 3), 235, np.uint8)
    bodies = [dict(rectangle([400, 60, 600, 150], 800, 800, .99, margin=0), id="b1", order=1, panel_id="p1")]
    glyphs = glyphs or [(2, 0), (3, 0), (0, 1), (3, 1)]
    centers = [(120, 220), (200, 220), (120, 300), (120, 380)]
    for i, ((cx, cy), glyph) in enumerate(zip(centers, glyphs), 2):
        cx, cy = cx + offset[0], cy + offset[1]
        r = diameter // 2
        cv2.circle(image, (cx, cy), r - 1, (0, 0, 0), 2)
        cv2.circle(image, (cx, cy), r - 3, (255, 255, 255), -1)
        if isinstance(glyph, str):
            cv2.putText(image, glyph, (cx - 7, cy + 6), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 0), 2)
        else:
            nh, nv = glyph
            for n in range(nh):
                y = round(cy + (n - (nh - 1) / 2) * diameter * .16)
                cv2.line(image, (cx - diameter // 7, y), (cx + diameter // 7, y), (0, 0, 0), 2)
            for n in range(nv):
                x = round(cx + (n - (nv - 1) / 2) * diameter * .16)
                cv2.line(image, (x, cy - diameter // 5), (x, cy + diameter // 5), (0, 0, 0), 2)
        body = rectangle([cx-r, cy-r, cx+r, cy+r], 800, 800, .8, margin=0)
        body.update(id=f"b{i}", order=i, panel_id="p1", polygons=[[dict(x=.5+.5*np.cos(a), y=.5+.5*np.sin(a)) for a in np.linspace(0, 2*np.pi, 32, endpoint=False)]])
        bodies.append(body)
    bodies.append(dict(rectangle([400, 500, 600, 600], 800, 800, .99, margin=0), id="b6", order=6, panel_id="p1", tail_tip=dict(x=.5, y=.625, confidence=.95, kind="visible-outline")))
    d = dict(result=dict(width=800, height=800, direction="ltr", layout="auto", confidence=.9,
                         panels=[dict(rectangle([30, 30, 700, 700], 800, 800, .99, margin=0), id="p1", order=1)], bubbles=bodies),
             review=dict(verified=False, flags=["check b3", "check b6", "keep page"]),
             analysis=dict(reading_anchors={b["id"]:{k:b[k] for k in ("x", "y", "w", "h")} for b in bodies},
                           text_check=dict(regions=[dict(region_id=b["id"], status="text") for b in bodies]),
                           tail_tips=dict(regions=[dict(region_id="b6", method="visible")]), historical=dict(region_id="b6")))
    dx, dy = offset
    rows = [dict(text="BEEP", score=.999, box=[150+dx, 260+dy, 180+dx, 280+dy]),
            dict(text="BIP", score=.999, box=[230+dx, 180+dy, 260+dx, 200+dy])]
    return Image.fromarray(image), d, Checker(rows)


@pytest.mark.parametrize("offset,diameter", [((0, 0), 40), ((80, 90), 44), ((200, 160), 36)])
def test_confirmed_native_controls_preserve_remaining_reading_and_restore(offset, diameter):
    image, d, checker = fixture(offset=offset, diameter=diameter)
    original = copy.deepcopy(d)
    out = stage.refine(image, d, checker)
    assert d == original
    assert [b["id"] for b in out["result"]["bubbles"]] == ["b1", "b2"]
    for new, old in zip(out["result"]["bubbles"], [d["result"]["bubbles"][0], d["result"]["bubbles"][-1]]):
        assert {k:v for k, v in new.items() if k not in {"id", "order"}} == {k:v for k, v in old.items() if k not in {"id", "order"}}
    assert out["analysis"]["tail_tips"]["regions"][0]["region_id"] == "b2"
    assert out["analysis"]["historical"] == d["analysis"]["historical"]
    assert out["review"]["flags"] == ["check b2", "keep page"]
    validate_result(out["result"])
    assert stage.restore(out)
    out["analysis"].pop("control_buttons")
    assert out == d


@pytest.mark.parametrize("glyphs", [["?", "!", ".", "?"], ["A", "E", "H", "I"], [(2, 0)]*4])
def test_punctuation_letters_and_repeated_symbols_are_preserved(glyphs):
    image, d, checker = fixture(glyphs=glyphs)
    assert stage.refine(image, d, checker) is d


@pytest.mark.parametrize("case", ["verified", "manual", "one-sfx", "speech-sfx", "uncertain-sfx", "no-checker", "inconsistent-size", "not-grid"])
def test_ambiguous_or_user_checked_pages_are_untouched(case):
    image, d, checker = fixture()
    if case == "verified": d["review"]["verified"] = True
    if case == "manual": d["result"]["bubbles"][1]["manual"] = True
    if case == "one-sfx": checker.rows.pop()
    if case == "uncertain-sfx": checker.rows[0]["score"] = .97
    if case == "no-checker": checker = None
    if case == "inconsistent-size": d["result"]["bubbles"][1]["w"] *= 1.3
    if case == "not-grid": d["result"]["bubbles"][1]["x"] += .027
    if case == "speech-sfx":
        b = rectangle(checker.rows[0]["box"], 800, 800, .99, margin=0)
        b.update(id="b7", order=7, panel_id="p1")
        d["result"]["bubbles"].append(b)
    original = copy.deepcopy(d)
    assert stage.refine(image, d, checker) is d
    assert d == original


def test_failure_and_size_limit_leave_original_document_intact():
    image, d, checker = fixture()
    original = copy.deepcopy(d)
    with patch.object(checker, "locate_context", side_effect=RuntimeError("OCR unavailable")):
        assert stage.refine(image, d, checker) is d
    d["analysis"]["padding"] = "x" * (2*1024*1024)
    assert stage.refine(image, d, checker) is d
    d["analysis"].pop("padding")
    assert d == original


def test_clear_non_candidates_do_not_trigger_additional_ocr():
    image, d, checker = fixture(glyphs=["?", "!", ".", "?"])
    assert stage.refine(image, d, checker) is d
    assert checker.calls == 0
