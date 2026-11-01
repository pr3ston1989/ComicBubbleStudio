"""Repair native enclosures and free text with independent pixel evidence.

No language-model verdict, page identity or reference annotation participates
in proposal selection. Existing reading order is retained at the first lobe.
"""

import copy
import itertools
import json
import math
import re

import cv2
import numpy as np

from .closed_body import raster, own_ocr, closed_body_proof
from .compound_guard import _texts
from .geometry import area, rectangle
from .native_enclosures import frame_box
from .native_ink_evidence import (
    added_support,
    align,
    conflict,
    owned,
    paper,
    preserved,
    support,
    text_boxes,
    trim_paper,
)
from .native_ink_graph import cut, roi_for
from .segmentation import ink_evidence
from .textcheck import pixel_box


def eligible_sets(image, document):
    """One body or neighbouring parts in the same detected panel."""
    eligible = []
    for body in document["result"]["bubbles"]:
        texts = _texts(image, document, body)
        if (
            texts
            and all(t["label"] == 1 and t["score"] >= 0.85 for t in texts)
            and own_ocr(document, body, image.size) is not None
        ):
            eligible.append(body)
    sets = [(b["id"],) for b in eligible]
    for a, b in itertools.combinations(eligible, 2):
        if a.get("panel_id") is None or a.get("panel_id") != b.get("panel_id"):
            continue
        if abs(a["order"] - b["order"]) > 4:
            continue
        ab, bb = pixel_box(a, image.size), pixel_box(b, image.size)
        dx = max(0, max(ab[0], bb[0]) - min(ab[2], bb[2]))
        dy = max(0, max(ab[1], bb[1]) - min(ab[3], bb[3]))
        scale = min(ab[2] - ab[0], ab[3] - ab[1], bb[2] - bb[0], bb[3] - bb[1])
        if math.hypot(dx, dy) <= max(12, 0.5 * scale):
            sets.append(tuple(sorted((a["id"], b["id"]))))
    return sorted(set(sets))


def included_blocks(image, document, region, eligible):
    """A mask may recruit complete text blocks; partial words reject it."""
    box = pixel_box(region, image.size)
    mask = raster(region, image.size, box)
    crop = image.crop(box)
    included = []
    for body in document["result"]["bubbles"]:
        coverages = []
        for word in text_boxes(image, document, body):
            if (
                word[0] < box[0]
                or word[1] < box[1]
                or word[2] > box[2]
                or word[3] > box[3]
            ):
                x, y, xx, yy = word
                a, c = max(0, int(x - box[0])), max(0, int(y - box[1]))
                aa = min(mask.shape[1], int(math.ceil(xx - box[0])))
                cc = min(mask.shape[0], int(math.ceil(yy - box[1])))
                coverages.append(
                    0.5 if aa > a and cc > c and np.any(mask[c:cc, a:aa]) else 0.0
                )
                continue
            evidence, reliable = ink_evidence(crop, [dict(box=word)], box)
            if reliable:
                coverages.append(float(np.mean(mask[evidence > 0])))
            else:
                x, y, xx, yy = [int(round(v - o)) for v, o in zip(word, box[:2] * 2)]
                coverages.append(
                    float(np.mean(mask[y:yy, x:xx])) if xx > x and yy > y else 0.0
                )
        if coverages and max(coverages) > 0.001:
            if min(coverages) < 0.995 or body["id"] not in eligible:
                return None
            included.append(body["id"])
    return included


def proposals(image, document):
    bodies = document["result"]["bubbles"]
    lookup = {b["id"]: b for b in bodies}
    eligible = {
        b["id"]
        for b in bodies
        if (ts := _texts(image, document, b))
        and all(t["label"] == 1 and t["score"] >= 0.85 for t in ts)
    }
    result = []
    for ids in eligible_sets(image, document):
        members = [lookup[k] for k in ids]
        if (
            len(ids) == 1
            and members[0].get("polygons")
            and support(image, members[0]) >= 0.85
            and paper(image, document, members, members[0]) is not None
        ):
            continue
        texts = [t for b in members for t in _texts(image, document, b)]
        roi = roi_for(image, document, members)
        for weight, texture_cap in itertools.product((1, 4), (64, 4096)):
            answer = cut(image, roi, texts, weight, texture_cap=texture_cap)
            if answer is None:
                continue
            region, audit = answer
            region["confidence"] = min(b["confidence"] for b in members)
            region = align(image, region)
            if region is None:
                continue
            included = included_blocks(image, document, region, eligible)
            if included is None or not set(ids) <= set(included):
                continue
            recruited = [lookup[k] for k in included]
            proof = paper(image, document, recruited, region, check_local=False)
            if proof is None or support(image, region) < 0.85:
                continue
            result.append(dict(ids=included, region=region, audit=audit))
    return result


