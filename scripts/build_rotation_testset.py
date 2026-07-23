from __future__ import annotations

"""Build the rotation-robustness test set from an approved labels_source.csv.

For each accepted stamp, rotate its full-res candidate crop to every angle and
write the images plus a per-image labels.csv. Labeling (labels_source.csv) and
evaluation (eval_rotation_testset.py) are decoupled from this step.

See docs/superpowers/specs/2026-07-20-rotation-robustness-testset-design.md

Run with:
    python scripts/build_rotation_testset.py
"""

import argparse
import csv
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.rotation import rotate_image  # noqa: E402

DEFAULT_ANGLES = [0, 20, 45, 75, 90, 180, 220]


def parse_angles(text: str) -> list[int]:
    return [int(a) for a in text.split(",") if a.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-csv", default="data/rotation_testset/labels_source.csv")
    ap.add_argument("--candidates-dir", default="data/rotation_testset/_candidates")
    ap.add_argument("--out", default="data/rotation_testset")
    ap.add_argument("--angles", default=",".join(str(a) for a in DEFAULT_ANGLES))
    args = ap.parse_args()

    angles = parse_angles(args.angles)
    candidates = Path(args.candidates_dir)
    out = Path(args.out)
    images_dir = out / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    with open(args.source_csv, newline="") as f:
        rows = [r for r in csv.DictReader(f)]

    out_rows: list[dict[str, object]] = []
    n_written = 0
    for r in rows:
        stamp_id = r["stamp_id"]
        # inclusion threshold: date + country must be present
        if not (r["date"].strip() and r["country"].strip()):
            print(f"  skip (no date+country): {stamp_id}")
            continue

        src = candidates / f"{stamp_id}.png"
        original = cv2.imread(str(src))
        if original is None:
            print(f"  skip (candidate image missing): {src}")
            continue

        for angle in angles:
            rotated = original.copy() if angle == 0 else rotate_image(original, angle)
            name = f"{stamp_id}_rot{angle:03d}.png"
            cv2.imwrite(str(images_dir / name), rotated)
            n_written += 1
            out_rows.append(
                {
                    "image_path": f"images/{name}",
                    "stamp_id": stamp_id,
                    "source_file": r["source_file"],
                    "angle": angle,
                    "gt_date": r["date"],
                    "gt_country": r["country"],
                    "gt_direction": r["direction"],
                    "label_confidence": r["label_confidence"],
                }
            )

    labels_path = out / "labels.csv"
    fieldnames = [
        "image_path",
        "stamp_id",
        "source_file",
        "angle",
        "gt_date",
        "gt_country",
        "gt_direction",
        "label_confidence",
    ]
    with open(labels_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    n_stamps = len({row["stamp_id"] for row in out_rows})
    print(f"built {n_written} images from {n_stamps} stamps x {len(angles)} angles")
    print(f"images -> {images_dir}")
    print(f"labels -> {labels_path}")


if __name__ == "__main__":
    main()
