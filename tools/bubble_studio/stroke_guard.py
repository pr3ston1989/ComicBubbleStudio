"""Conservative recovery of isolated physical ink outlines at native resolution.

Recover the physical ink beyond a model's interior mask. Require a stable,
isolated, closed outline enclosing the old core. Never shrink a balloon.
"""
import cv2
import numpy as np
from .geometry import padded_box, contour_box
from .quality_guard import _polygons
from .textcheck import pixel_box


def recover_page_outlines(image, document, recovery=None, audit_key='stroke_outline_recovery', flag=None):
    """Extend supported outlines after reading order and page review are final.

    Bind evidence by the immutable text anchor, never by balloon numbers. A
    changed contour cannot authorize itself or consume another reading anchor.
    """
    if document.get('review', {}).get('verified'):
        return document
    from .geometry import rectangle
    from .quality_guard import overlap_share
    analysis = document.get('analysis', {})
    anchors = analysis.get('reading_anchors', {})
    evidence = []
    for diagnostic in analysis.get('balloons', []):
        rows = diagnostic.get('supporting_texts', [])
        if not rows:
            continue
        bounds = [min(r['box'][0] for r in rows), min(r['box'][1] for r in rows),
                  max(r['box'][2] for r in rows), max(r['box'][3] for r in rows)]
        evidence.append((rectangle(bounds, *image.size, 1, margin=0), rows))
    bubbles = document['result']['bubbles']
    changes = []
    for index, bubble in enumerate(bubbles):
        anchor = anchors.get(bubble['id'])
        if anchor is None:
            continue
        matches = [rows for box, rows in evidence
                   if all(abs(box[k]-anchor[k]) < 1e-6 for k in ('x','y','w','h'))]
        if len(matches) != 1:
            continue
        candidate, audit = (recovery or recover_stroke_outline)(image, bubble, matches[0])
        if audit is None:
            continue
        if any(overlap_share(candidate, other, *image.size) > .03
               for other in bubbles if other is not bubble and other.get('polygons')):
            continue
        # Only added pixels are relevant: an existing imperfect mask must not
        # become permission to cover a neighbouring narration or thought.
        region = pixel_box(candidate, image.size)
        old = np.zeros((region[3]-region[1], region[2]-region[0]), np.uint8)
        new = np.zeros_like(old)
        cv2.fillPoly(old, _polygons(bubble, *image.size, region[:2]), 1)
        cv2.fillPoly(new, _polygons(candidate, *image.size, region[:2]), 1)
        added = new & (1-old)
        blocked = False
        for other in bubbles:
            if other is bubble:
                continue
            target = anchors.get(other['id'], other)
            x1,y1,x2,y2 = pixel_box(target, image.size)
            x1,x2 = max(0,x1-region[0]), min(added.shape[1],x2-region[0])
            y1,y2 = max(0,y1-region[1]), min(added.shape[0],y2-region[1])
            if x2>x1 and y2>y1 and np.any(added[y1:y2,x1:x2]):
                blocked = True
                break
        if blocked:
            continue
        if (sum(len(p) for b in bubbles if b is not bubble for p in b.get('polygons',[]))
                +sum(len(p) for p in candidate.get('polygons',[]))) > 32000:
            continue
        bubbles[index] = candidate
        changes.append(dict(region_id=bubble['id'], original_region=bubble, **audit))
    if changes:
        analysis[audit_key] = changes
        document['review']['flags'].append(flag or 'Uzupełniono końcówkę obrysu na podstawie zamkniętej linii dymka; sprawdź podgląd')
    return document


