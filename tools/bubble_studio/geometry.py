"""Native-resolution contour validation, deduplication, and reading-order geometry."""

from __future__ import annotations

import math
import cv2
import numpy as np

from web.backend.comic_smartview_layout import containing_panel, group_bubbles_by_panel, order_boxes_by_cuts, renumber


def intersection(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def deduplicate(items, threshold=0.82):
    """Suppress duplicate tile detections while keeping spatially distinct balloons."""
    output = []
    for item in sorted(items, key=lambda item: item['score'], reverse=True):
        if not any(intersection(item['box'], kept['box']) / max(1, min(area(item['box']), area(kept['box']))) >= threshold for kept in output):
            output.append(item)
    return output


def padded_box(box, width, height, fraction=0.28, minimum=12):
    dx, dy = max(minimum, (box[2] - box[0]) * fraction), max(minimum, (box[3] - box[1]) * fraction)
    return (max(0, math.floor(box[0] - dx)), max(0, math.floor(box[1] - dy)),
            min(width, math.ceil(box[2] + dx)), min(height, math.ceil(box[3] + dy)))


def _fill(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, contours, -1, 255, cv2.FILLED)
    return filled


def validated_mask(mask, detection, texts, origin):
    """Reject truncated, oversized, or text-cutting SAM masks; never fabricate contours."""
    mask = _fill((np.asarray(mask) > 0).astype(np.uint8) * 255)
    count = np.count_nonzero(mask)
    if not count or not 0.20 <= count / max(1, area(detection)) <= 1.65:
        return None, 'Rozmiar maski nie pasuje do dymka'
    if np.any(mask[0]) or np.any(mask[-1]) or np.any(mask[:, 0]) or np.any(mask[:, -1]):
        return None, 'Maska dotyka brzegu wycinka; możliwy ucięty kontur'
    for text in texts:
        x1, y1, x2, y2 = text['box']
        x1, x2 = max(0, math.floor(x1 - origin[0])), min(mask.shape[1], math.ceil(x2 - origin[0]))
        y1, y2 = max(0, math.floor(y1 - origin[1])), min(mask.shape[0], math.ceil(y2 - origin[1]))
        sample = mask[y1:y2, x1:x2]
        if not sample.size or np.count_nonzero(sample) / sample.size < 0.94:
            return None, 'Maska nie obejmuje całego wykrytego tekstu'
    # Dwa piksele zapasu zachowują tusz obramowania, nie tylko białe wnętrze.
    return cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2), None


def contour_box(mask, origin, width, height, confidence, epsilon=0.7, max_vertices=512):
    """Retain separate components and concavity, with bounded subpixel simplification."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted((c for c in contours if cv2.contourArea(c) >= 12), key=cv2.contourArea, reverse=True)[:16]
    if not contours:
        raise ValueError('Pusta maska dymka')
    x, y, w, h = cv2.boundingRect(np.concatenate(contours))
    polygons = []
    for contour in contours:
        tolerance = max(.01,float(epsilon))
        simplified = cv2.approxPolyDP(contour, tolerance, True)
        while len(simplified) > max_vertices:
            tolerance *= 1.5
            simplified = cv2.approxPolyDP(contour, tolerance, True)
        if len(simplified) >= 3:
            polygons.append([{'x': float(np.clip((point[0][0] - x) / w, 0, 1)),
                              'y': float(np.clip((point[0][1] - y) / h, 0, 1))} for point in simplified])
    if not polygons:
        raise ValueError('Zdegenerowany kontur dymka')
    return {'x': (x + origin[0]) / width, 'y': (y + origin[1]) / height, 'w': w / width, 'h': h / height,
            'confidence': confidence, 'polygons': polygons, 'polygon': polygons[0], 'type': 'bubble', 'source': 'external'}


def rectangle(box, width, height, confidence, kind='bubble', margin=3):
    x1, y1, x2, y2 = box
    x1, y1, x2, y2 = max(0, x1 - margin), max(0, y1 - margin), min(width, x2 + margin), min(height, y2 + margin)
    return {'x': x1 / width, 'y': y1 / height, 'w': (x2 - x1) / width, 'h': (y2 - y1) / height,
            'confidence': confidence, 'type': kind, 'source': 'external'}


def ordered_result(panels, bubbles, width, height, direction, layout):
    # Layout compares x-gaps with y-gaps in physical pixels: H/W, not W/H.
    panels = renumber(order_boxes_by_cuts(panels, direction, page_aspect=height / width, layout=layout), 'p')
    anchors = []
    originals = {}
    ambiguous=set()
    for i,a in enumerate(bubbles):
        for b in bubbles[i+1:]:
            overlap=max(0,min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x']))*max(0,min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y']))
            if overlap/max(1e-12,min(a['w']*a['h'],b['w']*b['h']))>.8:
                ambiguous.update((id(a),id(b)))
    for bubble in bubbles:
        # Tails and joined lobes must not move an utterance into another row/panel.
        anchor = dict(bubble.pop('_reading_box', bubble))
        # A conflict fallback can retain an anchor originally made for a
        # balloon. Layout needs the surviving region's actual classification.
        anchor['type'] = bubble.get('type', 'bubble')
        if id(bubble) in ambiguous:
            anchor['_layout_ambiguous']=True
        panel = containing_panel(panels, anchor)
        bubble['panel_id'] = panel['id'] if panel else None
        anchor['panel_id'] = bubble['panel_id']
        anchors.append(anchor)
        originals[id(anchor)] = bubble
    ordered = group_bubbles_by_panel(panels, anchors, direction, page_aspect=height / width, layout=layout)
    bubbles = renumber([originals[id(anchor)] for anchor in ordered], 'b')
    return {'width': width, 'height': height, 'direction': direction, 'layout': layout,
            'crop': {'x': 0, 'y': 0, 'w': 1, 'h': 1}, 'panels': panels, 'bubbles': bubbles,
            'confidence': sum(box['confidence'] for box in bubbles) / max(1, len(bubbles))}