def frame_spill(image, document, old, target):
    """A second paper colour alone never proves an old shape is defective."""
    if closed_body_proof(image, document, old, target) is not None:
        return True
    bb = pixel_box(old, image.size)
    mask = raster(old, image.size, bb)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False
    hull = cv2.convexHull(np.concatenate(contours))
    solidity = float(np.sum(mask) / max(1, cv2.contourArea(hull)))
    panel = next(
        (p for p in document["result"]["panels"] if p["id"] == old.get("panel_id")),
        None,
    )
    if panel is None:
        return False
    frame = frame_box(image, panel)
    edges = sum(
        abs(a - c) <= length * 0.03
        for a, c, length in zip(
            bb, frame, (frame[2] - frame[0], frame[3] - frame[1]) * 2
        )
    )
    target_area = np.sum(raster(target, image.size, pixel_box(target, image.size)))
    return bool(solidity < 0.85 and edges >= 2 and target_area < 0.65 * np.sum(mask))


def select(image, document, records):
    lookup = {b["id"]: b for b in document["result"]["bubbles"]}
    candidates = []
    expanded = []
    for record in records:
        expanded.append(record)
        members = [lookup[k] for k in record["ids"]]
        source = record.get("region", record.get("aligned_region"))
        trimmed = trim_paper(image, document, members, source)
        if trimmed is not None:
            expanded.append(dict(record, region=trimmed, paper_trimmed=True))
    for record in expanded:
        members = sorted([lookup[k] for k in record["ids"]], key=lambda b: b["order"])
        target = copy.deepcopy(record.get("region", record.get("aligned_region")))
        proof = paper(image, document, members, target)
        if proof is None:
            continue
        quality = support(image, target)
        added = added_support(image, document, members, target)
        if quality < 0.90 or added["new_boundary_ink_support"] < 0.85:
            continue
        if len(members) == 1:
            old = members[0]
            if old.get("polygons") and not frame_spill(image, document, old, target):
                continue
            reason = "native-enclosure-for-text-rectangle-or-frame-spill"
        else:
            # A shared shape cannot justify skipping an intervening stop.
            # Keep separate reading steps when another voice is interleaved.
            orders = [b["order"] for b in members]
            if orders != list(range(orders[0], orders[-1] + 1)):
                continue
            # Open background connecting text rectangles is not a balloon.
            if not any(b.get("polygons") for b in members):
                continue
            reason = "one-native-paper-enclosure-for-all-text-blocks"
        target.update(
            confidence=min(b["confidence"] for b in members),
            id=members[0]["id"],
            order=members[0]["order"],
            panel_id=members[0].get("panel_id"),
        )
        # A clipped balloon can meet a frame, but a new mask must not
        # spread into a neighbouring panel or gutter beyond the old shape.
        panel = next(
            (
                p
                for p in document["result"]["panels"]
                if p["id"] == members[0].get("panel_id")
            ),
            None,
        )
        if panel is None:
            continue
        frame = frame_box(image, panel)
        detected = pixel_box(panel, image.size)
        frame = (
            max(frame[0], detected[0]),
            max(frame[1], detected[1]),
            min(frame[2], detected[2]),
            min(frame[3], detected[3]),
        )
        tb = pixel_box(target, image.size)
        if any(
            new < bound - 3
            and new < min(pixel_box(b, image.size)[axis] for b in members) - 3
            for axis, new, bound in [(0, tb[0], frame[0]), (1, tb[1], frame[1])]
        ):
            continue
        if any(
            new > bound + 3
            and new > max(pixel_box(b, image.size)[axis] for b in members) + 3
            for axis, new, bound in [(2, tb[2], frame[2]), (3, tb[3], frame[3])]
        ):
            continue
        if conflict(target, members, document, image.size, image):
            continue
        check = preserved(image, document, members, target)
        if check is None:
            continue
        candidates.append(
            dict(
                ids=[b["id"] for b in members],
                target=target,
                native_check=check,
                reason=reason,
                score=quality + 0.15 * added["new_boundary_ink_support"],
                proof=proof,
                boundary_support=quality,
                added_boundary=added,
            )
        )
    for body in document["result"]["bubbles"]:
        texts = _texts(image, document, body)
        if (
            not body.get("polygons")
            or not texts
            or not all(t["label"] == 2 and t["score"] >= 0.85 for t in texts)
        ):
            continue
        box = pixel_box(body, image.size)
        mask = raster(body, image.size, box)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        hull = cv2.convexHull(np.concatenate(contours))
        solidity = float(np.sum(mask) / max(1, cv2.contourArea(hull)))
        if solidity >= 0.93:
            continue
        boxes = [t["box"] for t in texts] + [
            r["box"] for r in owned(image, document, body)
        ]
        bounds = [
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        ]
        target = rectangle(bounds, *image.size, body["confidence"], "text", margin=6)
        target.update(id=body["id"], order=body["order"], panel_id=body.get("panel_id"))
        if area(pixel_box(target, image.size)) >= 0.65 * np.sum(mask):
            continue
        if conflict(target, [body], document, image.size, image):
            continue
        check = preserved(image, document, [body], target)
        if check is not None:
            candidates.append(
                dict(
                    ids=[body["id"]],
                    target=target,
                    native_check=check,
                    reason="confident-free-text-with-oversized-noncompact-mask",
                    score=2.0,
                    proof=dict(old_solidity=solidity),
                )
            )
    selected, used = [], set()
    for candidate in sorted(candidates, key=lambda r: r["score"], reverse=True):
        if used.intersection(candidate["ids"]):
            continue
        selected.append(candidate)
        used.update(candidate["ids"])
    return selected


