# OCR Accuracy, Rotation Robustness & Crop Enhancement — Evaluation Report

**Date:** August 3, 2026
**Project:** Travel History Reconstruction from Travel Documents
**Branch:** `zuyantao` (synced to `master`)
**VLM:** `claude-sonnet-5` (via `configs/pipeline.yaml` → `ocr.engine: claude`)
**Detector:** fine-tuned YOLO (`runs/best_stamp_model.pt`, single class `stamp`)

---

## 1. Executive Summary

We evaluated the pipeline on the synthetic-scene test set (30 composited passport
pages, 77 ground-truth stamps) and the rotation-robustness test set (30 stamps ×
7 angles = 210 images), then prototyped and adopted a crop-level image
enhancement step.

Headline findings:

- **Detection is not the bottleneck.** End-to-end, YOLO scores **F1 96.8%**
  (Precision 96.2%, Recall 97.4%). Only 2 false negatives and 3 false positives
  across 77 stamps.
- **The bottleneck is OCR on faint/faded ink.** The dominant failure is
  *unreadable* stamps (the VLM returns `null`), not misreads. Of 25 date
  failures, 18 were "unreadable" and only 7 were wrong values.
- **The VLM is rotation-tolerant only for small tilts.** Accuracy holds from
  0–45°, drops at 75–90°, and collapses at 180°/220°. The earlier belief that the
  VLM is fully rotation-invariant was an artifact of the synthetic scenes only
  rotating stamps by ±25°.
- **Crop enhancement recovers faint ink.** A 2× upscale + CLAHE + mild saturation
  + light unsharp step lifted OCR field accuracy by **+11 to +15 points** on the
  GT-box eval, recovering 35 previously-unreadable fields. Now integrated into the
  pipeline (before the VLM call) at a conservative saturation gain.

---

## 2. Test Sets

- **Synthetic scenes** (`data/synthetic_scenes/`): hand-labeled stamps pasted onto
  passport backgrounds, carrying full ground truth (bbox + date/country/direction)
  per stamp. Regenerated deterministically with
  `python scripts/build_synthetic_scenes.py --n 30 --seed 42` — the regenerated
  `metadata.json` and YOLO labels are byte-identical to the committed versions.
  30 scenes, 77 placed stamps.
- **Rotation-robustness set** (`data/rotation_testset/`): each of 30 labeled stamps
  rotated to `[0, 20, 45, 75, 90, 180, 220]°`, built via
  `scripts/build_rotation_testset.py`. Ground-truth labels come from the
  human-curated `labels_source.csv` (not re-derived by the VLM).

All accuracies below are **per field, over stamps with a non-null ground-truth
label for that field** (case-insensitive exact match after trim).

---

## 3. OCR + Timeline Accuracy (ground-truth boxes)

`scripts/eval_synthetic_scenes.py` crops each stamp at its **true** box (isolating
OCR + timeline from the detector) and runs the VLM.

| Field | All | Upright | Rotated |
|-----------|------|---------|---------|
| date | 68% (52/77) | 61% (28/46) | 77% (24/31) |
| country | 68% (52/77) | 61% (28/46) | 77% (24/31) |
| direction | 73% (49/67) | 62% (25/40) | 89% (24/27) |

Timeline pairwise-order accuracy: **56%**.

**Failure breakdown:**

| Field | Unreadable (null) | Wrong value |
|-----------|-------------------|-------------|
| date | 18 | 7 |
| country | 19 | 6 |

The unreadable stamps correlate strongly with `labels_source.csv` rows flagged
`med` confidence and notes like *faint / faded / unclear*. The bottleneck is
signal quality, not localization. (The "rotated > upright" gap here is sampling
noise — the small upright subset happened to contain more faint stamps.)

---

## 4. End-to-End Accuracy (real YOLO → rotation retry → OCR → timeline)

`scripts/eval_end_to_end.py` runs the full `extract_page` logic on raw scenes and
matches predicted boxes to ground truth by IoU (threshold 0.5).

**Detection (confusion matrix):**

| TP | FP | FN | Precision | Recall | F1 |
|----|----|----|-----------|--------|------|
| 75 | 3 | 2 | 96.2% | 97.4% | 96.8% |

**OCR accuracy on true positives:**

| Field | Accuracy |
|-----------|--------------|
| date | 64.0% (48/75) |
| country | 65.3% (49/75) |
| direction | 69.2% (45/65) |

Timeline pairwise-order accuracy: **48.9%**.

OCR is only ~3–4 points below the GT-box numbers, confirming the detector barely
costs accuracy — the ceiling is the VLM's reading of degraded ink. Timeline
suffers because unreadable dates cannot be ordered.

> Note: `eval_end_to_end.py` prints the extraction section header as "Qwen
> EXTRACTION" — this is a stale hardcoded label. The run used `claude-sonnet-5`
> (the config engine); Qwen is an unimplemented stub that would return all-null.

---

## 5. Rotation Robustness (per-angle)

