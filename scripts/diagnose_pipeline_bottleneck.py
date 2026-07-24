import sys
import os
import argparse
import time
from pathlib import Path
import cv2
import pandas as pd
from typing import Dict, Any, List

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.enhancer import ImageEnhancer
from src.detection.stamp_detector import StampDetector
from src.ocr.factory import create_extractor_from_config
from src.utils.rotation import rotate_image

def generate_markdown_report(results, report_path):
    md = ["# Pipeline Bottleneck Diagnostic Report\n"]
    for res in results:
        md.append(f"## Image: {res['image_name']}\n")
        md.append(f"- **Mode A Detections:** {res['mode_a']['detections_count']}")
        md.append(f"- **Mode B Detections:** {res['mode_b']['detections_count']} (Best Angle: {res['mode_b'].get('best_angle', 'N/A')})\n")
        
        md.append("### Mode A Crops & Extractions")
        if res['mode_a']['crops']:
            md.append("| Crop | OCR Result |")
            md.append("|---|---|")
            for crop in res['mode_a']['crops']:
                md.append(f"| ![]({crop['path']}) | Date: {crop['date']}<br>Country: {crop['country']}<br>Direction: {crop['direction']} |")
        else:
            md.append("No stamps detected in Mode A.")
        md.append("\n")
            
        md.append("### Mode B Crops & Extractions")
        if res['mode_b']['crops']:
            md.append("| Crop | OCR Result |")
            md.append("|---|---|")
            for crop in res['mode_b']['crops']:
                md.append(f"| ![]({crop['path']}) | Date: {crop['date']}<br>Country: {crop['country']}<br>Direction: {crop['direction']} |")
        else:
            md.append("No stamps detected in Mode B.")
        md.append("\n---\n")

    with open(report_path, "w") as f:
        f.write("\n".join(md))
    print(f"Visual Markdown report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Diagnose Pipeline Bottleneck (Mode A vs Mode B)")
    parser.add_argument("--image", type=str, help="Single image path to test")
    parser.add_argument("--testset", action="store_true", help="Run on data/pipeline_testset/images")
    args = parser.parse_args()

    out_dir = PROJECT_ROOT / "data" / "processed" / "diagnostic_crops"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = PROJECT_ROOT / "data" / "processed" / "diagnostic_report.md"

    # Initialize components
    print("Initializing pipeline components...")
    enhancer = ImageEnhancer()
    detector = StampDetector(model_path="runs/best_stamp_model.pt")
    extractor = create_extractor_from_config()

    images_to_process = []
    if args.image:
        images_to_process.append(Path(args.image))
    elif args.testset:
        testset_dir = PROJECT_ROOT / "data" / "pipeline_testset" / "images"
        images_to_process = list(testset_dir.glob("*.png")) + list(testset_dir.glob("*.jpg"))
    else:
        raw_dir = PROJECT_ROOT / "data" / "raw"
        images_to_process = list(raw_dir.glob("*.png")) + list(raw_dir.glob("*.jpg"))
        # Limit to first 2 images by default to save time/API costs if no args given
        images_to_process = images_to_process[:2]

    if not images_to_process:
        print("No images found to process!")
        return

    results = []

    for img_path in images_to_process:
        print(f"\nProcessing {img_path.name}...")
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            print(f"Failed to read {img_path}")
            continue

        res = {
            "image_name": img_path.name,
            "mode_a": {"detections_count": 0, "crops": []},
            "mode_b": {"detections_count": 0, "crops": [], "best_angle": None}
        }

        # --- MODE A: Current Pipeline ---
        print("  Running Mode A (Current)...")
        enh_a, _ = enhancer.process(img_bgr)
        det_a = detector.detect(enh_a, extract_crops=True)
        res["mode_a"]["detections_count"] = det_a.count
        print(f"    Mode A found {det_a.count} stamps.")
        
        for i, det in enumerate(det_a.detections):
            if det.crop is not None:
                crop_path = out_dir / f"mode_a_{img_path.stem}_{i}.jpg"
                cv2.imwrite(str(crop_path), det.crop)
                ext = extractor.extract(det.crop)
                res["mode_a"]["crops"].append({
                    "path": str(crop_path.absolute()).replace("\\", "/"),
                    "date": ext.date,
                    "country": ext.country,
                    "direction": ext.direction
                })

        # --- MODE B: Multi-Rotation Strategy ---
        print("  Running Mode B (Multi-Rotation)...")
        best_angle = 0
        best_count = -1
        best_det = None
        best_enh = None
        
        for angle in [0, 90, 180, 270]:
            rot_img = rotate_image(img_bgr, angle)
            enh_b, _ = enhancer.process(rot_img)
            det_b = detector.detect(enh_b, extract_crops=True)
            # Pick the angle that yields the highest number of detections, break ties with confidence
            if det_b.count > best_count:
                best_count = det_b.count
                best_angle = angle
                best_det = det_b
                best_enh = enh_b
            elif det_b.count == best_count and det_b.count > 0:
                # tie-breaker: avg confidence
                avg_conf_cur = sum(d.confidence for d in best_det.detections) / best_det.count
                avg_conf_new = sum(d.confidence for d in det_b.detections) / det_b.count
                if avg_conf_new > avg_conf_cur:
                    best_angle = angle
                    best_det = det_b
                    best_enh = enh_b

        res["mode_b"]["best_angle"] = best_angle
        if best_det is not None:
            res["mode_b"]["detections_count"] = best_det.count
            print(f"    Mode B selected angle {best_angle} with {best_det.count} stamps.")
            for i, det in enumerate(best_det.detections):
                if det.crop is not None:
                    crop_path = out_dir / f"mode_b_{img_path.stem}_{best_angle}deg_{i}.jpg"
                    cv2.imwrite(str(crop_path), det.crop)
                    ext = extractor.extract(det.crop)
                    res["mode_b"]["crops"].append({
                        "path": str(crop_path.absolute()).replace("\\", "/"),
                        "date": ext.date,
                        "country": ext.country,
                        "direction": ext.direction
                    })

        results.append(res)
    
    generate_markdown_report(results, report_path)
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()
