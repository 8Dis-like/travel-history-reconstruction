"""
Pipeline Smoke Test — Preprocessing + Detection on Sample Data.

Runs the full preprocessing and detection pipeline on sample passport
page images in data/raw/, saves results to data/processed/, and
generates a text report summarizing findings.

Usage:
    python scripts/test_pipeline.py
    python scripts/test_pipeline.py --images page_001.png page_003.png
    python scripts/test_pipeline.py --skip-denoise    # faster, skip slow denoising
"""

import sys
import time
import json
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from src.preprocessing.enhancer import ImageEnhancer


def parse_args():
    parser = argparse.ArgumentParser(description="Test preprocessing + detection pipeline")
    parser.add_argument(
        "--images", nargs="*", default=None,
        help="Specific image filenames to test (default: all PNGs in data/raw/)"
    )
    parser.add_argument(
        "--max-images", type=int, default=5,
        help="Max images to process (default: 5, use -1 for all)"
    )
    parser.add_argument(
        "--skip-denoise", action="store_true",
        help="Skip denoising step (much faster, useful for quick tests)"
    )
    parser.add_argument(
        "--no-orient", action="store_true",
        help="Skip auto-orientation correction"
    )
    return parser.parse_args()


def test_preprocessing(args):
    """Test the preprocessing pipeline on sample images."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    out_dir = PROJECT_ROOT / "data" / "processed" / "enhanced"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect images
    if args.images:
        image_files = [raw_dir / f for f in args.images]
    else:
        image_files = sorted(raw_dir.glob("*.png"))

    if args.max_images > 0:
        image_files = image_files[:args.max_images]

    if not image_files:
        print("ERROR: No images found in data/raw/")
        return []

    print(f"\n{'='*70}")
    print(f"  PREPROCESSING PIPELINE TEST")
    print(f"  Images: {len(image_files)} | Denoise: {not args.skip_denoise} | Auto-orient: {not args.no_orient}")
    print(f"{'='*70}\n")

    enhancer = ImageEnhancer(
        denoise=not args.skip_denoise,
        auto_orient=not args.no_orient,
    )

    results = []
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing: {img_path.name}")
        print(f"  File size: {img_path.stat().st_size / 1024 / 1024:.1f} MB")

        t0 = time.time()
        try:
            out_path = out_dir / f"enhanced_{img_path.name}"
            enhanced, report = enhancer.process_file(str(img_path), str(out_path))
            elapsed = time.time() - t0

            print(f"  {report}")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Saved: {out_path.name}")
            print()

            results.append({
                "filename": img_path.name,
                "original_shape": list(report.original_shape),
                "final_shape": list(report.final_shape),
                "was_resized": report.was_resized,
                "rotation_deg": report.rotation_applied_deg,
                "deskew_deg": report.deskew_angle_deg,
                "processing_time_s": round(elapsed, 2),
                "output_file": out_path.name,
                "status": "OK",
            })
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ERROR: {e}")
            print()
            results.append({
                "filename": img_path.name,
                "status": "ERROR",
                "error": str(e),
                "processing_time_s": round(elapsed, 2),
            })

    return results


def test_detection_pretrained(args):
    """Test detection with pretrained COCO model (baseline sanity check).

    NOTE: The pretrained COCO model does NOT have a 'stamp' class.
    This test validates that:
    1. The YOLO wrapper loads and runs without errors
    2. The inference pipeline works end-to-end on our images
    3. We can measure inference time on our image sizes

    After fine-tuning on stamp data, re-run with the custom weights.
    """
    try:
        from src.detection.stamp_detector import StampDetector
    except ImportError as e:
        print(f"\n[DETECTION] Skipped — ultralytics not installed: {e}")
        return []

    raw_dir = PROJECT_ROOT / "data" / "raw"
    enhanced_dir = PROJECT_ROOT / "data" / "processed" / "enhanced"
    annotated_dir = PROJECT_ROOT / "data" / "processed" / "annotated"
    annotated_dir.mkdir(parents=True, exist_ok=True)

    # Use enhanced images if available, otherwise raw
    source_dir = enhanced_dir if enhanced_dir.exists() and any(enhanced_dir.glob("*.png")) else raw_dir

    if args.images:
        if source_dir == enhanced_dir:
            image_files = [source_dir / f"enhanced_{f}" for f in args.images]
            image_files = [f for f in image_files if f.exists()]
        if not image_files:
            image_files = [raw_dir / f for f in args.images]
    else:
        image_files = sorted(source_dir.glob("*.png"))

    if args.max_images > 0:
        image_files = image_files[:args.max_images]

    if not image_files:
        print("[DETECTION] No images to process")
        return []

    print(f"\n{'='*70}")
    print(f"  DETECTION PIPELINE TEST (pretrained COCO — baseline)")
    print(f"  Source: {source_dir.name}/ | Images: {len(image_files)}")
    print(f"  NOTE: COCO model has no 'stamp' class — this is a smoke test")
    print(f"{'='*70}\n")

    detector = StampDetector(
        model_path="yolov8s.pt",
        confidence_threshold=0.25,  # Low threshold for baseline
    )

    results = []
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Detecting: {img_path.name}")

        try:
            result = detector.detect(str(img_path))
            print(f"  Objects found: {result.count}")
            print(f"  Inference: {result.inference_time_ms:.0f}ms")

            # Show what COCO classes were detected (just for info)
            class_counts = {}
            for det in result.detections:
                class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
            if class_counts:
                print(f"  Classes: {class_counts}")

            # Save annotated image
            img = cv2.imread(str(img_path))
            if img is not None and result.count > 0:
                annotated = detector.visualize(img, result)
                ann_path = annotated_dir / f"annotated_{img_path.stem}.jpg"
                cv2.imwrite(str(ann_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
                print(f"  Saved: {ann_path.name}")

            print()
            results.append({
                "filename": img_path.name,
                "objects_detected": result.count,
                "classes": class_counts,
                "inference_time_ms": round(result.inference_time_ms, 1),
                "status": "OK",
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            print()
            results.append({
                "filename": img_path.name,
                "status": "ERROR",
                "error": str(e),
            })

    return results


def main():
    args = parse_args()

    # Test 1: Preprocessing
    preprocess_results = test_preprocessing(args)

    # Test 2: Detection (pretrained baseline)
    detection_results = test_detection_pretrained(args)

    # Save combined report
    report = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "preprocessing": preprocess_results,
        "detection_baseline": detection_results,
    }

    report_path = PROJECT_ROOT / "data" / "processed" / "test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    ok_preprocess = sum(1 for r in preprocess_results if r.get("status") == "OK")
    ok_detect = sum(1 for r in detection_results if r.get("status") == "OK")
    print(f"  Preprocessing: {ok_preprocess}/{len(preprocess_results)} succeeded")
    if preprocess_results:
        avg_time = np.mean([r["processing_time_s"] for r in preprocess_results if r.get("status") == "OK"])
        print(f"  Avg preprocessing time: {avg_time:.1f}s")
        rotated = sum(1 for r in preprocess_results if r.get("rotation_deg", 0) != 0)
        print(f"  Auto-rotated: {rotated}/{len(preprocess_results)} images")
    print(f"  Detection (COCO): {ok_detect}/{len(detection_results)} succeeded")
    if detection_results:
        avg_inf = np.mean([r["inference_time_ms"] for r in detection_results if r.get("status") == "OK"])
        print(f"  Avg inference time: {avg_inf:.0f}ms")
    print(f"\n  Full report: {report_path}")
    print()


if __name__ == "__main__":
    main()
