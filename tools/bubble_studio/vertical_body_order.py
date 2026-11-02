"""Correct adjacent same-column balloons only when body and text agree."""

import copy
import json
import re

from .native_ink_evidence import text_boxes


def propose(image, document):
    result = document["result"]
    bodies = result["bubbles"]
    if (
        document.get("review", {}).get("verified")
        or any(b.get("manual") for b in bodies)
        or result.get("layout") not in {"auto", "columns"}
        or result.get("direction") not in {"ltr", "rtl"}
        or set(document.get("analysis", {}).get("reading_anchors", {}))
        != {b["id"] for b in bodies}
    ):
        return None
    panels = {p["id"]: p for p in result.get("panels", [])}
    ordered = list(bodies)
    swaps = []
    # A single forward pass changes only originally adjacent pairs. It cannot
    # pull a balloon across an intervening speaker or across a panel boundary.
    for index in range(len(ordered) - 1):
        lower, upper = ordered[index : index + 2]
        if (
            not lower.get("panel_id")
            or lower.get("panel_id") != upper.get("panel_id")
            or lower["panel_id"] not in panels
            or any(
                b.get("type") != "bubble" or len(b.get("polygons", [])) != 1
                for b in (lower, upper)
            )
        ):
            continue
        gap = lower["y"] - upper["y"] - upper["h"]
        if not max(2 / image.height, 0.001) <= gap <= max(lower["h"], upper["h"]):
            continue
        width = min(lower["w"], upper["w"])
        overlap = min(lower["x"] + lower["w"], upper["x"] + upper["w"]) - max(
            lower["x"], upper["x"]
        )
        if width <= 0 or overlap / width < 0.8:
            continue
        low_text = text_boxes(image, document, lower)
        up_text = text_boxes(image, document, upper)
        if max(v[3] for v in up_text) >= min(v[1] for v in low_text) - 2:
            continue
        left = max(min(v[0] for v in low_text), min(v[0] for v in up_text))
        right = min(max(v[2] for v in low_text), max(v[2] for v in up_text))
        if left >= right:
            continue
        # The model's scene ownership must agree with the actual text bounds.
        panel = panels[lower["panel_id"]]
        if any(
            not (
                panel["x"] - 0.012
                <= a / image.width
                < c / image.width
                <= panel["x"] + panel["w"] + 0.012
                and panel["y"] - 0.015
                <= b / image.height
                < d / image.height
                <= panel["y"] + panel["h"] + 0.015
            )
            for a, b, c, d in low_text + up_text
        ):
            continue
        ordered[index], ordered[index + 1] = upper, lower
        swaps.append(
            dict(
                upper=upper["id"],
                lower=lower["id"],
                panel=panel["id"],
                body_gap=gap,
                horizontal_overlap=overlap / width,
            )
        )
    if not swaps:
        return None
    return dict(ids=[b["id"] for b in ordered], swaps=swaps)


def refine(image, document):
    if document.get("analysis", {}).get("vertical_body_order"):
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
        analysis["vertical_body_order"] = dict(
            method="adjacent-same-column-bodies-and-text-top-to-bottom",
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
    audit = document.get("analysis", {}).get("vertical_body_order", {})
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
