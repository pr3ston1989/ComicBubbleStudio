"""Replace a major mask leak only with a stable closed, text-preserving interior."""
import copy
import cv2
import numpy as np
from .geometry import padded_box, contour_box
from .quality_guard import _polygons
from .textcheck import pixel_box
from .compound_guard import _texts, _text_preserved, _conflicts
from .refinement import enclosed_candidates


def repair_enclosure(image, document, bubble):
    texts = _texts(image, document, bubble)
    if (bubble.get('type') != 'bubble' or len(bubble.get('polygons', [])) != 1
            or not texts or not all(t.get('label') == 1 and t.get('score', 0) >= .7 for t in texts)):
        return bubble, None
    check = next((r for r in document['analysis'].get('text_check', {}).get('regions', []) if r['region_id'] == bubble['id']), None)
    if not check or not any(r.get('score', 0) >= .9 and any(c.isalpha() for c in r.get('text', '')) for r in check.get('ocr', [])):
        return bubble, None
    bounds = pixel_box(bubble, image.size)
    roi = padded_box(bounds, *image.size, .8, minimum=70)
    if (roi[2]-roi[0]) * (roi[3]-roi[1]) > 8_000_000:
        return bubble, None
    crop = image.crop(roi)
    old = np.zeros((crop.height, crop.width), np.uint8)
    cv2.fillPoly(old, _polygons(bubble, *image.size, roi[:2]), 1)
    old_count = max(1, np.sum(old))
    for opening in (3, 5):
        for candidate in enclosed_candidates(crop, bounds, texts, roi, image.size, opening, min_area_ratio=.04):
            if candidate['stability'] < .985 or candidate['score'] < .95:
                continue
            mask = cv2.dilate((candidate['mask'] > 0).astype(np.uint8), np.ones((5, 5), np.uint8))
            ratio = float(np.sum(mask) / old_count)
            # Small cosmetic shrinkage can amputate valid rays or tails.
            # Only a major excess mask is eligible for this replacement.
            if not .10 <= ratio <= .60 or np.sum(mask & old) / max(1, np.sum(mask)) < .995:
                continue
            full = np.zeros((image.height, image.width), np.uint8)
            full[roi[1]:roi[3], roi[0]:roi[2]] = mask
            if not _text_preserved(image, document, bubble, full):
                continue
            region = contour_box(mask, roi, *image.size, bubble['confidence'], epsilon=.1, max_vertices=2048)
            region.update({key: bubble[key] for key in ('id', 'order', 'panel_id') if key in bubble})
            if len(region['polygons']) != 1 or _conflicts(region, [bubble], document, image.size):
                continue
            full.fill(0)
            cv2.fillPoly(full, _polygons(region, *image.size, (0, 0)), 1)
            if not _text_preserved(image, document, bubble, full):
                continue
            if sum(len(p) for b in document['result']['bubbles'] if b is not bubble for p in b.get('polygons', [])) + sum(len(p) for p in region['polygons']) > 32000:
                continue
            return region, dict(method='major-leak-stable-native-enclosure', area_ratio=ratio,
                                stability=candidate['stability'], boundary_support=candidate['score'],
                                original_region=copy.deepcopy(bubble))
    return bubble, None


def repair_page_enclosures(image, document, checker):
    if document.get('review', {}).get('verified'):
        return document
    changes = []
    for index, bubble in enumerate(document['result']['bubbles']):
        candidate, audit = repair_enclosure(image, document, bubble)
        if audit is not None:
            document['result']['bubbles'][index] = candidate
            changes.append(dict(region_id=bubble['id'], **audit))
    if changes:
        document['analysis']['enclosure_repair'] = changes
        checker.review(image, document)
        document['review']['flags'].append('Naprawiono duży wyciek obrysu po kontroli zamknięcia i zachowania wszystkich wykrytych wierszy tekstu; sprawdź podgląd')
    return document
