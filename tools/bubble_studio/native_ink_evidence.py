"""Native word ownership, ink alignment and bounded-paper proofs."""

import cv2
import numpy as np

from .closed_body import raster
from .compound_guard import _texts
from .geometry import area, intersection, padded_box, contour_box
from .native_enclosures import frame_box
from .quality_guard import overlap_share
from .refinement import boundary_support
from .segmentation import ink_evidence
from .textcheck import pixel_box


def text_boxes(image, doc, b):
    rows = _texts(image, doc, b)
    if rows:
        return [r["box"] for r in rows]
    anchor = pixel_box(
        doc["analysis"].get("reading_anchors", {}).get(b["id"], b), image.size
    )
    check = next(
        (
            r
            for r in doc["analysis"].get("text_check", {}).get("regions", [])
            if r["region_id"] == b["id"]
        ),
        None,
    )
    found = []
    if check:
        x, y, xx, yy = check["box"]
        for row in check.get("ocr", []):
            if row.get("score", 0) < 0.75 or len(row.get("box", [])) != 4:
                continue
            a, c, aa, cc = row["box"]
            r = [
                x + a * (xx - x),
                y + c * (yy - y),
                x + aa * (xx - x),
                y + cc * (yy - y),
            ]
            if intersection(r, anchor) / max(1, area(r)) >= 0.5:
                found.append(r)
    return found or [list(anchor)]


def conflict(candidate, members, document, size, image):
    ids = {b["id"] for b in members}
    others = [b for b in document["result"]["bubbles"] if b["id"] not in ids]
    if any(
        overlap_share(candidate, b, *size) > 0.03 for b in others if b.get("polygons")
    ):
        return True
    roi = pixel_box(candidate, size)
    mask = raster(candidate, size, roi)
    crop = image.crop(roi)
    for b in others:
        for box in text_boxes(image, document, b):
            if not intersection(roi, box):
                continue
            # Boundaries can pass through blank parts of a text block, never its ink.
            evidence, reliable = ink_evidence(crop, [dict(box=box)], roi)
            if reliable:
                if np.any((evidence > 0) & (mask > 0)):
                    return True
            else:
                x, y, xx, yy = box
                a, c = max(0, int(x - roi[0])), max(0, int(y - roi[1]))
                aa, cc = (
                    min(mask.shape[1], int(np.ceil(xx - roi[0]))),
                    min(mask.shape[0], int(np.ceil(yy - roi[1]))),
                )
                if aa > a and cc > c and np.any(mask[c:cc, a:aa]):
                    return True
    return False


def owned(image, document, member):
    check = next(
        (
            r
            for r in document["analysis"].get("text_check", {}).get("regions", [])
            if r["region_id"] == member["id"]
        ),
        None,
    )
    if check is None:
        return []
    primary = [t["box"] for t in _texts(image, document, member)]
    other = [
        box
        for b in document["result"]["bubbles"]
        if b["id"] != member["id"]
        for box in text_boxes(image, document, b)
    ]
    ob = pixel_box(member, image.size)
    oldmask = raster(member, image.size, ob)
    x, y, xx, yy = check["box"]
    words = []
    for row in check.get("ocr", []):
        if (
            row.get("score", 0) < 0.75
            or len(row.get("box", [])) != 4
            or not row.get("text", "").strip()
        ):
            continue
        a, c, aa, cc = row["box"]
        box = [x + a * (xx - x), y + c * (yy - y), x + aa * (xx - x), y + cc * (yy - y)]
        inside = any(intersection(box, t) / max(1, area(box)) >= 0.5 for t in primary)
        if not inside and any(
            intersection(box, t) / max(1, area(box)) >= 0.5 for t in other
        ):
            continue
        if not inside:
            if not any(ch.isalnum() or ch in "?!？！.…" for ch in row["text"]):
                continue
            a, c = max(0, int(box[0] - ob[0])), max(0, int(box[1] - ob[1]))
            aa, cc = (
                min(oldmask.shape[1], int(np.ceil(box[2] - ob[0]))),
                min(oldmask.shape[0], int(np.ceil(box[3] - ob[1]))),
            )
            if aa <= a or cc <= c or np.mean(oldmask[c:cc, a:aa]) < 0.50:
                continue
        words.append(dict(row, box=box))
    return words


