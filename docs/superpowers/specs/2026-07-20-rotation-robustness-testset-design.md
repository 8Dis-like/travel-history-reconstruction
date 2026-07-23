# Rotation Robustness Test Set — Design

**Date:** 2026-07-20
**Status:** Approved (pending spec review)

## Goal

Build a reusable test set that measures how OCR extraction accuracy on passport
stamps degrades as the stamp image is rotated. The core idea: label a stamp
once (from a careful reading of the upright crop), then rotate the *same* image
to several angles and check whether each field still extracts correctly. This
isolates the rotation effect from every other variable.

This extends the existing one-off `scripts/test_rotation_robustness.py` (which
rotates 4 hand-labeled fixtures in memory) into a persisted, larger, reviewable
test set with its own labels.

## Fields (what the timeline needs)

The extractor (`src/ocr/base.py::ExtractionResult`) returns five fields. The
travel-history timeline needs three of them:

| Field | In timeline? | Notes |
|-------|--------------|-------|
| `date` | yes | ordering anchor |
| `country` | yes | where |
| `direction` (ENTRY/EXIT) | yes | needed to reconstruct in-country intervals |
| `raw_text` | no | auxiliary |
| `confidence` | no | metadata |

The extractor is designed to emit `null` for any unreadable field, so a stamp
that never printed a direction is still usable via `date` + `country`.

## Scope decisions

- **Base unit:** individual stamp crops (not composited scenes). Cleanest
  measure of pure OCR-vs-rotation; matches the existing fixtures approach.
- **Source pool:** `clean_stamps_cropped/` inside
  `~/Downloads/cleaned_stamps_and_bgs.zip` (~1500 stamps).
- **Size:** ~30 accepted "clean" stamps → ~210 test images.
- **Angles:** `[0, 20, 45, 75, 90, 180, 220]` (7 angles per stamp).
- **Labeling:** done by hand — Claude views each candidate crop and transcribes
  fields. Arabic/degraded stamps are handled conservatively (unsure → `null`).

## Labeling & scoring rules

Per-field labeling + per-field scoring:

- Each field is either a ground-truth value or `null` (stamp doesn't show it, or
  it is unreadable even at 0°).
- **Inclusion threshold:** a stamp is accepted only if `date` **and** `country`
  are readable. `direction` is labeled when present, otherwise `null`.
- **Scoring:** for each angle, report accuracy for `date`, `country`, and
  `direction` *separately*, each computed only over stamps whose ground truth
  for that field is non-null. Plus a combined "all non-null fields correct"
  metric per stamp/angle.
- `date` comparison is exact string match on ISO `YYYY-MM-DD`; `country` exact
  on ISO-3166 alpha-3; `direction` exact on `ENTRY`/`EXIT`.

## Honesty caveat

Labels are one careful read by a model (Claude), not human-verified absolute
truth. The label CSV keeps a `label_confidence` column and a `note` column for
spot-checking, and the user reviews the selected set before it is built (see
workflow step 3). Scripts and any README note this explicitly.

## Workflow & components

Labeling and evaluation are decoupled so the model can be swapped and the eval
re-run without re-labeling.

### 1. `scripts/sample_stamps.py`
- Randomly samples `K` candidate stamps (default 80, `--seed` for
  reproducibility) from the zip and extracts them to
  `data/rotation_testset/_candidates/`.
- Writes a template `data/rotation_testset/labels_source.csv` with one row per
  candidate: `stamp_id, source_file, date, country, direction,
  label_confidence, note` (label columns blank).
- Args: `--zip`, `--out`, `--k`, `--seed`.

### 2. Hand labeling (Claude)
- Claude views each candidate and fills `labels_source.csv`.
- Rows failing the inclusion threshold (no readable date+country) are deleted.
- Target: ~30 accepted rows.

### 3. Review gate (user confirmation) — REQUIRED
- Claude presents the ~30 selected stamps as a visual contact sheet
  (thumbnail + proposed label per stamp) for the user to confirm or correct.
- Build does not run until the user approves. The user may edit
  `labels_source.csv` directly.

### 4. `scripts/build_rotation_testset.py`
- Reads the approved `labels_source.csv`.
- For each accepted stamp, generates 7 rotated copies using the existing
  `rotate_image` helper (expand canvas, white fill, no cropping) into
  `data/rotation_testset/images/` named `<stamp_id>_rot<angle>.png`.
- Writes `data/rotation_testset/labels.csv` — one row per image:
  `image_path, stamp_id, source_file, angle, gt_date, gt_country,
  gt_direction, label_confidence`.
- Args: `--source-csv`, `--candidates-dir`, `--out`, `--angles`.

### 5. `scripts/eval_rotation_testset.py`
- Reads `labels.csv`, runs `create_extractor_from_config().extract()` on each
  image, compares per-field, prints a per-angle summary
  (date / country / direction / combined accuracy) and per-image detail.
- Re-runnable against any configured model. Read-only w.r.t. the test set.

## Storage / git

- `.gitignore`: `data/rotation_testset/images/` and
  `data/rotation_testset/_candidates/` (large binaries).
- Commit: `labels_source.csv` and `labels.csv` — small, text, the actual label
  asset. Anyone can re-extract candidates by seed and rebuild images.

## Reused code

- `rotate_image` from `scripts/test_rotation_robustness.py` (extract into a
  shared helper so both scripts use one implementation).
- `create_extractor_from_config` from `src/ocr/factory.py`.

## Out of scope

- Composited-scene test set (background + stamp).
- Detection/localization metrics.
- Timeline reconstruction (module is still a stub).
- CV deskew / auto-rotation correction (repo deliberately dropped this).
