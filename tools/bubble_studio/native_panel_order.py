"""Recover reading order when native frame borders disprove panel fragments."""

import copy
import json
import math
import re

import cv2
import numpy as np

from .native_ink_evidence import text_boxes
from web.backend.comic_smartview_layout import order_boxes_by_cuts


def panel_frames(image):
    scale = min(1, 1600 / image.height, 1200 / image.width)
    im = image.resize((round(image.width * scale), round(image.height * scale)))
    rgb = np.asarray(im)
    h, w = rgb.shape[:2]
    sets = []
    for threshold in (220, 245):
        fg = (np.min(rgb, axis=2) < threshold).astype(np.uint8)
        cs, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid = []
        for c in cs:
            ar = cv2.contourArea(c)
            if not 0.04 * w * h < ar < 0.92 * w * h:
                continue
            poly = cv2.approxPolyDP(c, 0.015 * cv2.arcLength(c, True), True)
            if len(poly) != 4 or not cv2.isContourConvex(poly):
                continue
            solidity = ar / max(1, cv2.contourArea(poly))
            if not 0.94 < solidity < 1.06:
                continue
            pts = poly.reshape(-1, 2).astype(float)
            angles = []
            for i in range(4):
                a, b = pts[(i - 1) % 4] - pts[i], pts[(i + 1) % 4] - pts[i]
                angles.append(
                    math.degrees(
                        math.acos(
                            np.clip(
                                np.dot(a, b)
                                / max(1, np.linalg.norm(a) * np.linalg.norm(b)),
                                -1,
                                1,
                            )
                        )
                    )
                )
            if min(angles) < 45 or max(angles) > 135:
                continue
            poly = pts / np.array([w, h])
            valid.append(dict(poly=poly.tolist(), area=ar / (w * h), solidity=solidity))
        sets.append(valid)
    result = []
    for a in sets[0]:
        best = None
        for b in sets[1]:
            pa = np.asarray(a["poly"], np.float32)
            pb = np.asarray(b["poly"], np.float32)
            hit, _ = cv2.intersectConvexConvex(pa, pb)
            union = cv2.contourArea(pa) + cv2.contourArea(pb) - hit
            iou = hit / max(1e-9, union)
            if iou >= 0.985 and (best is None or iou > best[0]):
                best = (iou, b)
        if best is None:
            continue
        poly = np.asarray(a["poly"])
        x, y = poly.min(axis=0)
        xx, yy = poly.max(axis=0)
        result.append(
            dict(
                a,
                x=float(x),
                y=float(y),
                w=float(xx - x),
                h=float(yy - y),
                stability=best[0],
            )
        )
    return result


def frame_contains(frame, box, size=None):
    if size:
        box = [v / s for v, s in zip(box, (size[0], size[1], size[0], size[1]))]
    x, y, xx, yy = box
    poly = np.asarray(frame["poly"], np.float32)
    return all(
        cv2.pointPolygonTest(poly, (float(a), float(b)), False) >= 0
        for a, b in [(x, y), (xx, y), (xx, yy), (x, yy), ((x + xx) / 2, (y + yy) / 2)]
    )


