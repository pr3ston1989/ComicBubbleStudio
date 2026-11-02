"""Respect stable full-width native frames after uncertain model-free grouping.

Only vertically disjoint frames backed by two ink thresholds can constrain an
outside balloon. Local dialogue order, geometry and all detections are retained.
"""

import copy
import heapq
import json
import re

from .native_ink_evidence import text_boxes
from .native_panel_order import frame_contains, panel_frames


def propose(im, d):
    r = d["result"]
    bs = r["bubbles"]
    if (
        len(bs) < 4
        or d.get("review", {}).get("verified")
        or any(b.get("manual") for b in bs)
        or r.get("layout") != "auto"
        or r.get("direction") not in {"ltr", "rtl"}
        or r.get("panels")
        or d["analysis"].get("reading_mode") == "four_panel_strips"
        or d["analysis"].get("strip_reading")
        or d["analysis"].get("framed_strip_order")
        or d["analysis"]
        .get("scene_gutter_order", {})
        .get("classification", {})
        .get("all_physical_panel_gutters")
        is not True
        or set(d["analysis"].get("reading_anchors", {})) != {b["id"] for b in bs}
    ):
        return None
    fs = [f for f in panel_frames(im) if f["w"] >= 0.6]
    if len(fs) < 2:
        return None
    # Each native frame must be wide, vertically disjoint, similarly aligned.
    fs.sort(key=lambda f: f["y"])
    if (
        any(a["y"] + a["h"] > b["y"] for a, b in zip(fs, fs[1:]))
        or max(f["x"] for f in fs) - min(f["x"] for f in fs) > 0.025
        or max(f["x"] + f["w"] for f in fs) - min(f["x"] + f["w"] for f in fs) > 0.025
    ):
        return None
    words = {b["id"]: text_boxes(im, d, b) for b in bs}
    bounds = {b["id"]: [b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]] for b in bs}
    groups = []
    for f in fs:
        members = [
            b["id"]
            for b in bs
            if all(frame_contains(f, w, im.size) for w in words[b["id"]])
            and f["x"] - 0.01 <= bounds[b["id"]][0]
            and bounds[b["id"]][2] <= f["x"] + f["w"] + 0.01
            and f["y"] - 0.01 <= bounds[b["id"]][1]
            and bounds[b["id"]][3] <= f["y"] + f["h"] + 0.01
        ]
        if not members:
            return None
        # A caption or tail crossing a native border makes scene ownership
        # ambiguous. Do not move other balloons around that unresolved region.
        for body in bs:
            if body["id"] in members:
                continue
            x, y, xx, yy = bounds[body["id"]]
            if min(xx, f["x"] + f["w"]) > max(x, f["x"]) and min(
                yy, f["y"] + f["h"]
            ) > max(y, f["y"]):
                return None
        groups.append(members)
    if not any(len(g) >= 2 for g in groups):
        return None
    if len({i for g in groups for i in g}) != sum(map(len, groups)):
        return None
    ids = [b["id"] for b in bs]
    rank = {v: n for n, v in enumerate(ids)}
    edges = {v: set() for v in ids}
    for f, group in zip(fs, groups):
        # Preserve local dialogue order within this physical frame.
        for a, b in zip(group, group[1:]):
            edges[a].add(b)
        for body in bs:
            k = body["id"]
            if k in group:
                continue
            x, y, xx, yy = bounds[k]
            if not (f["x"] <= x < xx <= f["x"] + f["w"]):
                continue
            if yy < f["y"]:
                for v in group:
                    edges[k].add(v)
            elif y > f["y"] + f["h"]:
                for v in group:
                    edges[v].add(k)
    degree = {v: 0 for v in ids}
    for a, vs in edges.items():
        for b in vs:
            degree[b] += 1
    queue = [(rank[v], v) for v in ids if degree[v] == 0]
    heapq.heapify(queue)
    out = []
    while queue:
        _, v = heapq.heappop(queue)
        out.append(v)
        for b in edges[v]:
            degree[b] -= 1
            if degree[b] == 0:
                heapq.heappush(queue, (rank[b], b))
    if len(out) != len(ids) or out == ids:
        return None
    return dict(ids=out, frames=fs, groups=groups)


def refine(image, document):
    if document.get("analysis", {}).get("native_wide_frame_order"):
        return document
    try:
        proposal = propose(image, document)
        if proposal is None:
            return document
        candidate = copy.deepcopy(document)
        analysis = candidate["analysis"]
        fields = ("reading_anchors", "text_check", "tail_tips")
        original = dict(
            result=copy.deepcopy(candidate["result"]),
            review=copy.deepcopy(candidate["review"]),
            analysis_fields={
                k: copy.deepcopy(analysis[k]) for k in fields if k in analysis
            },
        )
        bodies = {b["id"]: b for b in candidate["result"]["bubbles"]}
        order = proposal["ids"]
        if len(order) != len(bodies) or set(order) != set(bodies):
            return document
        mapping = {identity: f"b{n + 1}" for n, identity in enumerate(order)}
        candidate["result"]["bubbles"] = [bodies[k] for k in order]
        for n, body in enumerate(candidate["result"]["bubbles"]):
            body.update(id=f"b{n + 1}", order=n + 1)
        analysis["reading_anchors"] = {
            mapping[k]: v for k, v in analysis["reading_anchors"].items()
        }
        for name in ("text_check", "tail_tips"):
            for row in analysis.get(name, {}).get("regions", []):
                row["region_id"] = mapping[row["region_id"]]
        candidate["review"]["flags"] = [
            re.sub(r"\bb\d+\b", lambda m: mapping.get(m[0], m[0]), flag)
            for flag in candidate["review"].get("flags", [])
        ]
        analysis["native_wide_frame_order"] = dict(
            method="stable-wide-native-frame-before-and-after-constraints",
            proposal=proposal,
            mapping=mapping,
            original=original,
        )
        if (
            len(
                json.dumps(candidate, ensure_ascii=False, allow_nan=False).encode(
                    "utf8"
                )
            )
            > 2 * 1024 * 1024
        ):
            return document
        return candidate
    except Exception:
        return document


def restore(document):
    audit = document.get("analysis", {}).get("native_wide_frame_order", {})
    if not audit.get("original") or audit.get("status") == "restored":
        return False
    original = copy.deepcopy(audit["original"])
    document["result"] = original["result"]
    document["review"] = original["review"]
    for name in ("reading_anchors", "text_check", "tail_tips"):
        document["analysis"].pop(name, None)
    document["analysis"].update(original["analysis_fields"])
    audit["status"] = "restored"
    return True
