"""Conservative rejection of repeated physical control buttons, with native evidence.

A circle or short OCR result alone never authorizes deletion. Require a regular
2-D array, several distinct straight-bar symbols and two nearby mechanical SFX
outside every reading region. All pre-filter reading data can be restored.
"""
import copy
import json
import math
import re

import cv2
import numpy as np

from .textcheck import pixel_box


def symbol(image, body):
    if body.get("type") != "bubble" or body.get("manual") or body.get("tail_tip"):
        return None
    polygons = body.get("polygons") or ([body["polygon"]] if body.get("polygon") else [])
    if len(polygons) != 1 or len(polygons[0]) < 10:
        return None
    box = pixel_box(body, image.size)
    w, h = box[2] - box[0], box[3] - box[1]
    if min(w, h) < 24 or max(w, h) > min(image.size) * .07 or not .9 <= w / h <= 1.1:
        return None
    vertices = np.array([[p["x"], p["y"]] for p in polygons[0]], float)
    radial = np.linalg.norm((vertices - .5) * 2, axis=1)
    if np.mean(np.abs(radial - 1)) > .08 or np.max(np.abs(radial - 1)) > .2:
        return None
    gray = np.asarray(image.crop(box).convert("L"))
    yy, xx = np.mgrid[:h, :w]
    interior = ((xx - (w - 1) / 2) / (w / 2)) ** 2 + ((yy - (h - 1) / 2) / (h / 2)) ** 2 < .64 ** 2
    ink = ((gray < 128) & interior).astype(np.uint8)
    if not .025 <= ink.sum() / (w * h) <= .13:
        return None
    length = max(3, round(min(w, h) * .21))
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((1, length), np.uint8))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((length, 1), np.uint8))
    covered = cv2.dilate(horizontal | vertical, np.ones((3, 3), np.uint8))
    coverage = float(np.count_nonzero(covered & ink) / max(1, ink.sum()))
    nh, nv = cv2.connectedComponents(horizontal)[0] - 1, cv2.connectedComponents(vertical)[0] - 1
    if coverage < .97 or (nh, nv) not in {(1, 0), (2, 0), (3, 0), (0, 1), (0, 2), (0, 3), (2, 1), (3, 1), (1, 2), (1, 3)}:
        return None
    return dict(region_id=body["id"], box=list(box), diameter=(w + h) / 2,
                center=[(box[0] + box[2]) / 2, (box[1] + box[3]) / 2],
                bars=[nh, nv], straight_ink_coverage=coverage)


def levels(values, tolerance):
    groups = []
    for value in sorted(values):
        if groups and abs(value - np.mean(groups[-1])) <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(np.mean(g)) for g in groups]


def arrays(image, document):
    groups = {}
    for body in document["result"]["bubbles"]:
        if not body.get("panel_id"):
            continue
        proof = symbol(image, body)
        if proof:
            groups.setdefault(body["panel_id"], []).append(proof)
    found = []
    for panel, group in groups.items():
        if not 4 <= len(group) <= 12:
            continue
        size = float(np.median([g["diameter"] for g in group]))
        if any(abs(g["diameter"] / size - 1) > .10 for g in group):
            continue
        xs, ys = [levels([g["center"][a] for g in group], size * .15) for a in (0, 1)]
        if not (2 <= len(xs) <= 4 and 3 <= len(ys) <= 6):
            continue
        gaps = [np.diff(v) for v in (xs, ys)]
        if any(np.any(g < size * 1.4) or np.any(g > size * 4) or (len(g) > 1 and max(g) / min(g) > 1.12) for g in gaps):
            continue
        cells = [(int(np.argmin(abs(np.array(xs) - g["center"][0]))), int(np.argmin(abs(np.array(ys) - g["center"][1])))) for g in group]
        if len(set(cells)) != len(cells) or max(sum(x == c[0] for x, y in cells) for c in cells) < 3 or max(sum(y == c[1] for x, y in cells) for c in cells) < 2:
            continue
        signatures = {tuple(g["bars"]) for g in group}
        if len(signatures) < 3 or sum(max(g["bars"]) >= 2 for g in group) < 2 or not any(min(g["bars"]) > 0 for g in group):
            continue
        found.append(dict(panel_id=panel, symbols=group, diameter=size, grid_x=xs, grid_y=ys))
    return found