def recover_stroke_outline(image, bubble, texts, ink_color=None):
    if (bubble.get('type') != 'bubble' or len(bubble.get('polygons', [])) != 1
            or not texts or not all(t.get('label') == 1 and t.get('score', 0) >= .7 for t in texts)):
        return bubble, None
    bounds = pixel_box(bubble, image.size)
    region = padded_box(bounds, *image.size, .6, minimum=60)
    if (region[2]-region[0])*(region[3]-region[1]) > 6_000_000:
        return bubble, None
    rgb = np.asarray(image.crop(region))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    old = np.zeros(gray.shape, np.uint8)
    cv2.fillPoly(old, _polygons(bubble, *image.size, region[:2]), 1)
    count = np.count_nonzero(old)
    core = cv2.erode(old, np.ones((7, 7), np.uint8))
    inside = gray[core > 0]
    if not len(inside):
        return bubble, None
    median = float(np.median(inside))
    if ink_color is not None:
        thresholds, light = (12, 24), False
    elif median < 60:
        thresholds, light = (208, 240), True
    elif median > 195:
        thresholds, light = (64, 80), False
    else:
        return bubble, None
    band = ((cv2.dilate(old, np.ones((9, 9), np.uint8)) > 0)
            & (cv2.erode(old, np.ones((3, 3), np.uint8)) == 0))
    candidates = []
    for threshold in thresholds:
        ink = ((np.max(np.abs(rgb.astype(np.int16)-np.asarray(ink_color)),axis=2) <= threshold)
               if ink_color is not None else ((gray > threshold) if light else (gray < threshold))).astype(np.uint8)
        _, labels, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
        ids, hits = np.unique(labels[band], return_counts=True)
        proposals = []
        for label, touches in zip(ids, hits):
            if not label or touches < .12*np.count_nonzero(band):
                continue
            x, y, w, h, _ = stats[label]
            if x == 0 or y == 0 or x+w == gray.shape[1] or y+h == gray.shape[0]:
                continue
            component = (labels == label).astype(np.uint8)
            contours, hierarchy = cv2.findContours(component, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            # An outline encloses one interior. Joined artwork/another balloon
            # can create additional holes and must not authorize a merge.
            holes = [c for c, v in zip(contours, hierarchy[0])
                     if v[3] >= 0 and cv2.contourArea(c) > max(12, count*.0001)]
            if len(holes) != 1:
                continue
            filled = np.zeros_like(old)
            cv2.drawContours(filled, [c for c, v in zip(contours, hierarchy[0]) if v[3] < 0], -1, 1, cv2.FILLED)
            coverage = np.count_nonzero((filled > 0) & (old > 0))/count
            core_coverage = np.count_nonzero((filled > 0) & (core > 0))/max(1, np.count_nonzero(core))
            if coverage < .97 or core_coverage < .999:
                continue
            merged = filled | old
            added = (merged > 0) & (old == 0)
            growth = np.count_nonzero(added)/count
            if not .001 <= growth <= .15:
                continue
            distance = cv2.distanceTransform((old == 0).astype(np.uint8), cv2.DIST_L2, 5)
            reach = float(distance[added].max())
            short = min(bounds[2]-bounds[0], bounds[3]-bounds[1])
            thickness = float(cv2.distanceTransform(added.astype(np.uint8), cv2.DIST_L2, 5).max())*2
            if not max(7, short*.025) <= reach <= min(120, short*.5) or thickness > max(14, short*.12):
                continue
            # A tail has one isolated extension. Several distant ink branches
            # are typically face creases, speed lines or attached screentone.
            # Ignore the thin rim itself and tiny raster islands, but require
            # one dominant extension instead of absorbing all connected ink.
            distal = (added & (distance > max(4, reach*.2))).astype(np.uint8)
            _, _, distal_stats, _ = cv2.connectedComponentsWithStats(distal, 8)
            branches = sorted((int(s[-1]) for s in distal_stats[1:] if s[-1] >= 4), reverse=True)
            if not branches or sum(branches[1:]) > max(8, branches[0]*.08):
                continue
            proposals.append((touches, merged, dict(growth=growth, reach=reach, thickness=thickness,
                                                  polarity='dark' if light else 'light')))
        if not proposals:
            return bubble, None
        candidates.append(max(proposals, key=lambda p: p[0]))
    a, b = candidates
    stability = np.count_nonzero(a[1] & b[1])/max(1, np.count_nonzero(a[1] | b[1]))
    if stability < .98:
        return bubble, None
    result = contour_box(a[1], region, *image.size, bubble['confidence'])
    result.update({k: bubble[k] for k in ('id', 'order', 'panel_id') if k in bubble})
    # Verify the exported polygon too: simplification can lose edge pixels
    # even though the raster union itself preserves every old pixel.
    final = np.zeros_like(old)
    cv2.fillPoly(final, _polygons(result, *image.size, region[:2]), 1)
    preserved = np.count_nonzero((final > 0) & (old > 0))/count
    if preserved < .999:
        return bubble, None
    return result, dict(a[2], stability=stability, mask_preserved=float(preserved),
                        method='native-rgb-isolated-ink-enclosure' if ink_color is not None else 'native-isolated-ink-enclosure')
