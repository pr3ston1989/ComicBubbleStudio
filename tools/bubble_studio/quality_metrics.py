"""Reviewable corpus metrics. Model confidence is never a correctness label."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .reading_benchmark import evaluate


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf8')).hexdigest()


def geometry_digest(region):
    return digest({k: region.get(k) for k in ('type', 'x', 'y', 'w', 'h', 'polygon', 'polygons')})


def aggregate(pages):
    tp = sum(p['matched_stops'] for p in pages)
    fn = sum(len(p['missing']) for p in pages)
    fp = sum(len(p['extra_regions']) for p in pages)
    pairs = sum(p['order_pairs'] for p in pages)
    wrong = sum(p['incorrect_order_pairs'] for p in pages)
    accepted = sum(p['contours_accepted'] for p in pages)
    rejected = sum(p['contours_rejected'] for p in pages)
    unknown = sum(p['contours_unreviewed'] for p in pages)
    f1 = 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None
    order = (pairs - wrong) / pairs if pairs else None
    contour = accepted / (accepted + rejected) if accepted + rejected else None
    # Incomplete review must not silently inflate the combined percentage.
    combined = (f1 * order * contour) ** (1 / 3) if not unknown and all(
        v is not None for v in (f1, order, contour)) else None
    return {'pages': len(pages), 'reference_stops': tp + fn, 'predicted_stops': tp + fp,
            'true_positives': tp, 'false_positives': fp, 'false_negatives': fn,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None, 'detection_f1': f1,
            'order_pairs': pairs, 'incorrect_order_pairs': wrong, 'order_agreement': order,
            'contours_accepted': accepted, 'contours_rejected': rejected,
            'contours_unreviewed': unknown, 'contour_acceptance': contour,
            'contour_review_coverage': (accepted + rejected) / tp if tp else None,
            'combined_estimate': combined,
            'complete_reading_pages': sum(p['complete_reading_success'] for p in pages),
            'fully_accepted_pages': sum(p['fully_accepted'] for p in pages)}


def measure(reference, contours, folder):
    identities=[p['sha_prefix'] for p in reference['pages']]
    if not identities or len(set(identities))!=len(identities):
        raise ValueError('Reference pages must be nonempty and unique')
    reading = evaluate(reference, folder)
    expected = {p['sha_prefix'] for p in reference['pages']}
    docs = {}
    for path in folder.glob('*.json'):
        if path.name == 'results.json':
            continue
        key = next((s for s in expected if path.stem.endswith(s)), None)
        if key is None or key in docs:
            raise ValueError('Unexpected or duplicated result page: ' + path.name)
        docs[key] = json.loads(path.read_text(encoding='utf8'))
    if docs.keys() != expected:
        raise ValueError('All analyzed pages must have a complete reference and result')
    reviews = {p['sha_prefix']: p for p in contours['pages']}
    if len(reviews) != len(contours['pages']) or reviews.keys() != expected:
        raise ValueError('Contour review must identify every analyzed page exactly once')
    for page in reading['pages']:
        doc = docs[page['sha_prefix']]; review = reviews[page['sha_prefix']]
        if (review['image_sha256'] != doc['lab']['sha256'] or
                review['size'] != [doc['result']['width'], doc['result']['height']]):
            raise ValueError('Contour review belongs to a different image')
        labels = {}
        for row in review['regions']:
            if type(row['accepted']) is not bool:
                raise ValueError('Visual verdict must be an explicit boolean')
            labels.setdefault(row['geometry_sha256'], []).append(row['accepted'])
        regions = {r['id']: r for r in doc['result']['bubbles']}
        verdicts = []
        excluded = {p['predicted_region'] for p in page['outline_exclusion_failures']}
        for stop in page['sequence']:
            identity = stop['predicted_region']
            if identity is None:
                continue
            candidates = labels.get(geometry_digest(regions[identity]), [])
            # Duplicate identical geometries with conflicting labels are unknown.
            verdict = candidates[0] if candidates and len(set(candidates)) == 1 else None
            if identity in excluded:
                verdict = False
            verdicts.append({'region_id': identity, 'accepted': verdict})
        page['contour_verdicts'] = verdicts
        page['contours_accepted'] = sum(v['accepted'] is True for v in verdicts)
        page['contours_rejected'] = sum(v['accepted'] is False for v in verdicts)
        page['contours_unreviewed'] = sum(v['accepted'] is None for v in verdicts)
        page['incorrect_order_pairs'] = (page['order_inversions'] if page['direction_matches']
            and not page['invalid_order_metadata'] else page['order_pairs'])
        page['fully_accepted'] = (page['complete_reading_success'] and
            not page['contours_rejected'] and not page['contours_unreviewed'])
    pages = reading['pages']
    return {'schema': 1, 'reference_sha256': reading['reference_sha256'],
            'contour_review_sha256': digest(contours), 'scope': reference['scope'],
            'method': {'detection': 'Micro F1 = 2TP/(2TP+FP+FN), one-to-one spatial stop matching.',
                       'contours': 'Visual acceptance of matched true regions; geometry fingerprints bind each verdict. Not pixel IoU.',
                       'order': 'Correct pairs among matched stops; missing stops are penalized by detection F1. Direction/metadata errors reject all page pairs.',
                       'combined': 'Equal-weight geometric mean of detection F1, contour acceptance and order agreement. No combined score while matched contours remain unreviewed.',
                       'limitations': 'Agent visual annotations, not independent expert truth. Connected balloons are ordered by their first lobe; internal interleaving is not measured. No OCR character/transcription accuracy measurement.'},
            'coverage': {'analyzed_pages': len(docs), 'fully_annotated_pages': len(pages),
                         'page_fraction': len(pages) / len(docs) if docs else None},
            'overall': aggregate(pages),
            'by_direction': {d: aggregate([p for p in pages if p['direction'] == d]) for d in ('ltr', 'rtl')},
            'pages': pages}


def compare_metrics(before, after):
    errors = []
    for key in ('reference_sha256', 'contour_review_sha256'):
        if not before.get(key) or before[key] != after.get(key):
            errors.append('Different assessment definitions: ' + key)
    old = {p['sha_prefix']: p for p in before['pages']}
    new = {p['sha_prefix']: p for p in after['pages']}
    if old.keys() != new.keys():
        errors.append('Different assessed page sets')
    for key in old.keys() & new.keys():
        a, b = old[key], new[key]
        for field in ('contours_rejected', 'contours_unreviewed', 'incorrect_order_pairs'):
            if b[field] > a[field]:
                errors.append(key + ': worse ' + field)
        for field in ('missing', 'extra_regions'):
            if len(b[field]) > len(a[field]):
                errors.append(key + ': worse ' + field)
    return {'passed': not errors, 'pages': len(old), 'errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Procentowa ocena wszystkich opisanych stron')
    for key in ('reference', 'contours', 'results', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args(argv)
    result = measure(json.loads(args.reference.read_text(encoding='utf8')),
                     json.loads(args.contours.read_text(encoding='utf8')), args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result['overall'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