def preserved(image, document, members, target):
    tb = pixel_box(target, image.size)
    mask = raster(target, image.size, tb)
    crop = image.crop(tb)
    allwords = []
    for b in members:
        blocks = [t["box"] for t in _texts(image, document, b)]
        words = owned(image, document, b)
        allwords.extend(words)
        for box in blocks + [r["box"] for r in words]:
            if intersection(box, tb) / max(1, area(box)) < 0.995:
                return None
            ink, reliable = ink_evidence(crop, [dict(box=box)], tb)
            if reliable:
                if np.sum((ink > 0) & (mask > 0)) / max(1, np.sum(ink > 0)) < 0.995:
                    return None
            else:
                x, y, xx, yy = box
                dx, dy = (xx - x) * 0.12, (yy - y) * 0.12
                a, c = max(0, int(x + dx - tb[0])), max(0, int(y + dy - tb[1]))
                aa, cc = (
                    min(mask.shape[1], int(np.ceil(xx - dx - tb[0]))),
                    min(mask.shape[0], int(np.ceil(yy - dy - tb[1]))),
                )
                if aa <= a or cc <= c or np.mean(mask[c:cc, a:aa]) < 0.98:
                    return None
    seen = set()
    rows = []
    for row in allwords:
        x, y, xx, yy = row["box"]
        key = (row.get("text"), tuple(round(v, 2) for v in row["box"]))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            dict(
                row,
                box=[
                    (x - tb[0]) / (tb[2] - tb[0]),
                    (y - tb[1]) / (tb[3] - tb[1]),
                    (xx - tb[0]) / (tb[2] - tb[0]),
                    (yy - tb[1]) / (tb[3] - tb[1]),
                ],
            )
        )
    return dict(
        region_id=members[0]["id"],
        box=list(tb),
        ocr=rows,
        uncertain=not any(r.get("score", 0) >= 0.85 for r in rows),
    )


def align(image, region):
    box = pixel_box(region, image.size)
    r = max(3, min(10, round(min(image.size) * 0.0025)))
    roi = padded_box(box, *image.size, 0, minimum=r * 3 + 4)
    mask = raster(region, image.size, roi)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    inside = cv2.erode(mask, kernel)
    outside = 1 - cv2.dilate(mask, kernel)
    if not np.any(inside):
        return None
    markers = np.zeros(mask.shape, np.int32)
    markers[inside > 0] = 1
    markers[outside > 0] = 2
    rgb = np.asarray(image.crop(roi))
    cv2.watershed(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), markers)
    result = (markers == 1).astype(np.uint8)
    ridge = (markers == -1) & (cv2.dilate(result, np.ones((3, 3), np.uint8)) > 0)
    result[ridge] = 1
    # Watershed marks image edges as ridges; retain genuine page clipping.
    if roi[0] == 0:
        result[:, 0] = mask[:, 0]
    if roi[1] == 0:
        result[0] = mask[0]
    if roi[2] == image.width:
        result[:, -1] = mask[:, -1]
    if roi[3] == image.height:
        result[-1] = mask[-1]
    result = cv2.dilate(result, np.ones((3, 3), np.uint8))
    target = contour_box(
        result, roi, *image.size, region["confidence"], epsilon=0.1, max_vertices=2048
    )
    return target


