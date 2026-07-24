from __future__ import annotations

"""Evaluate the pipeline end-to-end on the synthetic-scene test set.

For each ground-truth stamp in each scene, crop the scene at its true box, run
the OCR extractor, and score:

  - OCR field accuracy (date / country / direction), split by whether the stamp
    was rotated or placed upright;
  - timeline-order accuracy — do the predicted dates keep the stamps in the
    correct chronological order (via pairwise_order_accuracy).

Cropping at the ground-truth boxes isolates OCR + timeline from the detector
(which is still a mock). Once a real YOLO detector is wired in, the same scenes
and ground truth support a full detection + OCR eval.

Run:
  ANTHROPIC_API_KEY=sk-... python scripts/eval_synthetic_scenes.py
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reconstruction.scene_eval import pairwise_order_accuracy  # noqa: E402
from src.reconstruction.timeline import TimelineEvent, build_timeline  # noqa: E402

FIELDS = ["date", "country", "direction"]


def _norm(v):
    return (v or "").strip().upper() or None


def run_eval(metadata: list[dict], root: Path, extractor, limit: int = 0):
    """Crop each GT stamp, extract, and return (rows, summary)."""
    rows = []
    scenes = metadata[:limit] if limit else metadata

    for scene in scenes:
        img = cv2.imread(str(root / "images" / scene["image"]))
        if img is None:
            print(f"  skip (missing image): {scene['image']}")
            continue
        for st in scene["stamps"]:
            x1, y1, x2, y2 = st["bbox_xyxy"]
            crop = img[y1:y2, x1:x2]
            res = extractor.extract(crop)
            rows.append({
                "image": scene["image"],
                "stamp_id": st["stamp_id"],
                "rotated": st["rotation"] != 0.0,
                "gt_date": st["date"], "got_date": res.date,
                "gt_country": st["country"], "got_country": res.country,
                "gt_direction": st["direction"], "got_direction": res.direction,
            })

    return rows, _summarize(rows)


def _field_acc(rows, field, subset=None):
    n_ok = n_tot = 0
    for r in rows:
        if subset is not None and r["rotated"] != subset:
            continue
        gt = _norm(r[f"gt_{field}"])
        if gt is None:
            continue
        n_tot += 1
        n_ok += int(_norm(r[f"got_{field}"]) == gt)
    return n_ok, n_tot


def _summarize(rows):
    summary = {"n_stamps": len(rows), "fields": {}}
    for field in FIELDS:
        summary["fields"][field] = {
            "all": _field_acc(rows, field),
            "upright": _field_acc(rows, field, subset=False),
            "rotated": _field_acc(rows, field, subset=True),
        }
    # timeline order across all placed stamps
    pairs = [(r["gt_date"], r["got_date"]) for r in rows]
    summary["timeline_order"] = pairwise_order_accuracy(pairs)
    return summary


def _pct(ok_tot):
    ok, tot = ok_tot
    return f"{(ok / tot if tot else 0):>5.0%} ({ok}/{tot})"


def print_report(summary):
    print("\n=== OCR field accuracy (correct/scorable) ===")
    print(f"{'field':>10} {'all':>14} {'upright':>14} {'rotated':>14}")
    for field in FIELDS:
        f = summary["fields"][field]
        print(f"{field:>10} {_pct(f['all']):>14} {_pct(f['upright']):>14} {_pct(f['rotated']):>14}")
    print(f"\ntimeline-order accuracy (pairwise): {summary['timeline_order']:.0%}")
    print(f"stamps evaluated: {summary['n_stamps']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/synthetic_scenes")
    ap.add_argument("--out", default="", help="optional per-stamp results CSV")
    ap.add_argument("--limit", type=int, default=0, help="only evaluate the first N scenes")
    args = ap.parse_args()

    from src.ocr.factory import create_extractor_from_config
    root = Path(args.root)
    metadata = json.load(open(root / "metadata.json"))
    extractor = create_extractor_from_config()

    rows, summary = run_eval(metadata, root, extractor, limit=args.limit)
    print_report(summary)

    if args.out and rows:
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"per-stamp results -> {args.out}")

    # show the predicted timeline order as a sanity check
    events = build_timeline(
        TimelineEvent(date=r["got_date"], country=r["got_country"],
                      direction=r["got_direction"], stamp_id=r["stamp_id"],
                      source_image=r["image"])
        for r in rows
    )
    print(f"\npredicted timeline: {len(events.events)} placed, {len(events.undated)} undated")


if __name__ == "__main__":
    main()
