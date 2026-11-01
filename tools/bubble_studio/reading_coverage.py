"""Reference-point coverage diagnostics, separate from physical-stop F1.

These points sample text blocks; they do not measure full-word OCR accuracy.
A split balloon can cover every point while failing one-region stop matching.
"""

import argparse
import hashlib
import json
from pathlib import Path

from .reading_benchmark import contains, score_page


def inspect_page(reference, document):
    score_page(reference, document)  # Complete reference and image identity.
    bodies = document["result"]["bubbles"]
    point_rows, uncovered, partial, fragmented = [], [], [], []
    owners_used = set()
    for index, utterance in enumerate(reference["utterances"], 1):
        owners = [
            {b["id"] for b in bodies if contains(b, p)} for p in utterance["points"]
        ]
        for point_index, (point, identities) in enumerate(
            zip(utterance["points"], owners), 1
        ):
            owners_used.update(identities)
            point_rows.append(
                dict(
                    utterance=index,
                    point_index=point_index,
                    point=point,
                    owners=sorted(identities),
                )
            )
        row = dict(utterance=index, label=utterance["label"])
        missing = [i + 1 for i, identities in enumerate(owners) if not identities]
        if len(missing) == len(owners):
            uncovered.append(row)
        elif missing:
            partial.append(dict(row, missing_point_indices=missing))
        elif not set.intersection(*owners):
            fragmented.append(row)
    return dict(
        sha_prefix=reference["sha_prefix"],
        name=reference["name"],
        reference_points=len(point_rows),
        covered_points=sum(bool(p["owners"]) for p in point_rows),
        fully_uncovered_stops=uncovered,
        partly_uncovered_stops=partial,
        fragmented_but_all_points_covered=fragmented,
        regions_without_reference_point=[
            b["id"] for b in bodies if b["id"] not in owners_used
        ],
        multiply_covered_points=[p for p in point_rows if len(p["owners"]) > 1],
        regions_covering_multiple_stops=[
            dict(
                region_id=b["id"],
                utterances=sorted(
                    {p["utterance"] for p in point_rows if b["id"] in p["owners"]}
                ),
            )
            for b in bodies
            if len({p["utterance"] for p in point_rows if b["id"] in p["owners"]}) > 1
        ],
        points=point_rows,
    )


def measure(reference, folder):
    expected = {p["sha_prefix"] for p in reference["pages"]}
    if len(expected) != len(reference["pages"]) or not expected:
        raise ValueError("Reference pages must be unique and nonempty")
    docs = {}
    for path in Path(folder).glob("*.json"):
        if path.name == "results.json":
            continue
        identity = next((key for key in expected if path.stem.endswith(key)), None)
        if identity is None or identity in docs:
            raise ValueError("Unexpected or duplicate result page")
        docs[identity] = json.loads(path.read_text(encoding="utf8"))
    if set(docs) != expected:
        raise ValueError("Every analyzed page must be retained")
    pages = [inspect_page(p, docs[p["sha_prefix"]]) for p in reference["pages"]]
    total = sum(p["reference_points"] for p in pages)
    covered = sum(p["covered_points"] for p in pages)
    return dict(
        schema=1,
        reference_sha256=hashlib.sha256(
            json.dumps(reference, sort_keys=True, ensure_ascii=False).encode("utf8")
        ).hexdigest(),
        limitations="Text-centre samples, not complete-word/character accuracy or a replacement for detection F1 and order. A wrong large mask may still cover a sample point.",
        overall=dict(
            pages=len(pages),
            reference_points=total,
            covered_points=covered,
            point_coverage=covered / total if total else None,
            fully_uncovered_stops=sum(len(p["fully_uncovered_stops"]) for p in pages),
            partly_uncovered_stops=sum(len(p["partly_uncovered_stops"]) for p in pages),
            fragmented_but_all_points_covered=sum(
                len(p["fragmented_but_all_points_covered"]) for p in pages
            ),
            regions_without_reference_point=sum(
                len(p["regions_without_reference_point"]) for p in pages
            ),
            regions_covering_multiple_stops=sum(
                len(p["regions_covering_multiple_stops"]) for p in pages
            ),
            multiply_covered_points=sum(
                len(p["multiply_covered_points"]) for p in pages
            ),
        ),
        pages=pages,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = measure(
        json.loads(args.reference.read_text(encoding="utf8")), args.results
    )
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8"
    )


if __name__ == "__main__":
    main()
