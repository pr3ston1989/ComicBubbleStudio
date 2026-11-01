"""Independent ink, text ownership and metadata safety for the native-ink stage."""

import copy

import cv2
import numpy as np
from PIL import Image, ImageDraw

from tools.bubble_studio import native_ink as stage
from tools.bubble_studio.geometry import contour_box, rectangle
from tools.bubble_studio.native_ink_evidence import conflict, paper, preserved
from tools.bubble_studio.native_ink_graph import cut


def scene(joined=True):
    width, height = 900, 500
    image = Image.new("RGB", (width, height), "#6688aa")
    draw = ImageDraw.Draw(image)
    masks = []
    for x in (230, 650):
        mask = np.zeros((height, width), np.uint8)
        cv2.ellipse(mask, (x, 240), (120, 100), 0, 0, 360, 1, -1)
        masks.append(mask)
    whole = masks[0] | masks[1]
    if joined:
        cv2.rectangle(whole, (320, 200), (560, 280), 1, -1)
    rgb = np.asarray(image).copy()
    rgb[whole > 0] = 0
    rgb[cv2.erode(whole, np.ones((5, 5), np.uint8)) > 0] = 255
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image)
    bodies, anchors, diagnostics, checks = [], {}, [], []
    for i, (x, mask) in enumerate(zip((230, 650), masks), 1):
        identity = f"b{i}"
        region = contour_box(mask, (0, 0), width, height, 0.97)
        region.update(id=identity, order=i, panel_id="p1")
        bodies.append(region)
        bounds = [x - 60, 215, x + 60, 265]
        anchor = rectangle(bounds, width, height, 1, margin=0)
        anchors[identity] = {k: anchor[k] for k in ("x", "y", "w", "h")}
        diagnostics.append(
            dict(supporting_texts=[dict(box=bounds, label=1, score=0.97)])
        )
        draw.text((x - 45, 225), "HELLO WORLD", fill="black", stroke_width=1)
        bb = stage.pixel_box(region, image.size)
        word = [x - 50, 220, x + 50, 245]
        check = dict(
            region_id=identity,
            box=list(bb),
            uncertain=False,
            ocr=[
                dict(
                    text="HELLO WORLD",
                    score=0.99,
                    box=[
                        (word[0] - bb[0]) / (bb[2] - bb[0]),
                        (word[1] - bb[1]) / (bb[3] - bb[1]),
                        (word[2] - bb[0]) / (bb[2] - bb[0]),
                        (word[3] - bb[1]) / (bb[3] - bb[1]),
                    ],
                )
            ],
        )
        checks.append(check)
    doc = dict(
        result=dict(
            width=width,
            height=height,
            direction="rtl",
            layout="auto",
            confidence=0.97,
            panels=[dict(id="p1", x=0, y=0, w=1, h=1)],
            bubbles=bodies,
        ),
        analysis=dict(
            reading_anchors=anchors,
            balloons=diagnostics,
            text_check=dict(mode="review", regions=checks),
        ),
        review=dict(verified=False, flags=["Sprawdź b1 i b2"]),
    )
    target = contour_box(
        whole, (0, 0), width, height, 0.97, epsilon=0.1, max_vertices=2048
    )
    return image, doc, target


def test_graph_cut_requires_a_real_shared_paper_component():
    image, doc, _ = scene()
    texts = [t for b in doc["result"]["bubbles"] for t in stage._texts(image, doc, b)]
    answer = cut(image, (40, 60, 860, 440), texts)
    assert answer is not None
    region, _ = answer
    assert preserved(image, doc, doc["result"]["bubbles"], region) is not None
    separate, other, _ = scene(joined=False)
    assert cut(separate, (40, 60, 860, 440), texts) is None