def apply(image, document, selected):
    """Remap all live metadata; historical diagnostics retain their own mapping."""
    if not selected:
        return document
    original = copy.deepcopy(document)
    bodies = document["result"]["bubbles"]
    by_id = {b["id"]: b for b in bodies}
    replacements = {r["ids"][0]: r for r in selected}
    removed = {i for r in selected for i in r["ids"][1:]}
    proposed, anchors, texts = [], {}, []
    saved = document["analysis"].get("reading_anchors", {})
    for body in bodies:
        if body["id"] in removed:
            continue
        record = replacements.get(body["id"])
        proposed.append(copy.deepcopy(record["target"] if record else body))
        if record and len(record["ids"]) > 1:
            supports = [
                t for k in record["ids"] for t in _texts(image, document, by_id[k])
            ]
            bounds = [
                min(t["box"][0] for t in supports),
                min(t["box"][1] for t in supports),
                max(t["box"][2] for t in supports),
                max(t["box"][3] for t in supports),
            ]
            a = rectangle(bounds, *image.size, 1, margin=0)
            anchors[body["id"]] = {k: a[k] for k in ("x", "y", "w", "h")}
            texts.append(
                dict(
                    method="native-ink-connected-body",
                    supporting_texts=supports,
                    detection_box=list(pixel_box(record["target"], image.size)),
                )
            )
        else:
            anchors[body["id"]] = copy.deepcopy(saved[body["id"]])
    if sum(len(p) for b in proposed for p in b.get("polygons", [])) > 32000:
        return original
    mapping = {b["id"]: f"b{i + 1}" for i, b in enumerate(proposed)}
    first = {k: r["ids"][0] for r in selected for k in r["ids"]}
    full_mapping = {b["id"]: mapping[first.get(b["id"], b["id"])] for b in bodies}
    checks = document["analysis"].get("text_check", {}).get("regions", [])
    live_checks = []
    for check in checks:
        identity = check["region_id"]
        if identity in removed:
            continue
        row = copy.deepcopy(
            replacements[identity]["native_check"]
            if identity in replacements
            else check
        )
        row["region_id"] = full_mapping[identity]
        live_checks.append(row)
    if any(r["ids"][0] not in {c["region_id"] for c in checks} for r in selected):
        return original
    changes = []
    for record in selected:
        changes.append(
            {
                k: copy.deepcopy(v)
                for k, v in record.items()
                if k not in {"target", "native_check", "score"}
            }
            | dict(
                original_regions=[copy.deepcopy(by_id[k]) for k in record["ids"]],
                original_text_checks=[
                    copy.deepcopy(c) for c in checks if c["region_id"] in record["ids"]
                ],
            )
        )
    for i, body in enumerate(proposed):
        body.update(id=f"b{i + 1}", order=i + 1)
    document["result"]["bubbles"] = proposed
    document["result"]["confidence"] = sum(b["confidence"] for b in proposed) / max(
        1, len(proposed)
    )
    document["analysis"]["reading_anchors"] = {
        mapping[k]: v for k, v in anchors.items()
    }
    document["analysis"].setdefault("balloons", []).extend(texts)
    document["analysis"].setdefault("text_check", {})["regions"] = live_checks
    flags = document["review"].get("flags", [])
    document["review"]["flags"] = [
        re.sub(r"\bb\d+\b", lambda m: full_mapping.get(m[0], m[0]), s) for s in flags
    ]
    document["review"]["flags"].append(
        "Dopasowano obszary do tuszu i tekstu; połączone części zachowują kolejność pierwszej części"
    )
    document["analysis"]["native_ink_refinement"] = dict(
        changes=changes, mapping=full_mapping
    )
    if len(json.dumps(document, ensure_ascii=False).encode("utf8")) > 2 * 1024 * 1024:
        return original
    return document


def refine(image, document, proposal_factory=None):
    """Any failed proof or exception retains the entire preceding page result."""
    if document.get("review", {}).get("verified"):
        return document
    original = copy.deepcopy(document)
    try:
        records = (proposal_factory or proposals)(image, document)
        return apply(image, document, select(image, document, records))
    except Exception as error:
        original["analysis"]["native_ink_error"] = type(error).__name__
        original["review"]["flags"].append(
            "Dodatkowa analiza tuszu była niedostępna; zachowano poprzedni wynik"
        )
        return original
