"""Optional visible tail endpoints; never changes any reading geometry."""

import copy, json, math
import cv2, numpy as np
from .compound_guard import _texts
from .native_ink_evidence import text_boxes
from .textcheck import pixel_box


def endpoint(image, document, b):
    if (
        b.get("type") != "bubble"
        or b.get("group")
        or b.get("polarity") == "dark"
        or b.get("confidence", 0) < 0.75
    ):
        return None
    texts = _texts(image, document, b)
    if len(texts) != 1 or texts[0].get("label") != 1 or texts[0].get("score", 0) < 0.85:
        return None
    polys = b.get("polygons") or ([b["polygon"]] if b.get("polygon") else [])
    if len(polys) != 1 or len(polys[0]) < 12:
        return None
    raw = np.array(
        [
            [
                (b["x"] + p["x"] * b["w"]) * image.width,
                (b["y"] + p["y"] * b["h"]) * image.height,
            ]
            for p in polys[0]
        ],
        np.float32,
    )
    box = pixel_box(b, image.size)
    w, h = box[2] - box[0], box[3] - box[1]
    if min(w, h) < 24:
        return None
    # Two long straight borders can be a panel/caption edge around free text.
    # Such areas keep the ordinary zoom rather than an invented speech anchor.
    simple = cv2.approxPolyDP(raw.reshape(-1, 1, 2), min(w, h) * 0.012, True).reshape(
        -1, 2
    )
    long_edges = 0
    for first, second in zip(simple, np.roll(simple, -1, axis=0)):
        dx, dy = np.abs(first - second)
        if (dy <= min(w, h) * 0.015 and dx >= w * 0.55) or (
            dx <= min(w, h) * 0.015 and dy >= h * 0.55
        ):
            long_edges += 1
    if long_edges >= 2:
        return None

    scale = min(1, 400 / max(w, h))
    pad = 4
    pts = (raw - np.array(box[:2])) * scale + pad
    width, height = (
        math.ceil(w * scale) + pad * 2 + 1,
        math.ceil(h * scale) + pad * 2 + 1,
    )
    mask = np.zeros((height, width), np.uint8)
    cv2.fillPoly(mask, [np.round(pts).astype(np.int32)], 1)
    count = np.sum(mask)
    short = min(w, h) * scale
    words = text_boxes(image, document, b)
    glyph = np.zeros_like(mask)
    for a, c, aa, cc in words:
        cv2.rectangle(
            glyph,
            (round((a - box[0]) * scale) + pad, round((c - box[1]) * scale) + pad),
            (round((aa - box[0]) * scale) + pad, round((cc - box[1]) * scale) + pad),
            1,
            -1,
        )
    # Near-white simple speech bodies only; colored/dark and compound bodies
    # retain the existing reader behavior.
    rgb = np.asarray(
        image.crop(box).resize((width - pad * 2 - 1, height - pad * 2 - 1))
    )
    aligned = np.zeros((height, width, 3), np.uint8)
    aligned[pad : pad + rgb.shape[0], pad : pad + rgb.shape[1]] = rgb
    interior = cv2.erode(mask, np.ones((5, 5), np.uint8)) & (1 - glyph)
    sample = aligned[interior > 0]
    if (
        len(sample) < 30
        or np.min(np.median(sample, axis=0)) < 190
        or np.ptp(np.median(sample, axis=0)) > 25
    ):
        return None
    inside = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    records = []
    for fraction in (0.24, 0.32, 0.40):
        radius = max(2, short * fraction / 2)
        seed = (inside > radius).astype(np.uint8)
        if not np.any(seed):
            return None
        core = mask & (
            cv2.distanceTransform(1 - seed, cv2.DIST_L2, 5) <= radius
        ).astype(np.uint8)
        if np.sum(core) < count * 0.82:
            return None
        cs, _ = cv2.findContours(core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cs) != 1:
            return None
        hull = cv2.convexHull(cs[0])
        ar = cv2.contourArea(cs[0])
        if ar / max(1, cv2.contourArea(hull)) < 0.965:
            return None
        _, _, cw, ch = cv2.boundingRect(cs[0])
        if max(cw, ch) / max(1, min(cw, ch)) > 2.8:
            return None
        dist = cv2.distanceTransform(1 - core, cv2.DIST_L2, 5)
        frag = mask & (1 - core)
        _, ls, stats, _ = cv2.connectedComponentsWithStats(frag, 8)
        choices = []
        for j, (x, y, cw, ch, ar) in enumerate(stats[1:], 1):
            comp = ls == j
            reach = float(dist[comp].max())
            if ar < 8 or ar > count * 0.13 or reach < max(5, short * 0.075):
                continue
            if np.any(comp & (glyph > 0)):
                continue
            yy, xx = np.nonzero(comp)
            coords = np.column_stack((xx, yy)).astype(float)
            root = coords[dist[comp] < max(1, reach * 0.28)]
            if len(root) < 2:
                continue
            vertex_dist = np.array(
                [
                    dist[
                        int(np.clip(round(p[1]), 0, height - 1)),
                        int(np.clip(round(p[0]), 0, width - 1)),
                    ]
                    for p in pts
                ]
            )
            # The output is always an existing contour vertex, never an invented tail.
            possible = [
                n
                for n, p in enumerate(pts)
                if ls[
                    int(np.clip(round(p[1]), 0, height - 1)),
                    int(np.clip(round(p[0]), 0, width - 1)),
                ]
                == j
            ]
            if not possible:
                continue
            n = max(possible, key=lambda n: vertex_dist[n])
            tip = pts[n]
            axis = tip - root.mean(axis=0)
            length = np.linalg.norm(axis)
            if length < max(6, short * 0.10):
                continue
            axis /= length
            perp = np.array([-axis[1], axis[0]])
            along = (coords - root.mean(axis=0)) @ axis
            across = coords @ perp
            near = across[(along >= length * 0.10) & (along <= length * 0.40)]
            far = across[along >= length * 0.68]
            if len(near) < 3 or len(far) < 2:
                continue
            basewidth = float(near.max() - near.min() + 1)
            endwidth = float(far.max() - far.min() + 1)
            if endwidth > basewidth * 0.70 or length / basewidth < 1.15:
                continue
            choices.append(
                dict(
                    vertex=n,
                    reach=reach,
                    length=float(length),
                    area=int(ar),
                    taper=endwidth / basewidth,
                )
            )
        if len(choices) != 1:
            return None
        records.append(choices[0])
    if len({r["vertex"] for r in records}) != 1:
        return None
    n = records[0]["vertex"]
    tip = raw[n]

    # Both sides must form a tapered end, rather than a flat crop-edge corner.
    def side(direction):
        point = raw[n]
        length = 0.0
        j = n
        while length < max(4, min(w, h) * 0.035):
            k = (j + direction) % len(raw)
            length += float(np.linalg.norm(raw[k] - raw[j]))
            j = k
            if j == n:
                return None
        return raw[j] - point

    a, c = side(-1), side(1)
    if a is None or c is None:
        return None
    angle = math.degrees(
        math.acos(
            float(
                np.clip(
                    np.dot(a, c) / max(1e-9, np.linalg.norm(a) * np.linalg.norm(c)),
                    -1,
                    1,
                )
            )
        )
    )
    if angle > 75:
        return None
    return dict(
        x=float(b["x"] + polys[0][n]["x"] * b["w"]),
        y=float(b["y"] + polys[0][n]["y"] * b["h"]),
        confidence=0.95,
        kind="visible-outline",
    ), records


def annotate_tail_tips(image, document):
    """Add optional animation metadata; geometry, text and order are immutable."""
    if document.get("review", {}).get("verified"):
        return document
    candidate = copy.deepcopy(document)
    proposals = []
    try:
        for body in candidate["result"]["bubbles"]:
            if body.get("manual") or body.get("tail_tip"):
                continue
            found = endpoint(image, document, body)
            if found is None:
                continue
            point, proof = found
            body["tail_tip"] = point
            proposals.append(
                dict(
                    region_id=body["id"],
                    method="stable-visible-contour-endpoint",
                    evidence=proof,
                )
            )
        if not proposals:
            return document
        candidate["analysis"]["tail_tips"] = dict(
            method="optional-metadata-only",
            confidence_note="Shape evidence threshold, not a calibrated probability.",
            regions=proposals,
        )
        if (
            len(json.dumps(candidate, ensure_ascii=False).encode("utf8"))
            > 2 * 1024 * 1024
        ):
            return document
        return candidate
    except Exception:
        # Optional positioning must never make a readable page fail.
        return document