def test_merge_preserves_both_texts_and_remaps_live_ids_at_first_lobe():
    image, doc, target = scene()
    result = stage.refine(
        image, doc, lambda *_: [dict(ids=["b1", "b2"], region=target)]
    )
    assert "native_ink_error" not in result["analysis"]
    assert len(result["result"]["bubbles"]) == 1
    body = result["result"]["bubbles"][0]
    assert (body["id"], body["order"], body["panel_id"]) == ("b1", 1, "p1")
    assert result["result"]["direction"] == "rtl"
    assert result["analysis"]["native_ink_refinement"]["mapping"] == {
        "b1": "b1",
        "b2": "b1",
    }
    assert len(result["analysis"]["text_check"]["regions"]) == 1
    assert len(result["analysis"]["text_check"]["regions"][0]["ocr"]) == 2
    assert "Sprawdź b1 i b1" in result["review"]["flags"]


def test_any_unassigned_owned_ocr_word_blocks_a_smaller_mask():
    image, doc, target = scene()
    source = doc["analysis"]["text_check"]["regions"][0]
    source["ocr"].append(dict(text="ORPHAN", score=0.99, box=[0.4, 0.75, 0.7, 0.9]))
    draw = ImageDraw.Draw(image)
    bb = source["box"]
    draw.text(
        (bb[0] + 0.4 * (bb[2] - bb[0]), bb[1] + 0.76 * (bb[3] - bb[1])),
        "ORPHAN",
        fill="black",
    )
    small = rectangle([170, 210, 290, 270], *image.size, 0.97, margin=0)
    assert preserved(image, doc, [doc["result"]["bubbles"][0]], small) is None


def test_blank_corners_of_a_multi_block_anchor_are_not_letter_ink():
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 30), "FIRST", fill="black")
    draw.text((270, 270), "SECOND", fill="black")
    other = dict(
        rectangle([25, 25, 345, 300], 400, 400, 0.97, "text", margin=0),
        id="b2",
        order=2,
        panel_id="p1",
    )
    texts = [
        dict(box=[25, 25, 95, 60], label=2, score=0.97),
        dict(box=[260, 260, 345, 300], label=2, score=0.97),
    ]
    doc = dict(
        result=dict(bubbles=[other]),
        analysis=dict(
            reading_anchors={"b2": {k: other[k] for k in ("x", "y", "w", "h")}},
            balloons=[dict(supporting_texts=texts)],
        ),
    )
    blank = rectangle([150, 150, 210, 210], 400, 400, 0.97, "text", margin=0)
    assert not conflict(blank, [], doc, image.size, image)
    words = rectangle([20, 20, 110, 70], 400, 400, 0.97, "text", margin=0)
    assert conflict(words, [], doc, image.size, image)


def test_free_text_rectangle_keeps_glyphs_without_tracing_the_panel():
    image, doc, _ = scene()
    mask = np.zeros((500, 900), np.uint8)
    cv2.fillPoly(
        mask,
        [
            np.array(
                [[50, 50], [450, 50], [450, 430], [310, 430], [310, 315], [50, 315]],
                np.int32,
            )
        ],
        1,
    )
    body = contour_box(mask, (0, 0), 900, 500, 0.97)
    body.update(id="b1", order=1, panel_id="p1")
    doc["result"]["bubbles"][0] = body
    doc["analysis"]["balloons"][0]["supporting_texts"][0]["label"] = 2
    before = copy.deepcopy(doc)
    result = stage.refine(image, doc, lambda *_: [])
    assert not result["result"]["bubbles"][0].get("polygons")
    assert len(result["result"]["bubbles"]) == 2
    assert (
        result["analysis"]["reading_anchors"] == before["analysis"]["reading_anchors"]
    )


def test_verified_page_never_runs_even_a_proposal_factory():
    image, doc, _ = scene()
    doc["review"]["verified"] = True
    before = copy.deepcopy(doc)

    def forbidden(*_):
        raise AssertionError("must not be called")

    assert stage.refine(image, doc, forbidden) == before


def test_failure_after_proposal_work_rolls_back_the_complete_page():
    image, doc, _ = scene()
    before = copy.deepcopy(doc)

    def broken(*_):
        doc["result"]["bubbles"].clear()
        raise RuntimeError("unavailable")

    result = stage.refine(image, doc, broken)
    assert result["result"] == before["result"]
    assert (
        result["analysis"]["reading_anchors"] == before["analysis"]["reading_anchors"]
    )
    assert result["analysis"]["native_ink_error"] == "RuntimeError"


