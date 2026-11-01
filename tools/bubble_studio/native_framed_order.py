"""Preserve frame hierarchy across very thin, stable, bright panel gutters.

Only explicit frame-backed separators can disprove model panel ownership.
Each leaf retains its existing dialogue order and every reading geometry.
"""

import json, copy, re
import numpy as np
from .native_ink_evidence import text_boxes


def runs(profile):
    a = np.r_[False, profile, False].astype("int8")
    return list(zip(np.where(np.diff(a) == 1)[0], np.where(np.diff(a) == -1)[0]))


def propose(image, d):
    if (
        d.get("review", {}).get("verified")
        or d["analysis"].get("strip_reading")
        or d["result"].get("layout", "auto") not in {"auto", "rows"}
        or any(b.get("manual") for b in d["result"]["bubbles"])
    ):
        return None
    bs = d["result"]["bubbles"]
    anchors = d["analysis"].get("reading_anchors", {})
    if len(bs) < 6 or set(anchors) != {b["id"] for b in bs}:
        return None
    scale = min(1, 2200 / image.height, 1800 / image.width)
    rgb = np.asarray(
        image.resize((round(image.width * scale), round(image.height * scale)))
    )
    h, w = rgb.shape[:2]
    light = np.min(rgb, axis=2)
    dark = np.max(rgb, axis=2)
    boxes = {
        b["id"]: [[a * scale for a in box] for box in text_boxes(image, d, b)]
        for b in bs
    }
    proof = []

    def bands(rect, ids, axis):
        x, y, xx, yy = rect
        length = (yy - y, xx - x)[axis]
        patch = light[y:yy, x:xx]
        black = dark[y:yy, x:xx]
        along = 1 if axis == 0 else 0
        if min(patch.shape) < 80:
            return []
        darkness = np.mean(black < 120, axis=along)
        found = []
        for a, b in runs(np.mean(patch > 235, axis=along) >= 0.995):
            if (
                not 2 <= b - a <= length * 0.025
                or a < length * 0.08
                or b > length * 0.92
            ):
                continue
            reach = max(3, round(length * 0.012))
            left = darkness[max(0, a - reach) : a]
            right = darkness[b : min(length, b + reach)]
            support = max(left.max(initial=0), right.max(initial=0))
            if support < 0.90:
                continue
            # The same physical light band must survive a second brightness threshold.
            stable = [
                (c, e)
                for c, e in runs(np.mean(patch > 210, axis=along) >= 0.995)
                if c <= a and e >= b
            ]
            if (
                len(stable) != 1
                or stable[0][1] - stable[0][0] > (b - a) * 1.75
                or abs(sum(stable[0]) - a - b) > (b - a) * 0.6
            ):
                continue
            cut = (a + b) / 2 + (y if axis == 0 else x)
            coordinate = 1 if axis == 0 else 0
            first = [
                i for i in ids if all(box[coordinate + 2] < cut for box in boxes[i])
            ]
            second = [i for i in ids if all(box[coordinate] > cut for box in boxes[i])]
            if (
                len(first) < 2
                or len(second) < 2
                or len(first) + len(second) != len(ids)
            ):
                continue
            found.append(
                dict(
                    axis=axis,
                    cut=cut,
                    band=[int(a), int(b)],
                    frame_support=float(support),
                    first=first,
                    second=second,
                )
            )
        return found

    def split(rect, ids, depth=0):
        if depth >= 3:
            return [(rect, ids)]
        for axis in (0, 1):
            candidates = bands(rect, ids, axis)
            if not candidates:
                continue
            c = max(candidates, key=lambda c: c["band"][1] - c["band"][0])
            cut = round(c["cut"])
            x, y, xx, yy = rect
            rects = (
                [(x, y, xx, cut), (x, cut, xx, yy)]
                if axis == 0
                else [(x, y, cut, yy), (cut, y, xx, yy)]
            )
            groups = [(rects[0], c["first"]), (rects[1], c["second"])]
            proof.append(dict(rect=list(rect), **c))
            if axis == 1 and d["result"]["direction"] == "rtl":
                groups.reverse()
            return [leaf for r, g in groups for leaf in split(r, g, depth + 1)]
        return [(rect, ids)]

    leaves = split((0, 0, w, h), [b["id"] for b in bs])
    order = [i for _, ids in leaves for i in ids]
    if len(leaves) < 3 or order == [b["id"] for b in bs]:
        return None
    # Require a genuine conflict with a model's panel assignment, not a new
    # arbitrary sort of text in an unframed drawing.
    lookup = {b["id"]: b for b in bs}
    owners = {}
    for n, (_, ids) in enumerate(leaves):
        for i in ids:
            pid = lookup[i].get("panel_id")
            if pid:
                owners.setdefault(pid, set()).add(n)
    if not any(len(v) > 1 for v in owners.values()):
        return None
    return dict(
        ids=order,
        leaves=[dict(box=list(r), regions=ids) for r, ids in leaves],
        cuts=proof,
        size=[w, h],
    )


def refine(image, document):
    if document.get("analysis", {}).get("native_framed_order"):
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
        analysis["native_framed_order"] = dict(
            method="stable-thin-gutter-with-continuous-native-frame",
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
    audit = document.get("analysis", {}).get("native_framed_order", {})
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
