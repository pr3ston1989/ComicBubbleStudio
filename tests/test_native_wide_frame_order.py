import copy

import pytest
from PIL import Image, ImageDraw

from tools.bubble_studio import native_wide_frame_order as stage


def frame(y, h, x=0.06, w=0.88):
    return dict(
        x=x,
        y=y,
        w=w,
        h=h,
        poly=[[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
        stability=0.999,
    )


def scene(direction="ltr"):
    # Existing order interleaves a final-row balloon into an earlier native frame.
    positions = [
        (0.24, 0.08),
        (0.30, 0.21),
        (0.76, 0.18),
        (0.19, 0.51),
        (0.17, 0.59),
        (0.44, 0.84),
        (0.80, 0.34),
        (0.70, 0.64),
    ]
    bubbles = []
    for n, (x, y) in enumerate(positions):
        bubbles.append(
            dict(
                id=f"b{n + 1}",
                order=n + 1,
                x=x,
                y=y,
                w=0.09,
                h=0.035,
                confidence=0.98,
                type="bubble",
                panel_id=None,
                polygons=[
                    [dict(x=0, y=0), dict(x=1, y=0), dict(x=1, y=1), dict(x=0, y=1)]
                ],
                tail_tip=dict(x=x + 0.04, y=y + 0.035),
            )
        )
    return dict(
        result=dict(
            width=1000,
            height=1000,
            direction=direction,
            layout="auto",
            panels=[],
            bubbles=bubbles,
        ),
        analysis=dict(
            reading_anchors={
                b["id"]: {k: b[k] for k in ("x", "y", "w", "h")} for b in bubbles
            },
            scene_gutter_order=dict(
                classification=dict(all_physical_panel_gutters=True)
            ),
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
        review=dict(verified=False, flags=["Sprawdz b6 i b8"]),
    )


@pytest.mark.parametrize("direction", ["ltr", "rtl"])
def test_real_two_threshold_frames_recover_scene_order_and_preserve_every_region(
    direction,
):
    image = Image.new("RGB", (1000, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 490, 940, 800), outline="black", width=5)
    draw.rectangle((60, 820, 940, 990), outline="black", width=5)
    d = scene(direction)
    before = copy.deepcopy(d)
    a = stage.refine(image, d)
    assert d == before and a != d
    audit = a["analysis"]["native_wide_frame_order"]
    assert audit["proposal"]["ids"] == ["b1", "b2", "b3", "b7", "b4", "b5", "b8", "b6"]
    assert len(audit["proposal"]["frames"]) == 2
    for b in before["result"]["bubbles"]:
        new = next(
            v for v in a["result"]["bubbles"] if v["id"] == audit["mapping"][b["id"]]
        )
        assert {k: v for k, v in b.items() if k not in {"id", "order"}} == {
            k: v for k, v in new.items() if k not in {"id", "order"}
        }
        assert (
            a["analysis"]["reading_anchors"][new["id"]]
            == before["analysis"]["reading_anchors"][b["id"]]
        )
    assert a["result"]["panels"] == before["result"]["panels"]
    assert [b["order"] for b in a["result"]["bubbles"]] == list(range(1, 9))
    assert {r["region_id"] for r in a["analysis"]["text_check"]["regions"]} == set(
        a["analysis"]["reading_anchors"]
    )
    assert {r["region_id"] for r in a["analysis"]["tail_tips"]["regions"]} == set(
        a["analysis"]["reading_anchors"]
    )
    assert stage.refine(image, a) == a
    assert (
        stage.restore(a)
        and a["result"] == before["result"]
        and a["review"] == before["review"]
    )
    for field in ["reading_anchors", "text_check", "tail_tips"]:
        assert a["analysis"][field] == before["analysis"][field]
    assert not stage.restore(a)


@pytest.mark.parametrize(
    "guard",
    [
        "manual",
        "verified",
        "rows",
        "single",
        "columns",
        "panels",
        "declared",
        "strip",
        "framed-strip",
        "missing-anchors",
        "unconfirmed",
        "numeric-confirmation",
    ],
)
def test_declared_or_uncertain_pages_never_use_native_frame_detector(
    monkeypatch, guard
):
    d = scene()
    if guard == "manual":
        d["result"]["bubbles"][0]["manual"] = True
    elif guard == "verified":
        d["review"]["verified"] = True
    elif guard in {"rows", "single", "columns"}:
        d["result"]["layout"] = guard
    elif guard == "panels":
        d["result"]["panels"] = [dict(id="p1", x=0, y=0, w=1, h=1)]
    elif guard == "declared":
        d["analysis"]["reading_mode"] = "four_panel_strips"
    elif guard == "strip":
        d["analysis"]["strip_reading"] = dict(confirmed=True)
    elif guard == "framed-strip":
        d["analysis"]["framed_strip_order"] = dict(confirmed=True)
    elif guard == "missing-anchors":
        d["analysis"]["reading_anchors"].pop("b1")
    elif guard == "unconfirmed":
        d["analysis"].pop("scene_gutter_order")
    elif guard == "numeric-confirmation":
        d["analysis"]["scene_gutter_order"]["classification"][
            "all_physical_panel_gutters"
        ] = 1

    def no_call(*args):
        raise AssertionError("Detector must not be called")

    monkeypatch.setattr(stage, "panel_frames", no_call)
    before = copy.deepcopy(d)
    assert stage.propose(Image.new("RGB", (1000, 1000)), d) is None
    assert d == before


@pytest.mark.parametrize(
    "frames",
    [
        [frame(0.49, 0.31)],
        [frame(0.49, 0.31, w=0.5), frame(0.82, 0.17, w=0.5)],
        [frame(0.49, 0.36), frame(0.82, 0.17)],
        [frame(0.49, 0.31), frame(0.82, 0.17, x=0.12, w=0.78)],
    ],
)
def test_incomplete_narrow_overlapping_or_misaligned_frame_evidence_is_ignored(
    monkeypatch, frames
):
    monkeypatch.setattr(stage, "panel_frames", lambda im: copy.deepcopy(frames))
    d = scene()
    before = copy.deepcopy(d)
    assert stage.refine(Image.new("RGB", (1000, 1000)), d) == before


def test_no_native_frames_does_not_guess_from_text_geometry():
    d = scene()
    before = copy.deepcopy(d)
    assert stage.refine(Image.new("RGB", (1000, 1000), "white"), d) == before


def test_large_audit_and_detector_failure_are_atomic(monkeypatch):
    monkeypatch.setattr(
        stage, "panel_frames", lambda im: [frame(0.49, 0.31), frame(0.82, 0.17)]
    )
    d = scene()
    d["analysis"]["padding"] = "x" * (2 * 1024 * 1024)
    before = copy.deepcopy(d)
    assert stage.refine(Image.new("RGB", (1000, 1000)), d) == before

    def broken(im):
        raise RuntimeError("simulated detector failure")

    monkeypatch.setattr(stage, "panel_frames", broken)
    assert stage.refine(Image.new("RGB", (1000, 1000)), d) == before


def test_balloon_crossing_native_frame_boundary_blocks_ownership_guess(monkeypatch):
    monkeypatch.setattr(
        stage, "panel_frames", lambda im: [frame(0.49, 0.31), frame(0.82, 0.17)]
    )
    d = scene()
    d["result"]["bubbles"][6]["y"] = 0.48
    d["analysis"]["reading_anchors"]["b7"]["y"] = 0.48
    before = copy.deepcopy(d)
    assert stage.refine(Image.new("RGB", (1000, 1000)), d) == before
