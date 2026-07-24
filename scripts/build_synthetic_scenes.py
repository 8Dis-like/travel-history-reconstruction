from __future__ import annotations

"""Build a full-pipeline synthetic test set: paste hand-labeled stamps onto fake
passport backgrounds, carrying BOTH detection ground truth (bounding boxes) and
OCR ground truth (date / country / direction) for every pasted stamp.

Unlike the existing training synthetic_dataset (geometry only), each stamp here
records which labeled stamp it is and what it should read, so the same scenes
can evaluate detection, OCR, and timeline ordering end to end.

Inputs
  - passport backgrounds from cleaned_stamps_and_bgs.zip (backgrounds/passport_backgrounds/)
  - the labeled stamps: labels_source.csv (date/country/direction) + the RGBA
    originals in the same zip (clean_stamps_cropped/<stamp_id>.png)

Outputs (data/synthetic_scenes/)
  images/scene_00000.jpg        composited page
  yolo_detect/scene_00000.txt   YOLO detection labels (class xc yc w h, normalized)
  metadata.json                 full ground truth (bbox + date/country/direction per stamp)

Run:
  python scripts/build_synthetic_scenes.py --n 30 --seed 42
"""

import argparse
import csv
import io
import json
import random
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

BG_PREFIX = "backgrounds/passport_backgrounds/"
STAMP_PREFIX = "clean_stamps_cropped/"
STAMP_CLASS = 0  # single detection class: "stamp"