def propose_order(image, d):
    if (
        d.get("review", {}).get("verified")
        or d["analysis"].get("strip_reading")
        or d["result"].get("layout") not in {"auto", "rows", None}
    ):
        return None
    fs = panel_frames(image)
    if len(fs) < 2:
        return None
    for n, f in enumerate(fs):
        f["id"] = f"n{n}"
        f["model_centres"] = []
    for p in d["result"]["panels"]:
        if p.get("confidence", 0) < 0.5:
            continue
        point = [p["x"] + p["w"] / 2, p["y"] + p["h"] / 2] * 2
        possible = [f for f in fs if frame_contains(f, point)]
        if len(possible) == 1:
            possible[0]["model_centres"].append(p["id"])
    if not any(len(f["model_centres"]) >= 2 for f in fs):
        return None
    # Native frames replace all model fragments whose centres share that frame.
    # Keep the remaining detected panels; incomplete native frame evidence must
    # not leave their dialogue fixed between the parts of a corrected panel.
    model_to_native = {pid: f["id"] for f in fs for pid in f["model_centres"]}
    hybrid = [f for f in fs if f["model_centres"]]
    for p in d["result"]["panels"]:
        if p["id"] not in model_to_native:
            hybrid.append(
                dict(
                    p,
                    poly=[
                        [p["x"], p["y"]],
                        [p["x"] + p["w"], p["y"]],
                        [p["x"] + p["w"], p["y"] + p["h"]],
                        [p["x"], p["y"] + p["h"]],
                    ],
                    model_centres=[p["id"]],
                    native=False,
                )
            )
    lookup = {f["id"]: f for f in hybrid}
    assigned = {}
    byframe = {}
    for body in d["result"]["bubbles"]:
        words = text_boxes(image, d, body)
        pid = body.get("panel_id")
        identity = model_to_native.get(pid, pid)
        if identity not in lookup or not all(
            frame_contains(lookup[identity], box, image.size) for box in words
        ):
            possible = [
                f
                for f in hybrid
                if all(frame_contains(f, box, image.size) for box in words)
            ]
            if len(possible) != 1:
                return None
            identity = possible[0]["id"]
        assigned[body["id"]] = identity
        byframe.setdefault(identity, []).append(body["id"])
    if not any(
        len(f["model_centres"]) >= 2 and len(byframe.get(f["id"], [])) >= 2 for f in fs
    ):
        return None
    ordered = order_boxes_by_cuts(
        hybrid, d["result"]["direction"], image.height / image.width, "rows"
    )
    output = [i for f in ordered for i in byframe.get(f["id"], [])]
    if len(output) != len(d["result"]["bubbles"]):
        return None
    if output == [b["id"] for b in d["result"]["bubbles"]]:
        return None
    return dict(ids=output, frames=fs, ownership=assigned)


def refine(image, document):
    if document.get("review", {}).get("verified"):
        return document
    original = copy.deepcopy(document)
    try:
        proposal = propose_order(image, document)
        if proposal is None:
            return document
        bodies = document["result"]["bubbles"]
        lookup = {b["id"]: b for b in bodies}
        order = proposal["ids"]
        if len(order) != len(bodies) or set(order) != set(lookup):
            return original
        mapping = {identity: f"b{index + 1}" for index, identity in enumerate(order)}
        anchors = document["analysis"].get("reading_anchors", {})
        if set(anchors) != set(lookup):
            return original
        document["result"]["bubbles"] = [lookup[k] for k in order]
        for index, body in enumerate(document["result"]["bubbles"]):
            body.update(id=f"b{index + 1}", order=index + 1)
        document["analysis"]["reading_anchors"] = {
            mapping[k]: v for k, v in anchors.items()
        }
        for row in document["analysis"].get("text_check", {}).get("regions", []):
            row["region_id"] = mapping[row["region_id"]]
        document["review"]["flags"] = [
            re.sub(r"\bb\d+\b", lambda m: mapping.get(m[0], m[0]), s)
            for s in document["review"].get("flags", [])
        ]
        document["analysis"]["native_panel_order"] = dict(
            mapping=mapping,
            original_order=[b["id"] for b in original["result"]["bubbles"]],
            native_frames=proposal["frames"],
            ownership=proposal["ownership"],
            method="stable-native-quadrilateral-frame-replaces-oversegmented-panel-fragments",
        )
        document["review"]["flags"].append(
            "Kolejność oparto na pełnej ramce kadru; zachowano wszystkie kwestie i ich obrysy"
        )
        if (
            len(json.dumps(document, ensure_ascii=False).encode("utf8"))
            > 2 * 1024 * 1024
        ):
            return original
        return document
    except Exception as error:
        original["analysis"]["native_panel_order_error"] = type(error).__name__
        original["review"]["flags"].append(
            "Dodatkowa kontrola kadrów była niedostępna; zachowano poprzednią kolejność"
        )
        return original
