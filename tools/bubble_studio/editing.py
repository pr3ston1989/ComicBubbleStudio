"""Pure manual contour operations, independent of Tk and inference dependencies."""

import math


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _intersect(a, b, c, d):
    sides = (_cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b))
    if sides[0]*sides[1] < 0 and sides[2]*sides[3] < 0:
        return True
    for value, point, p, q in ((sides[0], c, a, b), (sides[1], d, a, b), (sides[2], a, c, d), (sides[3], b, c, d)):
        if abs(value) < 1e-10 and min(p[0], q[0])-1e-10 <= point[0] <= max(p[0], q[0])+1e-10 and min(p[1], q[1])-1e-10 <= point[1] <= max(p[1], q[1])+1e-10:
            return True
    return False


def polygon_box(points, identifier, confidence=1):
    """Convert page-normalized vertices to a bounded local polygon without smoothing."""
    vertices = []
    for x, y in points:
        if not (math.isfinite(x) and math.isfinite(y) and 0 <= x <= 1 and 0 <= y <= 1):
            raise ValueError('Punkt konturu poza stroną')
        if not vertices or abs(x-vertices[-1][0]) + abs(y-vertices[-1][1]) > 1e-7:
            vertices.append((x, y))
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices.pop()
    if not 3 <= len(vertices) <= 512:
        raise ValueError('Kontur wymaga od 3 do 512 różnych punktów')
    for i in range(len(vertices)):
        for j in range(i+2, len(vertices)):
            if i == 0 and j == len(vertices)-1:
                continue
            if _intersect(vertices[i], vertices[(i+1) % len(vertices)], vertices[j], vertices[(j+1) % len(vertices)]):
                raise ValueError('Krawędzie konturu przecinają się — popraw punkty')
    signed_area = sum(x*vertices[(i+1) % len(vertices)][1] - y*vertices[(i+1) % len(vertices)][0]
                      for i, (x, y) in enumerate(vertices)) / 2
    if abs(signed_area) < .000001:
        raise ValueError('Kontur jest zbyt mały lub zdegenerowany')
    x1, y1 = min(x for x, _ in vertices), min(y for _, y in vertices)
    x2, y2 = max(x for x, _ in vertices), max(y for _, y in vertices)
    polygon = [{'x': (x-x1)/(x2-x1), 'y': (y-y1)/(y2-y1)} for x, y in vertices]
    return {'id': identifier, 'x': x1, 'y': y1, 'w': x2-x1, 'h': y2-y1, 'polygons': [polygon],
            'polygon': polygon, 'type': 'bubble', 'source': 'external', 'confidence': confidence}