def test_two_open_text_rectangles_cannot_establish_a_compound():
    image, doc, target = scene()
    for i, body in enumerate(doc["result"]["bubbles"]):
        rectangle_body = rectangle(
            stage.pixel_box(body, image.size), *image.size, 0.97, "text", margin=0
        )
        rectangle_body.update(id=body["id"], order=body["order"], panel_id="p1")
        doc["result"]["bubbles"][i] = rectangle_body
    before = copy.deepcopy(doc)
    assert (
        stage.refine(image, doc, lambda *_: [dict(ids=["b1", "b2"], region=target)])
        == before
    )


def test_texture_outside_text_blocks_is_not_a_flat_paper_enclosure():
    image, doc, target = scene()
    rgb = np.asarray(image).copy()
    for y in range(145, 330, 4):
        rgb[y, 120:340] = 100
    assert paper(Image.fromarray(rgb), doc, doc["result"]["bubbles"], target) is None


def test_small_art_patch_cannot_hide_in_a_high_whole_mask_paper_percentage():
    image, doc, target = scene()
    rgb = np.asarray(image).copy()
    rgb[160:180, 215:250] = 120
    replacement = rectangle([170, 215, 290, 265], *image.size, 0.97, "text", margin=0)
    replacement.update(id="b1", order=1, panel_id="p1")
    doc["result"]["bubbles"][0] = replacement
    assert paper(Image.fromarray(rgb), doc, doc["result"]["bubbles"], target) is None


def test_merge_retains_following_regions_and_rebases_their_live_metadata():
    image, doc, target = scene()
    third = dict(
        rectangle([760, 30, 840, 80], *image.size, 0.97, "text", margin=0),
        id="b3",
        order=3,
        panel_id="p1",
    )
    doc["result"]["bubbles"].append(third)
    doc["analysis"]["reading_anchors"]["b3"] = {
        k: third[k] for k in ("x", "y", "w", "h")
    }
    doc["analysis"]["text_check"]["regions"].append(
        dict(region_id="b3", box=[760, 30, 840, 80], ocr=[], uncertain=True)
    )
    doc["review"]["flags"].append("Sprawdź b3")
    result = stage.refine(
        image, doc, lambda *_: [dict(ids=["b1", "b2"], region=target)]
    )
    assert len(result["result"]["bubbles"]) == 2
    last = result["result"]["bubbles"][1]
    assert (last["id"], last["order"]) == ("b2", 2)
    assert all(last[k] == third[k] for k in ("x", "y", "w", "h"))
    assert result["analysis"]["text_check"]["regions"][1]["region_id"] == "b2"
    assert "Sprawdź b2" in result["review"]["flags"]


def test_a_merge_cannot_skip_an_intervening_reading_stop():
    image, doc, target = scene()
    last = doc["result"]["bubbles"][1]
    last.update(id="b3", order=3)
    doc["analysis"]["reading_anchors"]["b3"] = doc["analysis"]["reading_anchors"].pop(
        "b2"
    )
    doc["analysis"]["text_check"]["regions"][1]["region_id"] = "b3"
    middle = dict(
        rectangle([410, 30, 490, 85], *image.size, 0.97, "text", margin=0),
        id="b2",
        order=2,
        panel_id="p1",
    )
    doc["result"]["bubbles"].insert(1, middle)
    doc["analysis"]["reading_anchors"]["b2"] = {
        k: middle[k] for k in ("x", "y", "w", "h")
    }
    doc["analysis"]["text_check"]["regions"].insert(
        1, dict(region_id="b2", box=[410, 30, 490, 85], ocr=[], uncertain=True)
    )
    for direction in ("ltr", "rtl"):
        doc["result"]["direction"] = direction
        before = copy.deepcopy(doc)
        result = stage.refine(
            image,
            copy.deepcopy(doc),
            lambda *_: [dict(ids=["b1", "b3"], region=target)],
        )
        assert result == before
