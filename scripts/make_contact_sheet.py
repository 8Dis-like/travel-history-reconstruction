from __future__ import annotations

"""Build a contact sheet (grid of thumbnails + captions) from labels_source.csv.

Used for the human review gate: the user eyeballs each stamp against its
proposed date / country / direction before the rotation test set is built.

Run with:
    python scripts/make_contact_sheet.py \
        --source-csv data/rotation_testset/labels_source.csv \
        --preview-dir data/rotation_testset/_candidates_preview \
        --out /tmp/rotation_testset_contact_sheet.png
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

CELL_W = 360
THUMB_H = 220
CAP_H = 78
COLS = 5
PAD = 10
FONT = cv2.FONT_HERSHEY_SIMPLEX


def fit_letterbox(img: np.ndarray, w: int, h: int) -> np.ndarray:
    ih, iw = img.shape[:2]
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((h, w, 3), 245, np.uint8)
    y0, x0 = (h - nh) // 2, (w - nw) // 2
    canvas[y0 : y0 + nh, x0 : x0 + nw] = resized
    return canvas


def make_cell(img: np.ndarray, line1: str, line2: str) -> np.ndarray:
    cell = np.full((THUMB_H + CAP_H, CELL_W, 3), 255, np.uint8)
    cell[:THUMB_H] = fit_letterbox(img, CELL_W, THUMB_H)
    cv2.line(cell, (0, THUMB_H), (CELL_W, THUMB_H), (210, 210, 210), 1)
    cv2.putText(cell, line1, (8, THUMB_H + 28), FONT, 0.62, (20, 20, 20), 2, cv2.LINE_AA)
    cv2.putText(cell, line2, (8, THUMB_H + 60), FONT, 0.58, (140, 40, 40), 1, cv2.LINE_AA)
    return cell


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-csv", default="data/rotation_testset/labels_source.csv")
    ap.add_argument("--preview-dir", default="data/rotation_testset/_candidates_preview")
    ap.add_argument("--out", default="/tmp/rotation_testset_contact_sheet.png")
    args = ap.parse_args()

    preview_dir = Path(args.preview_dir)
    with open(args.source_csv, newline="") as f:
        rows = [r for r in csv.DictReader(f)]

    cells = []
    for r in rows:
        img = cv2.imread(str(preview_dir / f"{r['stamp_id']}.png"))
        if img is None:
            img = np.full((THUMB_H, CELL_W, 3), 230, np.uint8)
        line1 = f"{r['stamp_id']}  {r['date'] or '?'}"
        direction = r["direction"] or "-"
        line2 = f"{r['country'] or '?'}  {direction}  ({r['label_confidence']})"
        cells.append(make_cell(img, line1, line2))

    rows_n = (len(cells) + COLS - 1) // COLS
    cell_h, cell_w = cells[0].shape[:2]
    sheet_w = COLS * cell_w + (COLS + 1) * PAD
    sheet_h = rows_n * cell_h + (rows_n + 1) * PAD
    sheet = np.full((sheet_h, sheet_w, 3), 255, np.uint8)

    for i, cell in enumerate(cells):
        rr, cc = divmod(i, COLS)
        y = PAD + rr * (cell_h + PAD)
        x = PAD + cc * (cell_w + PAD)
        sheet[y : y + cell_h, x : x + cell_w] = cell

    cv2.imwrite(args.out, sheet)
    print(f"contact sheet ({len(cells)} stamps) -> {args.out}")


if __name__ == "__main__":
    main()
