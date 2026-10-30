"""Evidence-guided mask validation shared by GPU inference and offline benchmarks."""

from __future__ import annotations

import math
import cv2
import numpy as np

from .geometry import area, intersection, _fill


def mask_in_region(candidate, region):
    """Place a compact native-resolution candidate into a requested page crop."""
    output = np.zeros((region[3] - region[1], region[2] - region[0]), np.uint8)
    origin, mask = candidate['origin'], candidate['mask']
    x1, y1 = max(region[0], origin[0]), max(region[1], origin[1])
    x2, y2 = min(region[2], origin[0] + mask.shape[1]), min(region[3], origin[1] + mask.shape[0])
    if x2 > x1 and y2 > y1:
        output[y1-region[1]:y2-region[1], x1-region[0]:x2-region[0]] = mask[y1-origin[1]:y2-origin[1], x1-origin[0]:x2-origin[0]]
    return output


def ink_evidence(image, texts, origin):
    """Find small contrast components inside text boxes, without OCR or language assumptions."""
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    evidence = np.zeros_like(gray, np.uint8)
    reliable = 0
    for text in texts:
        x1, y1, x2, y2 = text['box']
        x1, y1 = max(0, math.floor(x1-origin[0])), max(0, math.floor(y1-origin[1]))
        x2, y2 = min(gray.shape[1], math.ceil(x2-origin[0])), min(gray.shape[0], math.ceil(y2-origin[1]))
        sample = gray[y1:y2, x1:x2]
        if sample.size < 25 or np.percentile(sample, 95) - np.percentile(sample, 5) < 25:
            continue
        _, binary = cv2.threshold(sample, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Tekst to zwykle mniejszość pikseli; obsługujemy również jasne litery na czerni.
        if np.count_nonzero(binary) > sample.size / 2:
            binary = 255 - binary
        count, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
        # Letter components must sit on the dominant local paper/background.
        # Art fragments can be as small as letters, so size alone is insufficient.
        rgb_sample = np.asarray(image)[y1:y2, x1:x2].astype(np.int16)
        quantized = rgb_sample.astype(np.int32)//16
        codes = quantized[..., 0]*256 + quantized[..., 1]*16 + quantized[..., 2]
        values, frequencies = np.unique(codes, return_counts=True)
        dominant = codes == values[np.argmax(frequencies)]
        background = np.median(rgb_sample[dominant], axis=0)
        paper = np.max(np.abs(rgb_sample-background), axis=2) <= 32
        accepted = []
        for index in range(1, count):
            x, y, w, h, pixels = stats[index]
            # Loose detector boxes include arcs and background strokes at their
            # edges. Boundary-touching components are not reliable evidence.
            touches = x == 0 or y == 0 or x+w == sample.shape[1] or y+h == sample.shape[0]
            if touches:
                continue
            if 2 <= pixels <= sample.size * .12 and h >= 2 and w < sample.shape[1] * .85 and h < sample.shape[0] * .85:
                a,b,c,d = max(0,x-3),max(0,y-3),min(sample.shape[1],x+w+3),min(sample.shape[0],y+h+3)
                component = (labels[b:d,a:c] == index).astype(np.uint8)
                ring = (cv2.dilate(component, np.ones((5,5),np.uint8)) > 0) & (component == 0)
                if w > h*4:
                    continue
                if np.count_nonzero(paper[b:d,a:c] & ring) / max(1,np.count_nonzero(ring)) >= .80:
                    accepted.append(index)
        if len(accepted) >= 3:
            evidence[y1:y2, x1:x2] |= np.isin(labels, accepted).astype(np.uint8) * 255
            reliable += 1
    return evidence, reliable


def validate_candidate(mask, detection, texts, region, page_size, image):
    """Reject clipping and text loss while allowing genuine physical page boundaries."""
    mask = _fill((np.asarray(mask) > 0).astype(np.uint8) * 255)
    count = np.count_nonzero(mask)
    ratio = count / max(1, area(detection))
    if not count or not .18 <= ratio <= 1.8:
        return None, 'Rozmiar maski nie pasuje do dymka', {}
    width, height = page_size
    if ((region[0] > 0 and np.any(mask[:, 0])) or (region[1] > 0 and np.any(mask[0]))
            or (region[2] < width and np.any(mask[:, -1])) or (region[3] < height and np.any(mask[-1]))):
        return None, 'Maska ucięta na sztucznej granicy wycinka', {}
    # Usuwanie drobnych wysp musi poprzedzać walidację tekstu, inaczej mogłoby usunąć sprawdzone litery.
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    retained = [contour for contour in contours if cv2.contourArea(contour) >= max(12, count*.002)]
    clean = np.zeros_like(mask)
    cv2.drawContours(clean, retained, -1, 255, cv2.FILLED)
    mask = clean
    if not np.any(mask):
        return None, 'Brak istotnego konturu', {}
    # Include the physical ink stroke and antialiasing before checking letters.
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
    coverages = []
    for text in texts:
        evidence, reliable = ink_evidence(image, [text], region)
        if reliable:
            pixels = np.count_nonzero(evidence)
            coverage = np.count_nonzero((evidence > 0) & (mask > 0)) / max(1, pixels)
            coverages.append(coverage)
            if coverage < .975:
                return None, 'Maska ucina piksele wykrytego tekstu', {'ink_coverage': round(coverage, 4)}
        x1, y1, x2, y2 = text['box']
        cx, cy = round((x1+x2)/2-region[0]), round((y1+y2)/2-region[1])
        if not (0 <= cy < mask.shape[0] and 0 <= cx < mask.shape[1] and mask[cy, cx]):
            return None, 'Maska nie obejmuje środka bloku tekstu', {}
        # Gdy litery nie dają wiarygodnej maski, sprawdzamy wnętrze box, nie puste narożniki.
        if not reliable:
            dx, dy = (x2-x1)*.12, (y2-y1)*.12
            a, b = max(0, math.floor(x1+dx-region[0])), max(0, math.floor(y1+dy-region[1]))
            c, d = min(mask.shape[1], math.ceil(x2-dx-region[0])), min(mask.shape[0], math.ceil(y2-dy-region[1]))
            sample = mask[b:d, a:c]
            if not sample.size or np.count_nonzero(sample) / sample.size < .90:
                return None, 'Maska nie obejmuje wnętrza wykrytego tekstu', {}
    return mask, None, {
        'ink_coverage': round(min(coverages), 4) if coverages else None,
        'text_evidence': 'per-block-contrast+inner-box' if coverages else 'inner-box', 'area_ratio': round(ratio, 3)}


def prompt_points(detection, texts, region, image):
    """Choose foreground points within text and background points outside the detected box."""
    points, labels = [], []
    for text in texts[:8]:
        box = text['box']
        points.append([(box[0]+box[2])/2-region[0], (box[1]+box[3])/2-region[1]])
        labels.append(1)
    if not points:
        points.append([(detection[0]+detection[2])/2-region[0], (detection[1]+detection[3])/2-region[1]])
        labels.append(1)
    w, h = image.size
    for x, y in ((2, 2), (w-3, 2), (2, h-3), (w-3, h-3)):
        if not (detection[0] <= x+region[0] <= detection[2] and detection[1] <= y+region[1] <= detection[3]):
            points.append([max(0, x), max(0, y)])
            labels.append(0)
    return points, labels


def related_candidates(detection, candidates):
    return [item for item in candidates
            if intersection(detection, item['box']) / max(1, min(area(detection), area(item['box']))) > .65
            and .3 <= area(item['box']) / max(1, area(detection)) <= 3]


def prediction_items(prediction, origin, name, label_map, page_size=None):
    """Extract and crop native masks; never retain a full page tensor per balloon."""
    items = []
    for index, box in enumerate(prediction.boxes):
        label = label_map.get(int(box.cls.item()))
        if label is None:
            continue
        coords = box.xyxy[0].float().cpu().tolist()
        item = {'box': [coords[0]+origin[0], coords[1]+origin[1], coords[2]+origin[0], coords[3]+origin[1]],
                'score': float(box.conf.item()), 'label': label, 'method': name}
        if label == 'bubble' and prediction.masks is not None and index < len(prediction.masks.data):
            raw = (prediction.masks.data[index].cpu().numpy() > .5).astype(np.uint8)
            if raw.shape != tuple(prediction.orig_shape):
                raise ValueError('Model nie zwrócił masek w natywnej skali: wymagane retina_masks=True')
            if page_size and ((origin[0] > 0 and np.any(raw[:, 0])) or (origin[1] > 0 and np.any(raw[0]))
                    or (origin[0]+raw.shape[1] < page_size[0] and np.any(raw[:, -1]))
                    or (origin[1]+raw.shape[0] < page_size[1] and np.any(raw[-1]))):
                # Nie przenosimy uciętej maski z kafla; inny nakładający się kafel powinien ją objąć.
                continue
            points = cv2.findNonZero(raw)
            if points is not None:
                x, y, w, h = cv2.boundingRect(points)
                item.update(mask=raw[y:y+h, x:x+w].copy(), origin=(x+origin[0], y+origin[1]))
        items.append(item)
    return items