def mechanical_context(rows, group, document):
    size = group["diameter"]
    x1 = min(g["box"][0] for g in group["symbols"]) - 2 * size
    y1 = min(g["box"][1] for g in group["symbols"]) - 2 * size
    x2 = max(g["box"][2] for g in group["symbols"]) + 2 * size
    y2 = max(g["box"][3] for g in group["symbols"]) + 2 * size
    page_size = (document["result"]["width"], document["result"]["height"])
    regions = [pixel_box(b, page_size) for b in document["result"]["bubbles"]]
    hits = []
    for row in rows:
        box = row.get("box", [])
        if len(box) != 4 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in box):
            continue
        if row.get("score", 0) < .98 or not re.fullmatch(r"(?:BEEP|BIP|PIP|BIEP)[!.,~ -]*", row.get("text", "").upper()):
            continue
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if not (x1 < cx < x2 and y1 < cy < y2 and .25 * size <= box[3] - box[1] <= 1.2 * size):
            continue
        if any(a <= cx <= c and b <= cy <= d for a, b, c, d in regions):
            continue
        if all(math.hypot(cx - p[0], cy - p[1]) > size for p in hits):
            hits.append((cx, cy))
    return hits if len(hits) >= 2 else []


def refine(image, document, checker):
    if document.get("review", {}).get("verified") or document.get("analysis", {}).get("control_buttons") or checker is None:
        return document
    try:
        groups = arrays(image, document)
        if not groups:
            return document
        rows = checker.locate_context(image)
        confirmed = []
        for group in groups:
            proof = mechanical_context(rows, group, document)
            if proof:
                confirmed.append(dict(group, mechanical_sfx_centers=proof))
        removed = {s["region_id"] for g in confirmed for s in g["symbols"]}
        if not removed:
            return document
        candidate = copy.deepcopy(document)
        analysis = candidate["analysis"]
        original = dict(result=copy.deepcopy(candidate["result"]), review=copy.deepcopy(candidate["review"]),
                        analysis_fields={k:copy.deepcopy(analysis[k]) for k in ("reading_anchors", "text_check", "tail_tips") if k in analysis})
        kept = [b for b in candidate["result"]["bubbles"] if b["id"] not in removed]
        mapping = {b["id"]: f"b{i+1}" for i, b in enumerate(kept)}
        for i, body in enumerate(kept):
            body["id"], body["order"] = f"b{i+1}", i + 1
        candidate["result"]["bubbles"] = kept
        candidate["result"]["confidence"] = sum(b["confidence"] for b in kept) / max(1, len(kept))
        if "reading_anchors" in analysis:
            analysis["reading_anchors"] = {mapping[k]: v for k, v in analysis["reading_anchors"].items() if k in mapping}
        for key, field in (("text_check", "region_id"), ("tail_tips", "region_id")):
            if key in analysis:
                analysis[key]["regions"] = [dict(row, **{field:mapping[row[field]]}) for row in analysis[key].get("regions", []) if row.get(field) in mapping]
        flags = []
        for flag in candidate["review"].get("flags", []):
            if any(k in removed for k in re.findall(r"\bb\d+\b", flag)):
                continue
            flags.append(re.sub(r"\bb\d+\b", lambda m: mapping.get(m[0], m[0]), flag))
        candidate["review"]["flags"] = flags
        analysis["control_buttons"] = dict(method="native-bar-symbol-array-with-mechanical-context", removed_region_ids=sorted(removed),
            preserved_id_mapping=mapping, evidence=confirmed, original=original)
        if len(json.dumps(candidate, ensure_ascii=False, allow_nan=False).encode("utf8")) > 2 * 1024 * 1024:
            return document
        return candidate
    except Exception:
        return document


def restore(document):
    audit = document.get("analysis", {}).get("control_buttons", {})
    if audit.get("status") == "restored" or not audit.get("original"):
        return False
    original = copy.deepcopy(audit["original"])
    document["result"] = original["result"]
    document["review"] = original["review"]
    for key in ("reading_anchors", "text_check", "tail_tips"):
        document["analysis"].pop(key, None)
    document["analysis"].update(original["analysis_fields"])
    audit["status"] = "restored"
    return True
