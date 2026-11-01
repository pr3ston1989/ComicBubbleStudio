"""Keep existing headings with visually confirmed four-panel stories."""

import copy
import hashlib
import json
import re

from .native_ink_evidence import text_boxes
from .strip_reader import STRIP_CONTEXT_PROMPT, STRIP_PROMPT, strip_columns


def confirmed(document):
    audit = document["analysis"].get("strip_reading", {})
    if audit.get("classification", {}).get("four_panel_strips") is True:
        return True
    prompts = {
        hashlib.sha256(p.encode()).hexdigest()
        for p in (STRIP_CONTEXT_PROMPT, STRIP_PROMPT)
    }
    for call in document["analysis"].get("page_context", {}).get("calls", []):
        if call.get("prompt_sha256") not in prompts:
            continue
        try:
            answer = json.loads(call["answer"])
        except (ValueError, TypeError, KeyError):
            continue
        if isinstance(answer, dict) and answer.get("four_panel_strips") is True:
            return True
    return False


def propose(image, document):
    result = document["result"]
    bodies = result["bubbles"]
    if (
        document.get("review", {}).get("verified")
        or any(b.get("manual") for b in bodies)
        or result.get("layout", "auto") not in {"auto", "columns"}
        or not confirmed(document)
    ):
        return None
    columns = strip_columns(result)
    if not 2 <= len(columns) <= 3:
        return None
    anchors = document["analysis"].get("reading_anchors", {})
    if set(anchors) != {b["id"] for b in bodies}:
        return None
    bounds = {}
    for b in bodies:
        words = text_boxes(image, document, b)
        bounds[b["id"]] = [
            min(v[0] for v in words) / image.width,
            min(v[1] for v in words) / image.height,
            max(v[2] for v in words) / image.width,
            max(v[3] for v in words) / image.height,
        ]
    headings = []
    for column in columns:
        first = column[0]
        left = min(p["x"] for p in column) - 0.012
        right = max(p["x"] + p["w"] for p in column) + 0.012
        found = []
        for b in bodies:
            x, y, xx, yy = bounds[b["id"]]
            if (
                b.get("type") == "text"
                and b.get("panel_id") is None
                and left <= x < xx <= right
                and max(0, first["y"] - 0.10) <= y < first["y"]
                and yy <= first["y"] + 0.01
                and 0.004 <= yy - y <= 0.05
            ):
                found.append(b["id"])
        if len(found) != 1:
            return None
        headings.append(found[0])
    if len(set(headings)) != len(headings):
        return None
    groups = [[] for _ in columns]
    occupied = [set() for _ in columns]
    assigned = []
    for b in bodies:
        if b["id"] in headings:
            continue
        x, y, xx, yy = bounds[b["id"]]
        possible = [
            (n, k)
            for n, column in enumerate(columns)
            for k, panel in enumerate(column)
            if panel["x"] - 0.012 <= x < xx <= panel["x"] + panel["w"] + 0.012
            and panel["y"] - 0.015 <= y < yy <= panel["y"] + panel["h"] + 0.015
        ]
        # Every dialogue belongs unambiguously to one of the four panels.
        if len(possible) != 1:
            return None
        n, k = possible[0]
        groups[n].append(b["id"])
        occupied[n].add(k)
        assigned.append(n)
    # Only headings may change position. Never choose a new dialogue order.
    if assigned != sorted(assigned) or not any(len(v) >= 2 for v in occupied):
        return None
    order = [i for title, group in zip(headings, groups) for i in [title, *group]]
    if order == [b["id"] for b in bodies]:
        return None
    return dict(
        ids=order, headings=headings, columns=[[p["id"] for p in c] for c in columns]
    )


def refine(image, document):
    if document.get("analysis", {}).get("strip_heading_order"):
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
        analysis["strip_heading_order"] = dict(
            method="existing-heading-stays-with-confirmed-four-panel-story",
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
    audit = document.get("analysis", {}).get("strip_heading_order", {})
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
