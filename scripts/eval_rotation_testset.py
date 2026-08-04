from __future__ import annotations

"""Evaluate the OCR extractor on the rotation-robustness test set.

Reads labels.csv, runs the configured extractor on each rotated image, and
reports per-field accuracy broken down by rotation angle. Scoring is per-field
and only counts stamps whose ground truth for that field is non-null, so a stamp
with no printed direction never penalizes the direction score.

Re-runnable against any configured model (swap ocr provider/model in
configs/pipeline.yaml). Read-only with respect to the test set.

See docs/superpowers/specs/2026-07-20-rotation-robustness-testset-design.md

Run with:
    ANTHROPIC_API_KEY=sk-... python scripts/eval_rotation_testset.py
(or rely on the .env file at repo root, which is loaded automatically)
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import cv2
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ocr.factory import create_extractor_from_config  # noqa: E402

FIELDS = ["date", "country", "direction"]


def norm(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip().upper()
    return v or None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="data/rotation_testset/labels.csv")
    ap.add_argument("--root", default="data/rotation_testset")
    ap.add_argument("--out", default="", help="optional path to write per-image results CSV")
    ap.add_argument("--limit", type=int, default=0, help="only evaluate the first N images (smoke test)")
    args = ap.parse_args()

    root = Path(args.root)
    with open(args.labels, newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    if args.limit:
        rows = rows[: args.limit]

    extractor = create_extractor_from_config()

    # angle -> field -> [n_correct, n_scorable]
    tally: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {fld: [0, 0] for fld in FIELDS + ["combined"]}
    )
    results: list[dict[str, object]] = []

    for i, r in enumerate(rows, 1):
        angle = int(r["angle"])
        img = cv2.imread(str(root / r["image_path"]))
        if img is None:
            print(f"  skip (image missing): {r['image_path']}")
            continue

        res = extractor.extract(img)
        got = {"date": res.date, "country": res.country, "direction": res.direction}
        gt = {"date": r["gt_date"], "country": r["gt_country"], "direction": r["gt_direction"]}

        per_field_correct: dict[str, bool | None] = {}
        combined_scorable = False
        combined_correct = True
        for fld in FIELDS:
            gt_val = norm(gt[fld])
            if gt_val is None:
                per_field_correct[fld] = None  # not scored for this stamp
                continue
            ok = norm(got[fld]) == gt_val
            per_field_correct[fld] = ok
            tally[angle][fld][0] += int(ok)
            tally[angle][fld][1] += 1
            combined_scorable = True
            combined_correct = combined_correct and ok

        if combined_scorable:
            tally[angle]["combined"][0] += int(combined_correct)
            tally[angle]["combined"][1] += 1

        def mark(fld: str) -> str:
            v = per_field_correct[fld]
            return "-" if v is None else ("OK" if v else "X")

        print(
            f"[{i:>3}/{len(rows)}] {r['stamp_id']:>10} {angle:>3}deg  "
            f"date {mark('date')}  country {mark('country')}  direction {mark('direction')}  "
            f"| got date={got['date']!r} country={got['country']!r} direction={got['direction']!r}"
        )
        results.append(
            {
                "image_path": r["image_path"],
                "stamp_id": r["stamp_id"],
                "angle": angle,
                "gt_date": gt["date"],
                "got_date": got["date"],
                "gt_country": gt["country"],
                "got_country": got["country"],
                "gt_direction": gt["direction"],
                "got_direction": got["direction"],
                "confidence": res.confidence,
            }
        )

    print("\n=== Accuracy by rotation angle (correct/scorable) ===")
    header = f"{'angle':>6}  " + "  ".join(f"{fld:>10}" for fld in FIELDS + ["combined"])
    print(header)
    for angle in sorted(tally):
        cells = []
        for fld in FIELDS + ["combined"]:
            n_ok, n_tot = tally[angle][fld]
            cells.append(f"{(n_ok / n_tot if n_tot else 0):>6.0%}({n_tot:>2})" if n_tot else f"{'-':>10}")
        print(f"{angle:>5}deg  " + "  ".join(f"{c:>10}" for c in cells))
    print("\n(percentages are per-field, over stamps with a non-null ground-truth label for that field)")

    if args.out:
        fieldnames = list(results[0].keys()) if results else []
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(results)
        print(f"\nper-image results -> {args.out}")


if __name__ == "__main__":
    main()