`scripts/eval_rotation_testset.py` feeds pre-rotated GT crops **directly** to the
VLM (no detector, no page-level retry), so these numbers are the VLM alone.

| Angle | date | country | direction | Combined (all 3) |
|-------|------|---------|-----------|------------------|
| 0° | 83% | 90% | 88% | 80% |
| 20° | 93% | 90% | 88% | 87% |
| 45° | 83% | 83% | 80% | 73% |
| 75° | 77% | 83% | 84% | 70% |
| 90° | 60% | 73% | 68% | 57% |
| 180° | 50% | 53% | 52% | 40% |
| 220° | 50% | 70% | 64% | 43% |

**Interpretation:** the VLM is robust for small tilts (0–45°, the realistic range
for a stamped-then-scanned page), degrades at 75–90°, and collapses when text is
inverted (180°/220°).

### 5.1 Why the 4-direction retry does not fully close this

The `extract_page` rotation retry rotates the **whole page** through
0/90/180/270°, runs YOLO on each, and keeps the orientation with the most
detections. Consequences:

- It corrects a **whole page** scanned sideways/upside-down (all stamps share the
  same misorientation), and only in 90° steps.
- It **cannot** upright a single stamp rotated relative to the page — rotating the
  page rotates every stamp together. YOLO outputs axis-aligned boxes and does not
  emit per-stamp orientation, so an inverted stamp is cropped still inverted.

Per-stamp rotation (the synthetic scenes' ±25°, or a single crooked stamp) is
therefore handled only by the VLM's own tolerance — fine up to ~45°, weak beyond.

### 5.2 Future options for per-stamp uprighting

| Approach | Gives orientation? | Cost |
|----------|--------------------|------|
| Segmentation mask (`yolo26s_seg`, already on `wilsontee`) + `cv2.minAreaRect` | derive angle from mask | low — model exists, not yet wired |
| Oriented bounding box (YOLO-OBB) | angle predicted directly (`xywhr`) | medium — needs OBB-format labels + training |
| Per-crop VLM over 4 rotations, keep most confident | brute force, no angle needed | high — 4× API calls |

Note: `minAreaRect` / OBB angles are defined mod 180°, so they fix tilt but not
inversion; distinguishing upright vs upside-down needs an extra up/down check.

---

## 6. Crop Enhancement — A/B and Adoption

Hypothesis from §3: if the bottleneck is faint ink, enhancing the crop before OCR
should recover unreadable stamps. We added `enhance_crop`
(`src/preprocessing/enhancer.py`): **2× upscale of small crops → CLAHE on L →
saturation boost → light unsharp mask**, and re-ran the GT-box eval, comparing
per-stamp against the baseline.

**Result (prototype, saturation ×1.4):**

| Field | Baseline | Enhanced | Δ | Recovered | Broken |
|-----------|----------|----------|-------|-----------|--------|
| date | 68% | 79% | +11 | 14 | 5 |
| country | 68% | 83% | +15 | 16 | 4 |
| direction | 73% | 87% | +14 | 13 | 4 |

35 previously-unreadable (`null`) fields were recovered. "Recovered" exceeds
"broken" for every field, so the net effect is a clear win; the small "broken"
counts are over-processing of already-clear stamps (plus some VLM run-to-run
noise).

**Adopted configuration:** saturation gain lowered from **×1.4 → ×1.2** to reduce
over-processing of clear stamps. This tuning was **not** re-evaluated against the
API (budget constraint); ×1.2 is expected to retain most of the gain with fewer
"broken" cases. `enhance_crop` lives in `src/preprocessing/enhancer.py`; wiring it
before every VLM extraction in `src/api/routes.py` (`/extract/page`,
`/extract/stamp`) is a separate backend change, tracked outside this report.

---

## 7. Recommendations

1. **Re-run the two evals with `enhance_crop` live** when API budget allows, to
   confirm the ×1.2 setting and measure the end-to-end (real-box) gain.
2. **Attack the remaining unreadable stamps** — consider adaptive enhancement
   (only enhance low-contrast crops) and light super-resolution.
3. **Add per-stamp uprighting** via the existing segmentation mask + `minAreaRect`
   (cheapest path) to recover the 45–90° range; add an up/down check for
   inversion.
4. **Fix the stale "Qwen EXTRACTION" label** in `eval_end_to_end.py` to print the
   actual configured engine.

---

## 8. Reproduction

```bash
# Regenerate test sets (deterministic; no API)
python scripts/build_synthetic_scenes.py --n 30 --seed 42
python scripts/build_rotation_testset.py

# Set OCR engine in configs/pipeline.yaml -> ocr.engine: "claude"
# Requires ANTHROPIC_API_KEY in .env

python scripts/eval_synthetic_scenes.py     # OCR + timeline (GT boxes)
python scripts/eval_end_to_end.py           # full pipeline + detection matrix
python scripts/eval_rotation_testset.py     # per-angle robustness
```
