from __future__ import annotations

"""Sample candidate stamp crops from the cleaned_stamps_and_bgs zip for labeling.

Produces a reproducible candidate set (full-res, flattened onto white so it
matches the white fill used when rotating), downscaled previews for quick visual
labeling, and a blank label CSV template.

The stamp order is a seeded shuffle of *all* stamps, so increasing --k only
appends more candidates from the same ordering (reproducible + extensible).

See docs/superpowers/specs/2026-07-20-rotation-robustness-testset-design.md

Run with:
    python scripts/sample_stamps.py --k 48 --seed 42
"""

import argparse
import csv
import random
import zipfile
from pathlib import Path

import cv2
import numpy as np

STAMP_PREFIX = "clean_stamps_cropped/"


def list_stamps(zf: zipfile.ZipFile) -> list[str]:
    return sorted(
        n
        for n in zf.namelist()
        if n.startswith(STAMP_PREFIX)
        and n.lower().endswith(".png")
        and not Path(n).name.startswith("._")
    )


def flatten_on_white(img: np.ndarray | None) -> np.ndarray | None:
    """Composite any alpha channel onto a white background; return BGR uint8."""
    if img is None:
        return None
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        bgr = img[:, :, :3].astype(np.float32)
        alpha = img[:, :, 3:4].astype(np.float32) / 255.0
        white = np.full_like(bgr, 255.0)
        return (bgr * alpha + white * (1.0 - alpha)).astype(np.uint8)
    return img


def downscale(img: np.ndarray, max_dim: int) -> np.ndarray:
    h, w = img.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(Path.home() / "Downloads" / "cleaned_stamps_and_bgs.zip"))
    ap.add_argument("--out", default="data/rotation_testset")
    ap.add_argument("--k", type=int, default=48)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--preview-max", type=int, default=768)
    args = ap.parse_args()

    out = Path(args.out)
    cand = out / "_candidates"
    prev = out / "_candidates_preview"
    cand.mkdir(parents=True, exist_ok=True)
    prev.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.zip) as zf:
        stamps = list_stamps(zf)
        order = stamps[:]
        random.Random(args.seed).shuffle(order)
        picked = order[: args.k]

        rows: list[str] = []
        for name in picked:
            stamp_id = Path(name).stem
            arr = cv2.imdecode(np.frombuffer(zf.read(name), np.uint8), cv2.IMREAD_UNCHANGED)
            full = flatten_on_white(arr)
            if full is None:
                print(f"  skip (decode failed): {name}")
                continue
            cv2.imwrite(str(cand / f"{stamp_id}.png"), full)
            cv2.imwrite(str(prev / f"{stamp_id}.png"), downscale(full, args.preview_max))
            rows.append(stamp_id)

    csv_path = out / "labels_source.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stamp_id", "source_file", "date", "country", "direction", "label_confidence", "note"])
        for stamp_id in rows:
            w.writerow([stamp_id, f"{STAMP_PREFIX}{stamp_id}.png", "", "", "", "", ""])

    print(f"extracted {len(rows)} candidates -> {cand}")
    print(f"previews             -> {prev}")
    print(f"label template       -> {csv_path}")


if __name__ == "__main__":
    main()