def paper(image, document, members, region, check_local=True):
    texts = [t for b in members for t in _texts(image, document, b)]
    if not texts:
        return None
    box = pixel_box(region, image.size)
    roi = padded_box(box, *image.size, 0, minimum=10)
    crop = image.crop(roi)
    rgb = np.asarray(crop)
    mask = raster(region, image.size, roi)
    for t in texts:
        a, b, c, d = [int(round(v)) for v in t["box"]]
        x, y, xx, yy = a - roi[0], b - roi[1], c - roi[0], d - roi[1]
        if min(x, y) < 0 or xx > crop.width or yy > crop.height or xx <= x or yy <= y:
            return None
    # Text glyphs can dominate a tight detector box. Sample paper outside
    # individual text blocks instead of mistaking a bold letter for its background.
    wordmask = np.zeros(mask.shape, np.uint8)
    for text in texts:
        a, b, c, d = [int(round(v - o)) for v, o in zip(text["box"], roi[:2] * 2)]
        wordmask[max(0, b) : min(crop.height, d), max(0, a) : min(crop.width, c)] = 1
    interior = cv2.erode(mask, np.ones((5, 5), np.uint8))
    clean = (interior > 0) & (wordmask == 0)
    pixels = rgb[clean]
    if len(pixels) < max(100, 0.10 * np.sum(mask)):
        return None
    if not len(pixels):
        return None
    codes = pixels.astype(np.int32) // 16
    codes = codes[:, 0] * 256 + codes[:, 1] * 16 + codes[:, 2]
    v, n = np.unique(codes, return_counts=True)
    colour = np.median(pixels[codes == v[np.argmax(n)]], axis=0)
    similar = np.max(np.abs(rgb.astype(np.float32) - colour), axis=2)
    sample = (interior > 0) & (wordmask == 0)
    if np.sum(sample) < 100:
        return None
    share = float(np.mean(similar[sample] <= 32))
    if share < 0.97:
        return None
    # A small art leak can be invisible in the whole-mask percentage.
    # Inspect overlapping native tiles, away from the printed body border.
    margin = max(4, min(10, round(min(image.size) * 0.0025)))
    deep = cv2.erode(
        mask,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (margin * 2 + 1, margin * 2 + 1)),
    )
    local = (deep > 0) & (wordmask == 0)
    # Do not reinterpret intentional texture in retained source lobes.
    # The local veto applies to paper/art newly introduced by this proposal.
    for old in members:
        if old.get("polygons"):
            local &= raster(old, image.size, roi) == 0
    tile = max(20, min(40, round(min(image.size) * 0.01)))
    step = max(10, tile // 2)
    for y in range(0, crop.height, step):
        for x in range(0, crop.width, step):
            chosen = local[y : y + tile, x : x + tile]
            if np.sum(chosen) < max(64, tile * tile * 0.15):
                continue
            if (
                check_local
                and float(np.mean(similar[y : y + tile, x : x + tile][chosen] <= 32))
                < 0.90
            ):
                return None
    # A common paper path must stay inside the actual panel, not use the gutter.
    panelids = {b.get("panel_id") for b in members}
    frame = None
    if len(members) > 1:
        if len(panelids) != 1 or None in panelids:
            return None
        p = next(
            (
                p
                for p in document["result"]["panels"]
                if p["id"] == next(iter(panelids))
            ),
            None,
        )
        if p is None:
            return None
        frame = frame_box(image, p)
    connected = []
    for tolerance in [16, 32]:
        allowed = ((similar <= tolerance) & (mask > 0)).astype(np.uint8)
        if frame:
            clip = np.zeros_like(mask)
            x, y = max(0, frame[0] - roi[0]), max(0, frame[1] - roi[1])
            xx, yy = (
                min(crop.width, frame[2] - roi[0]),
                min(crop.height, frame[3] - roi[1]),
            )
            if xx <= x or yy <= y:
                return None
            clip[y:yy, x:xx] = 1
            allowed &= clip
        allowed = cv2.erode(allowed, np.ones((3, 3), np.uint8))
        _, labels = cv2.connectedComponents(allowed, 8)
        found = set()
        for text in texts:
            a, b, c, d = [int(round(v - o)) for v, o in zip(text["box"], roi[:2] * 2)]
            minimum = max(3, 0.02 * max(1, (c - a) * (d - b)))
            a, b, c, d = (
                max(0, a - 6),
                max(0, b - 6),
                min(crop.width, c + 6),
                min(crop.height, d + 6),
            )
            v, n = np.unique(labels[b:d, a:c], return_counts=True)
            good = [(count, int(k)) for k, count in zip(v, n) if k and count >= minimum]
            if not good:
                return None
            found.add(max(good)[1])
        if len(found) != 1:
            return None
        basin = float(np.sum(labels == next(iter(found))) / max(1, np.sum(allowed)))
        if basin < 0.90:
            return None
        connected.append(True)
    if not all(connected):
        return None
    return dict(
        paper_rgb=[float(c) for c in colour],
        paper_share=share,
        native_paper_connection_both_tolerances=True,
        connection_eroded_by=1,
        connection_inside_panel=bool(frame),
    )


def support(image, region):
    box = pixel_box(region, image.size)
    roi = padded_box(box, *image.size, 0, minimum=14)
    mask = raster(region, image.size, roi)
    return float(boundary_support(mask * 255, image.crop(roi)))


def added_support(image, document, members, region):
    box = pixel_box(region, image.size)
    oldboxes = [pixel_box(b, image.size) for b in members]
    box = [
        min([box[0]] + [b[0] for b in oldboxes]),
        min([box[1]] + [b[1] for b in oldboxes]),
        max([box[2]] + [b[2] for b in oldboxes]),
        max([box[3]] + [b[3] for b in oldboxes]),
    ]
    roi = padded_box(box, *image.size, 0, minimum=16)
    new = raster(region, image.size, roi)
    old = np.zeros_like(new)
    for b in members:
        if b.get("polygons"):
            old |= raster(b, image.size, roi)
    boundary = new - cv2.erode(new, np.ones((3, 3), np.uint8))
    oldboundary = old - cv2.erode(old, np.ones((3, 3), np.uint8))
    radius = max(3, min(10, round(min(image.size) * 0.0025)))
    halo = cv2.dilate(oldboundary, np.ones((2 * radius + 1, 2 * radius + 1), np.uint8))
    inserted = (boundary > 0) & (halo == 0)
    count = int(np.sum(inserted))
    gray = cv2.cvtColor(np.asarray(image.crop(roi)), cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 100)
    distance = cv2.distanceTransform((edges == 0).astype(np.uint8), cv2.DIST_L2, 5)
    score = float(np.mean(distance[inserted] <= 3)) if count else 1.0
    return dict(new_boundary_pixels=count, new_boundary_ink_support=score)


def trim_paper(image, document, members, region):
    """Rebuild the shared paper basin inside a graph-cut hypothesis.

    Raw paper from every primary text block must belong to one component
    before filling glyph holes. This removes halftone appendages without
    inventing an ellipse or discarding owned words; callers validate again.
    """
    proof = paper(image, document, members, region, check_local=False)
    if proof is None:
        return None
    from .geometry import _fill

    roi = padded_box(pixel_box(region, image.size), *image.size, 0, minimum=8)
    rgb = np.asarray(image.crop(roi)).astype(np.float32)
    mask = raster(region, image.size, roi)
    distance = np.max(np.abs(rgb - np.asarray(proof["paper_rgb"])), axis=2)
    allowed = ((distance <= 24) & (mask > 0)).astype(np.uint8)
    allowed = cv2.erode(allowed, np.ones((5, 5), np.uint8))
    _, labels = cv2.connectedComponents(allowed, 8)
    found = set()
    for body in members:
        for text in _texts(image, document, body):
            a, b, c, d = [int(round(v - o)) for v, o in zip(text["box"], roi[:2] * 2)]
            a, b, c, d = (
                max(0, a - 6),
                max(0, b - 6),
                min(mask.shape[1], c + 6),
                min(mask.shape[0], d + 6),
            )
            values, counts = np.unique(labels[b:d, a:c], return_counts=True)
            choices = [
                (count, int(k)) for k, count in zip(values, counts) if k and count >= 3
            ]
            if not choices:
                return None
            found.add(max(choices)[1])
    if len(found) != 1:
        return None
    chosen = (labels == next(iter(found))).astype(np.uint8)
    chosen = cv2.dilate(chosen, np.ones((7, 7), np.uint8)) & mask
    chosen = (_fill(chosen * 255) > 0).astype(np.uint8)
    target = contour_box(
        chosen, roi, *image.size, region["confidence"], epsilon=0.1, max_vertices=2048
    )
    if len(target.get("polygons", [])) != 1:
        return None
    return target
