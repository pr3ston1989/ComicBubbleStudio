"""Recover enclosed balloon interiors at scan resolution, with explicit leak checks.

This is a candidate generator, not an assumed ellipse: open/transparent balloons
continue through the learned segmenters. No page or drawing is modified.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import _fill, area


def boundary_support(mask, image):
    """Fraction of contour pixels near a contrast edge (not model confidence)."""
    rgb = np.asarray(image)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 120)
    # Include chromatic borders with little luminance contrast.
    for channel in cv2.split(rgb):
        edges |= cv2.Canny(channel, 50, 120)
    near = cv2.dilate(edges, np.ones((7, 7), np.uint8)) > 0
    binary = (mask > 0).astype(np.uint8)
    boundary = binary - cv2.erode(binary, np.ones((3, 3), np.uint8))
    return float(np.count_nonzero(near & (boundary > 0)) / max(1, np.count_nonzero(boundary)))


def enclosed_candidates(image, detection, texts, region, page_size=None, opening=0, min_area_ratio=.30):
    """Find uniform interiors seeded by text backgrounds, rejecting escaping fills.

    Quantized modes ignore the minority ink pixels. A candidate must be stable
    at two color tolerances, connected, bounded, and occupy most of its detector
    box. Letter holes are filled only after the outer component is established.
    """
    rgb = np.asarray(image)
    height, width = rgb.shape[:2]
    if not texts or width * height > 8_000_000:
        return []
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.int16)
    samples = []
    for text in texts:
        box = text['box']
        x1, y1 = max(0, int(box[0]-region[0])), max(0, int(box[1]-region[1]))
        x2, y2 = min(width, int(np.ceil(box[2]-region[0]))), min(height, int(np.ceil(box[3]-region[1])))
        if x2-x1 < 3 or y2-y1 < 3:
            continue
        crop = rgb[y1:y2, x1:x2]
        codes = (crop.astype(np.int32)//16)
        codes = codes[..., 0]*256 + codes[..., 1]*16 + codes[..., 2]
        values, counts = np.unique(codes, return_counts=True)
        mode = values[np.argmax(counts)]
        matching = codes == mode
        if np.count_nonzero(matching) < crop.shape[0]*crop.shape[1]*.25:
            continue
        color = np.median(lab[y1:y2, x1:x2][matching], axis=0)
        samples.append((color, (x1, y1, x2, y2)))
    output = []
    for color, text_region in samples:
        distance = np.max(np.abs(lab-color), axis=2)
        previous = None
        for tolerance in (12, 24):
            binary = (distance <= tolerance).astype(np.uint8)
            if opening:
                # A three-pixel opening separates white balloon interiors from
                # the diagonal white channels of printed halftone backgrounds.
                # This variant is opt-in and must pass the tail-specific guard.
                binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((opening,opening),np.uint8))
            count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            x1, y1, x2, y2 = text_region
            ids, counts = np.unique(labels[y1:y2, x1:x2], return_counts=True)
            valid = [(int(n), int(i)) for i, n in zip(ids, counts) if i and stats[i, cv2.CC_STAT_AREA] >= area(detection)*.15]
            if not valid:
                break
            component = max(valid)[1]
            x, y, w, h, pixels = stats[component]
            # Color fills reaching even the physical page edge can be exterior
            # whitespace leaking through an open manga balloon. Learned masks
            # may handle true page clipping; this generator requires enclosure.
            if x == 0 or y == 0 or x+w == width or y+h == height:
                break
            mask = _fill((labels == component).astype(np.uint8)*255)
            ratio = np.count_nonzero(mask)/max(1, area(detection))
            if not min_area_ratio <= ratio <= 4.5:
                break
            if previous is not None:
                a, b = previous > 0, mask > 0
                stability = np.count_nonzero(a & b)/max(1, np.count_nonzero(a | b))
                support = boundary_support(mask, image)
                if stability >= .96 and support >= .70:
                    if not any(np.count_nonzero((mask > 0) ^ (item['mask'] > 0)) < np.count_nonzero(mask)*.02 for item in output):
                        output.append({'mask': mask, 'origin': region[:2], 'method': 'screened-enclosure' if opening else 'enclosed-color',
                                       'score': support, 'stability': round(float(stability), 4),
                                       'box': [x+region[0], y+region[1], x+w+region[0], y+h+region[1]],
                                       'area_ratio': round(float(ratio), 3)})
            previous = mask
    return output


def candidate_rank(mask, image, confidence, metrics):
    """Compare image evidence first; confidence is only a small tie breaker."""
    support = boundary_support(mask, image)
    ink = metrics.get('ink_coverage')
    return .80*support + .15*(ink if ink is not None else .9) + .05*float(confidence), support


def contour_covers_text(bubble, text, page_size):
    """Use the polygon interior, never the balloon's bounding rectangle."""
    width,height=page_size
    box=text['box']
    # Test a grid inside the text box; unlike bbox overlap this rejects concavity.
    points=[(x,y) for y in np.linspace(box[1]+(box[3]-box[1])*.2,box[3]-(box[3]-box[1])*.2,5)
            for x in np.linspace(box[0]+(box[2]-box[0])*.2,box[2]-(box[2]-box[0])*.2,5)]
    contours=[np.array([[(bubble['x']+p['x']*bubble['w'])*width,
                        (bubble['y']+p['y']*bubble['h'])*height] for p in polygon],np.float32)
              for polygon in bubble.get('polygons',[])]
    return bool(contours) and all(any(cv2.pointPolygonTest(c,(float(x),float(y)),False)>=0 for c in contours) for x,y in points)