def load_labels(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        rows = [r for r in csv.DictReader(f)]
    # only stamps that meet the inclusion bar (date + country readable)
    return [r for r in rows if r["date"].strip() and r["country"].strip()]


def list_backgrounds(zf: zipfile.ZipFile) -> list[str]:
    return sorted(
        n for n in zf.namelist()
        if n.startswith(BG_PREFIX) and n.lower().endswith((".png", ".jpg", ".jpeg"))
        and not Path(n).name.startswith("._")
    )


def open_rgba(zf: zipfile.ZipFile, name: str) -> Image.Image:
    return Image.open(io.BytesIO(zf.read(name))).convert("RGBA")


def iou(a: list[int], b: list[int]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def transform_stamp(stamp: Image.Image, bg_w: int, rng: random.Random, args):
    """Scale + (maybe) rotate + fade a stamp. Returns (rgba, rotation, scale, opacity).

    A fraction of stamps (1 - args.rotate_prob) are left upright (rotation 0.0)
    so the scenes contain a mix of rotated and non-rotated stamps.
    """
    scale = rng.uniform(args.scale_min, args.scale_max)
    target_w = max(24, int(scale * bg_w))
    ratio = target_w / stamp.width
    stamp = stamp.resize((target_w, max(24, int(stamp.height * ratio))), Image.LANCZOS)

    if rng.random() < args.rotate_prob:
        rotation = rng.uniform(-args.rotation, args.rotation)
        stamp = stamp.rotate(rotation, expand=True, resample=Image.BICUBIC)
    else:
        rotation = 0.0

    opacity = rng.uniform(args.opacity_min, args.opacity_max)
    if opacity < 1.0:
        r, g, b, a = stamp.split()
        a = a.point(lambda v: int(v * opacity))
        stamp = Image.merge("RGBA", (r, g, b, a))
    return stamp, rotation, scale, opacity


def compose_scene(bg: Image.Image, chosen: list[dict], stamp_imgs: dict, rng: random.Random, args):
    """Paste stamps onto a copy of bg; return (scene RGBA, list of per-stamp GT dicts)."""
    scene = bg.copy()
    bg_w, bg_h = scene.size
    placed_boxes: list[list[int]] = []
    stamps_meta = []

    for rec in chosen:
        stamp, rotation, scale, opacity = transform_stamp(
            stamp_imgs[rec["stamp_id"]].copy(), bg_w, rng, args
        )
        sw, sh = stamp.size
        if sw >= bg_w or sh >= bg_h:
            continue
        alpha = np.array(stamp.split()[-1])

        # try several positions; accept the first with low overlap
        accepted = None
        for _ in range(12):
            ox = rng.randint(0, bg_w - sw)
            oy = rng.randint(0, bg_h - sh)
            box = tight_bbox(alpha, ox, oy)
            if box is None:
                break
            if all(iou(box, b) < 0.15 for b in placed_boxes):
                accepted = (ox, oy, box)
                break
        if accepted is None:
            continue

        ox, oy, box = accepted
        scene.alpha_composite(stamp, (ox, oy))
        placed_boxes.append(box)
        stamps_meta.append({
            "stamp_id": rec["stamp_id"],
            "date": rec["date"],
            "country": rec["country"],
            "direction": rec["direction"] or None,
            "bbox_xyxy": box,
            "position": [ox, oy],
            "size": [sw, sh],
            "rotation": round(rotation, 2),
            "scale": round(scale, 3),
            "opacity": round(opacity, 3),
        })

    return scene, stamps_meta


def tight_bbox(alpha: np.ndarray, ox: int, oy: int) -> list[int] | None:
    ys, xs = np.where(alpha > 10)
    if xs.size == 0:
        return None
    return [ox + int(xs.min()), oy + int(ys.min()), ox + int(xs.max()), oy + int(ys.max())]


def yolo_line(box: list[int], bg_w: int, bg_h: int) -> str:
    x1, y1, x2, y2 = box
    xc = (x1 + x2) / 2 / bg_w
    yc = (y1 + y2) / 2 / bg_h
    w = (x2 - x1) / bg_w
    h = (y2 - y1) / bg_h
    return f"{STAMP_CLASS} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(Path.home() / "Downloads" / "cleaned_stamps_and_bgs.zip"))
    ap.add_argument("--source-csv", default="data/rotation_testset/labels_source.csv")
    ap.add_argument("--out", default="data/synthetic_scenes")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--min-stamps", type=int, default=1)
    ap.add_argument("--max-stamps", type=int, default=4)
    ap.add_argument("--rotation", type=float, default=25.0)
    ap.add_argument("--rotate-prob", type=float, default=0.5,
                    help="probability a stamp is rotated; the rest are placed upright (0 deg)")
    ap.add_argument("--scale-min", type=float, default=0.18)
    ap.add_argument("--scale-max", type=float, default=0.32)
    ap.add_argument("--opacity-min", type=float, default=0.75)
    ap.add_argument("--opacity-max", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "yolo_detect").mkdir(parents=True, exist_ok=True)

    labels = load_labels(Path(args.source_csv))
    scenes_meta = []

    with zipfile.ZipFile(args.zip) as zf:
        backgrounds = list_backgrounds(zf)
        stamp_imgs = {r["stamp_id"]: open_rgba(zf, f"{STAMP_PREFIX}{r['stamp_id']}.png") for r in labels}

        for i in range(args.n):
            name = f"scene_{i:05d}"
            bg_name = rng.choice(backgrounds)
            bg = open_rgba(zf, bg_name)
            bg_w, bg_h = bg.size
            k = rng.randint(args.min_stamps, min(args.max_stamps, len(labels)))
            chosen = rng.sample(labels, k)

            scene, stamps_meta = compose_scene(bg, chosen, stamp_imgs, rng, args)
            if not stamps_meta:
                continue  # nothing placed (rare); skip empty scene

            scene.convert("RGB").save(out / "images" / f"{name}.jpg", quality=92)
            with open(out / "yolo_detect" / f"{name}.txt", "w") as f:
                f.write("\n".join(yolo_line(s["bbox_xyxy"], bg_w, bg_h) for s in stamps_meta) + "\n")

            scenes_meta.append({
                "image": f"{name}.jpg",
                "background": bg_name.replace(BG_PREFIX, ""),
                "width": bg_w,
                "height": bg_h,
                "stamps": stamps_meta,
            })

    with open(out / "metadata.json", "w") as f:
        json.dump(scenes_meta, f, indent=1, ensure_ascii=False)

    n_stamps = sum(len(s["stamps"]) for s in scenes_meta)
    print(f"built {len(scenes_meta)} scenes, {n_stamps} placed stamps")
    print(f"images  -> {out / 'images'}")
    print(f"yolo    -> {out / 'yolo_detect'}")
    print(f"metadata-> {out / 'metadata.json'}")


if __name__ == "__main__":
    main()
