"""Segment native balloon ink with bounded, text-seeded graph cuts."""

import math, time
import numpy as np, cv2
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow, breadth_first_order
from .geometry import padded_box, contour_box, _fill
from .compound_guard import _texts
from .textcheck import pixel_box


def cut(image, roi, texts, area_weight=1, max_pixels=180000, texture_cap=64):
    crop = np.asarray(image.crop(roi))
    h, w = crop.shape[:2]
    scale = min(1, 800 / max(w, h), math.sqrt(max_pixels / (w * h)))
    size = max(8, round(w * scale)), max(8, round(h * scale))
    rgb = cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
    height, width = rgb.shape[:2]
    n = height * width
    colours = []
    blocks = []
    for t in texts:
        x, y, xx, yy = t["box"]
        x, y = (
            int(math.floor((x - roi[0]) * scale)),
            int(math.floor((y - roi[1]) * scale)),
        )
        xx, yy = (
            int(math.ceil((xx - roi[0]) * scale)),
            int(math.ceil((yy - roi[1]) * scale)),
        )
        if min(x, y) < 2 or xx >= width - 2 or yy >= height - 2 or xx <= x or yy <= y:
            return None
        blocks.append((x, y, xx, yy))
        pad = max(2, round(6 * scale))
        a, b, c, d = (
            max(0, x - pad),
            max(0, y - pad),
            min(width, xx + pad),
            min(height, yy + pad),
        )
        patch = rgb[b:d, a:c]
        ring = np.ones(patch.shape[:2], bool)
        ring[y - b : yy - b, x - a : xx - a] = False
        pixels = patch[ring]
        if not len(pixels):
            return None
        code = pixels.astype(np.int32) // 16
        code = code[:, 0] * 256 + code[:, 1] * 16 + code[:, 2]
        v, hits = np.unique(code, return_counts=True)
        colours.append(np.median(pixels[code == v[np.argmax(hits)]], axis=0))
    colour = np.median(colours, axis=0)
    if max(float(np.max(np.abs(c - colour))) for c in colours) > 48:
        return None
    diff = np.max(np.abs(rgb.astype(np.float32) - colour), axis=2)
    foreground = np.zeros((height, width), bool)
    for x, y, xx, yy in blocks:
        patch = diff[y:yy, x:xx] <= 40
        if np.mean(patch) < 0.12:
            return None
        foreground[y:yy, x:xx] |= patch
    background = np.zeros_like(foreground)
    background[:2] = True
    background[-2:] = True
    background[:, :2] = True
    background[:, -2:] = True
    if np.any(background & foreground):
        return None
    nodes = np.arange(n, dtype=np.int32).reshape(height, width)
    rows = []
    cols = []
    weights = []
    # Penalize cutting through smooth paper; native ink is a cheap barrier.
    for a, b, delta in [
        (
            nodes[:, :-1],
            nodes[:, 1:],
            rgb[:, :-1].astype(np.float32) - rgb[:, 1:].astype(np.float32),
        ),
        (
            nodes[:-1],
            nodes[1:],
            rgb[:-1].astype(np.float32) - rgb[1:].astype(np.float32),
        ),
    ]:
        distance = np.max(np.abs(delta), axis=2)
        cap = (
            (1 + np.rint(4095 * np.exp(-(distance**2) / (2 * 16**2))))
            .astype(np.int32)
            .ravel()
        )
        ar = a.ravel()
        br = b.ravel()
        rows.extend([ar, br])
        cols.extend([br, ar])
        weights.extend([cap, cap])
    source, sink = n, n + 1
    fg = np.flatnonzero(foreground)
    bg = np.flatnonzero(background)
    rows.extend([np.full(len(fg), source, np.int32), bg, nodes.ravel()])
    cols.extend([fg, np.full(len(bg), sink, np.int32), np.full(n, sink, np.int32)])
    smooth = cv2.GaussianBlur(rgb.astype(np.float32), (5, 5), 1.2)
    deviation = np.max(np.abs(smooth - colour), axis=2)
    penalty = np.minimum(texture_cap, np.rint((deviation / 8) ** 4))
    for x, y, xx, yy in blocks:
        penalty[y:yy, x:xx] = 0
    unary = (area_weight + penalty).astype(np.int32).ravel()
    weights.extend(
        [
            np.full(len(fg), 10000000, np.int32),
            np.full(len(bg), 10000000, np.int32),
            unary,
        ]
    )
    graph = csr_matrix(
        (np.concatenate(weights), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n + 2, n + 2),
        dtype=np.int32,
    )
    start = time.monotonic()
    flow = maximum_flow(graph, source, sink, method="dinic")
    residual = graph - flow.flow
    residual.data[residual.data <= 0] = 0
    residual.eliminate_zeros()
    reachable = breadth_first_order(
        residual, source, directed=True, return_predecessors=False
    )
    mask = np.zeros(n + 2, np.uint8)
    mask[reachable] = 1
    mask = mask[:n].reshape(height, width)
    # Require one real foreground component to contain paper from every block.
    _, labels = cv2.connectedComponents(mask, 8)
    common = None
    for x, y, xx, yy in blocks:
        v, hits = np.unique(labels[y:yy, x:xx], return_counts=True)
        ids = {
            int(k)
            for k, count in zip(v, hits)
            if k and count > max(2, 0.10 * ((xx - x) * (yy - y)))
        }
        common = ids if common is None else common & ids
    if not common:
        return None
    key = max(common, key=lambda k: np.sum(labels == k))
    mask = (labels == key).astype(np.uint8)
    mask = (_fill(mask * 255) > 0).astype(np.uint8)
    if (
        np.mean(mask) > 0.80
        or np.any(mask[:2])
        or np.any(mask[-2:])
        or np.any(mask[:, :2])
        or np.any(mask[:, -2:])
    ):
        return None
    native = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    native = cv2.dilate(native, np.ones((3, 3), np.uint8))
    region = contour_box(native, roi, *image.size, 0.95, epsilon=0.1, max_vertices=2048)
    return region, dict(
        method="text-seeded-native-ink-mincut",
        texture_cap=texture_cap,
        area_weight=area_weight,
        scale=scale,
        paper_rgb=colour.tolist(),
        flow=int(flow.flow_value),
        seconds=round(time.monotonic() - start, 3),
    )


def roi_for(image, document, members):
    boxes = [pixel_box(b, image.size) for b in members] + [
        t["box"] for b in members for t in _texts(image, document, b)
    ]
    x, y = min(b[0] for b in boxes), min(b[1] for b in boxes)
    xx, yy = max(b[2] for b in boxes), max(b[3] for b in boxes)
    pad = max(
        35,
        round(
            max(xx - x, yy - y)
            * (0.6 if any(not b.get("polygons") for b in members) else 0.3)
        ),
    )
    return padded_box([x, y, xx, yy], *image.size, 0, minimum=pad)
