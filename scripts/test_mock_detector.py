"""
Quick test of the MockStampDetector on enhanced images.

This script demonstrates how to use the mock detector as a drop-in
replacement for StampDetector while we wait for fine-tuned weights.

Usage:
    python scripts/test_mock_detector.py
    python scripts/test_mock_detector.py --images enhanced_page_001.png enhanced_page_022.png
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
from src.detection.mock_detector import MockStampDetector


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test mock stamp detector")
    parser.add_argument("--images", nargs="*", default=None,
                        help="Specific filenames in data/processed/enhanced/")
    parser.add_argument("--max-images", type=int, default=3)
    args = parser.parse_args()

    enhanced_dir = PROJECT_ROOT / "data" / "processed" / "enhanced"
    crops_dir = PROJECT_ROOT / "data" / "processed" / "mock_crops"
    annotated_dir = PROJECT_ROOT / "data" / "processed" / "mock_annotated"
    crops_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    if args.images:
        image_files = [enhanced_dir / f for f in args.images]
    else:
        image_files = sorted(enhanced_dir.glob("*.png"))

    if args.max_images > 0:
        image_files = image_files[:args.max_images]

    if not image_files:
        print("No enhanced images found. Run test_pipeline.py first.")
        return

    print(f"\n{'='*70}")
    print(f"  MOCK STAMP DETECTOR TEST")
    print(f"  Images: {len(image_files)}")
    print(f"  NOTE: Uses contour-based detection — NOT the fine-tuned YOLO model")
    print(f"{'='*70}\n")

    detector = MockStampDetector()

    total_stamps = 0
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] {img_path.name}")

        result = detector.detect(str(img_path))
        print(f"  Stamps found: {result.count}")
        print(f"  Time: {result.inference_time_ms:.0f}ms")

        # Save crops
        saved = detector.save_crops(result, crops_dir)
        for p in saved:
            print(f"    → Crop saved: {p.name}")

        # Save annotated image
        img = cv2.imread(str(img_path))
        if img is not None and result.count > 0:
            annotated = detector.visualize(img, result)
            ann_path = annotated_dir / f"mock_{img_path.stem}.jpg"
            cv2.imwrite(str(ann_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            print(f"    → Annotated: {ann_path.name}")

        total_stamps += result.count
        print()

    print(f"{'='*70}")
    print(f"  Total stamps extracted: {total_stamps}")
    print(f"  Crops directory: {crops_dir}")
    print(f"  Annotated directory: {annotated_dir}")
    print(f"{'='*70}\n")

    # Show how Zuyan would consume these crops
    print("=" * 70)
    print("  HOW TO USE THESE CROPS FOR OCR DEVELOPMENT")
    print("=" * 70)
    print("""
  Zuyan — here's how to plug into this:

  Option A: Use crops directly (simplest)
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    result = ocr.ocr('data/processed/mock_crops/enhanced_page_001_MOCK_001.jpg')

  Option B: Use the detector in your pipeline code
    from src.detection.mock_detector import MockStampDetector
    detector = MockStampDetector()
    result = detector.detect('data/processed/enhanced/enhanced_page_001.png')
    for det in result.detections:
        # det.crop is a numpy array — feed directly to PaddleOCR
        ocr_result = ocr.ocr(det.crop)

  When best.pt is ready, swap ONE line:
    from src.detection.stamp_detector import StampDetector
    detector = StampDetector('models/finetuned/best.pt')
    # Everything else stays identical!
""")


if __name__ == "__main__":
    main()
