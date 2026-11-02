"""Read independently confirmed four-panel strips below framed title rows."""

import copy
import json
import re

from web.backend.comic_smartview_layout import _cluster_along

from .native_ink_evidence import text_boxes
from .strip_heading_order import confirmed
from .strip_reader import STRIP_CONTEXT_PROMPT, STRIP_PROMPT, strip_columns


def propose(image, document):
    result = document["result"]
    bodies = result["bubbles"]
    if (
        document.get("review", {}).get("verified")
        or any(b.get("manual") for b in bodies)
        or result.get("layout") not in {"auto", "columns"}
        or result.get("direction") not in {"ltr", "rtl"}
        or len(result.get("panels", [])) not in {10, 15}
        or set(document.get("analysis", {}).get("reading_anchors", {}))
        != {b["id"] for b in bodies}
    ):
        return None
    columns, _ = _cluster_along(result.get("panels", []), "x", "w")
    if not 2 <= len(columns) <= 3 or any(len(c) != 5 for c in columns):
        return None
    for c in columns:
        c.sort(key=lambda p: p["y"])
        title, *story = c
        if (
            not 0.008 <= title["h"] <= 0.08
            or not 0 < title["h"] <= min(p["h"] for p in story) * 0.45
            or not 0 <= story[0]["y"] - title["y"] - title["h"] <= 0.05
            or min(p["w"] for p in c) <= 0
            or max(p["w"] for p in c) / min(p["w"] for p in c) > 1.25
            or max(p["x"] for p in c) - min(p["x"] for p in c)
            > min(p["w"] for p in c) * 0.12
            or story[-1]["y"] + story[-1]["h"] - story[0]["y"] < 0.5
        ):
            return None
    if max(c[0]["y"] for c in columns) - min(c[0]["y"] for c in columns) > 0.02:
        return None
    story_columns = strip_columns(
        dict(result, panels=[p for c in columns for p in c[1:]])
    )
    if len(story_columns) != len(columns):
        return None
    columns.sort(key=lambda c: c[0]["x"], reverse=result["direction"] == "rtl")
    groups = [[[] for _ in c] for c in columns]
    for body in bodies:
        words = text_boxes(image, document, body)
        x = min(v[0] for v in words) / image.width
        y = min(v[1] for v in words) / image.height
        xx = max(v[2] for v in words) / image.width
        yy = max(v[3] for v in words) / image.height
        possible = [
            (n, k)
            for n, column in enumerate(columns)
            for k, panel in enumerate(column)
            if panel["x"] - 0.012 <= x < xx <= panel["x"] + panel["w"] + 0.012
            and panel["y"] - 0.015 <= y < yy <= panel["y"] + panel["h"] + 0.015
        ]
        if len(possible) != 1:
            return None
        n, k = possible[0]
        groups[n][k].append(body["id"])
    # Each short frame must already contain exactly one detected heading.
    # Within each story panel preserve the engine's existing dialogue order.
    if any(len(g[0]) != 1 or sum(bool(v) for v in g[1:]) < 2 for g in groups):
        return None
    order = [identity for g in groups for panel in g for identity in panel]
    if order == [b["id"] for b in bodies]:
        return None
    return dict(ids=order, columns=[[p["id"] for p in c] for c in columns])


def propose_declared(image, document):
    """A user's 4koma declaration overrides classification, never bad geometry."""
    result = document["result"]
    bodies = result["bubbles"]
    if (
        document.get("review", {}).get("verified")
        or any(b.get("manual") for b in bodies)
        or result.get("layout") not in {"auto", "columns"}
        or set(document.get("analysis", {}).get("reading_anchors", {}))
        != {b["id"] for b in bodies}
    ):
        return None
    columns = strip_columns(result)
    if not columns:
        return propose(image, document)
    groups = [[[] for _ in range(5)] for c in columns]
    for body in bodies:
        words = text_boxes(image, document, body)
        x = min(v[0] for v in words) / image.width
        y = min(v[1] for v in words) / image.height
        xx = max(v[2] for v in words) / image.width
        yy = max(v[3] for v in words) / image.height
        possible = [
            (n, k + 1)
            for n, c in enumerate(columns)
            for k, p in enumerate(c)
            if p["x"] - 0.012 <= x < xx <= p["x"] + p["w"] + 0.012
            and p["y"] - 0.015 <= y < yy <= p["y"] + p["h"] + 0.015
        ]
        if not possible and body.get("type") == "text" and body.get("panel_id") is None:
            possible = [
                (n, 0)
                for n, c in enumerate(columns)
                if c[0]["x"] - 0.012 <= x < xx <= c[0]["x"] + c[0]["w"] + 0.012
                and max(0, c[0]["y"] - 0.10) <= y < yy <= c[0]["y"] + 0.005
                and 0.004 <= yy - y <= 0.05
            ]
        if len(possible) != 1:
            return None
        n, k = possible[0]
        groups[n][k].append(body["id"])
    if any(len(g[0]) > 1 for g in groups):
        return None
    order = [identity for g in groups for panel in g for identity in panel]
    if order == [b["id"] for b in bodies]:
        return None
    return dict(ids=order, columns=[[p["id"] for p in c] for c in columns])


def classify(image, document, semantic, proposal):
    if confirmed(document):
        return dict(four_panel_strips=True, source="existing-confirmation")
    preview = image.copy()
    preview.thumbnail((1280, 1536))
    answer = semantic._ask([preview], STRIP_CONTEXT_PROMPT)
    if isinstance(answer, dict) and answer.get("four_panel_strips") is False:
        panels = {p["id"]: p for p in document["result"]["panels"]}
        selected = [panels[k] for c in proposal["columns"] for k in c]
        left = min(p["x"] for p in selected)
        top = min(p["y"] for p in selected)
        right = max(p["x"] + p["w"] for p in selected)
        bottom = max(p["y"] + p["h"] for p in selected)
        crop = image.crop(
            (
                max(0, int(left * image.width) - 15),
                max(0, int(top * image.height) - 15),
                min(image.width, int(right * image.width) + 15),
                min(image.height, int(bottom * image.height) + 15),
            )
        )
        crop.thumbnail((1100, 1536))
        answer = semantic._ask([preview, crop], STRIP_PROMPT)
    return answer


def refine(image, document, semantic, declared=False):
    if document.get("analysis", {}).get("framed_strip_order"):
        return document
    try:
        proposal = (
            propose_declared(image, document) if declared else propose(image, document)
        )
        if proposal is None:
            return document
        if semantic is None and not declared:
            return document
        calls_start = len(getattr(semantic, "calls", []))
        answer = (
            dict(four_panel_strips=True, source="user-declaration")
            if declared
            else classify(image, document, semantic, proposal)
        )
        if not isinstance(answer, dict) or answer.get("four_panel_strips") is not True:
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
        analysis["framed_strip_order"] = dict(
            method="four-panel-stories-with-framed-or-unframed-headings",
            classification=answer,
            calls=copy.deepcopy(getattr(semantic, "calls", [])[calls_start:]),
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
        if getattr(semantic, "strict", False):
            raise
        return document


def restore(document):
    audit = document.get("analysis", {}).get("framed_strip_order", {})
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
