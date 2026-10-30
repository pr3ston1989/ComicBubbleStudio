"""Recover detached thought circles only from closed native paper-and-ink shapes."""
import cv2
import numpy as np
from .geometry import padded_box, contour_box
from .quality_guard import _polygons
from .textcheck import pixel_box
from .stroke_guard import recover_page_outlines


def _circles(gray, old, body, distance, short, threshold):
    _, labels, stats, centers = cv2.connectedComponentsWithStats((gray > threshold).astype(np.uint8), 8)
    output = []
    for index, (x, y, width, height, area) in enumerate(stats[1:], 1):
        radius = (area / np.pi) ** .5
        if (not 1.5 <= radius <= min(40, short * .16)
                or not .65 <= width / max(1, height) <= 1.55
                or x == 0 or y == 0 or x + width == gray.shape[1] or y + height == gray.shape[0]):
            continue
        cx, cy = np.rint(centers[index]).astype(int)
        if body[cy, cx] or distance[cy, cx] > max(30, short * .35):
            continue
        component = (labels[y:y+height, x:x+width] == index).astype(np.uint8)
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        if len(contour) < 5 or 4 * np.pi * cv2.contourArea(contour) / max(1, perimeter ** 2) < .68:
            continue
        fitted = np.zeros_like(component)
        cv2.ellipse(fitted, cv2.fitEllipse(contour), 1, -1)
        if np.sum(fitted & component) / max(1, np.sum(fitted | component)) < .85:
            continue
        mask = (labels == index).astype(np.uint8)
        ring = (cv2.dilate(mask, np.ones((3, 3), np.uint8)) > 0) & (mask == 0)
        if np.mean(gray[ring] < 128) < .50:
            continue
        output.append(dict(center=np.array([cx, cy]), radius=radius, mask=mask,
                           distance=float(distance[cy, cx]),
                           new_fraction=float(np.sum(mask & (1-old)) / max(1, np.sum(mask)))))
    return output


def _chain(circles, body, short):
    moments = cv2.moments(body)
    center = np.array([moments['m10'] / max(1, moments['m00']), moments['m01'] / max(1, moments['m00'])])
    best = []
    for index, first in enumerate(circles):
        if first['distance'] > max(12, first['radius'] * 3.5):
            continue
        path = [index]
        direction = first['center'] - center
        while len(path) < 4:
            previous = circles[path[-1]]
            options = []
            for other_index, other in enumerate(circles):
                if other_index in path or other['radius'] > previous['radius'] * 1.1:
                    continue
                vector = other['center'] - previous['center']
                length = np.linalg.norm(vector)
                cosine = np.dot(vector, direction) / max(1e-9, length * np.linalg.norm(direction))
                radius_sum = previous['radius'] + other['radius']
                if .8 * radius_sum <= length <= 3.5 * radius_sum and cosine > .8:
                    options.append((length, other_index))
            if not options:
                break
            _, other_index = min(options)
            direction = circles[other_index]['center'] - previous['center']
            path.append(other_index)
        if len(path) > len(best):
            best = path
    return [circles[index] for index in best] if len(best) >= 2 else []


def recover_thought_dots(image, bubble, texts):
    if (bubble.get('type') != 'bubble' or not 1 <= len(bubble.get('polygons', [])) <= 12
            or not texts or not all(t.get('label') == 1 and t.get('score', 0) >= .7 for t in texts)):
        return bubble, None
    bounds = pixel_box(bubble, image.size)
    short = min(bounds[2]-bounds[0], bounds[3]-bounds[1])
    roi = padded_box(bounds, *image.size, .45, minimum=60)
    if (roi[2]-roi[0]) * (roi[3]-roi[1]) > 4_000_000:
        return bubble, None
    gray = cv2.cvtColor(np.asarray(image.crop(roi)), cv2.COLOR_RGB2GRAY)
    old = np.zeros(gray.shape, np.uint8)
    cv2.fillPoly(old, _polygons(bubble, *image.size, roi[:2]), 1)
    size = max(9, round(short * .20)) | 1
    opened = cv2.morphologyEx(old, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
    _, labels, stats, _ = cv2.connectedComponentsWithStats(opened, 8)
    if len(stats) < 2:
        return bubble, None
    body = (labels == 1 + int(np.argmax(stats[1:, -1]))).astype(np.uint8)
    if np.sum(body) < .6 * np.sum(old) or np.median(gray[body > 0]) < 210:
        return bubble, None
    distance = cv2.distanceTransform(1-old, cv2.DIST_L2, 5)
    first = _chain(_circles(gray, old, body, distance, short, 220), body, short)
    second = _chain(_circles(gray, old, body, distance, short, 240), body, short)
    if not first or len(first) != len(second) or not any(c['new_fraction'] > .10 for c in first):
        return bubble, None
    for a, b in zip(first, second):
        if np.linalg.norm(a['center']-b['center']) > 2 or np.sum(a['mask'] & b['mask']) / max(1, np.sum(a['mask'] | b['mask'])) < .90:
            return bubble, None
    merged = old.copy()
    for circle in first:
        merged |= cv2.dilate(circle['mask'], np.ones((3, 3), np.uint8))
    result = contour_box(merged, roi, *image.size, bubble['confidence'], epsilon=.1, max_vertices=2048)
    if len(result['polygons']) > 16:
        return bubble, None
    result.update({key: bubble[key] for key in ('id', 'order', 'panel_id') if key in bubble})
    exported = np.zeros_like(old)
    cv2.fillPoly(exported, _polygons(result, *image.size, roi[:2]), 1)
    preserved = float(np.sum(exported & old) / max(1, np.sum(old)))
    if preserved < .999 or any(np.sum(exported & c['mask']) / max(1, np.sum(c['mask'])) < .95 for c in first):
        return bubble, None
    return result, dict(method='native-stable-thought-circle-chain', mask_preserved=preserved,
                        circles=[dict(center=(c['center']+roi[:2]).tolist(), radius=c['radius']) for c in first])


def recover_page_thought_dots(image, document):
    return recover_page_outlines(image, document, recovery=recover_thought_dots,
        audit_key='thought_circle_recovery', flag='Uzupełniono kółka prowadzące od dymka myśli; sprawdź podgląd')
