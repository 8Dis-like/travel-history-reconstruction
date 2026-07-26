from __future__ import annotations

"""End-to-end pipeline evaluation on the synthetic-scene test set.

This script runs the full extract_page logic (Detection -> Rotation -> OCR -> Timeline)
on raw uncropped synthetic scenes. It uses Intersection over Union (IoU) to match
predicted bounding boxes to ground-truth bounding boxes to compute a Detection
Confusion Matrix (TP, FP, FN).

For True Positives, it evaluates OCR extraction accuracy and pairwise timeline accuracy.

Run:
  python scripts/eval_end_to_end.py
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.detection.stamp_detector import StampDetector
from src.ocr.factory import create_extractor_from_config
from src.preprocessing.enhancer import ImageEnhancer
from src.utils.rotation import rotate_image
from src.reconstruction.timeline import TimelineEvent, build_timeline
from src.reconstruction.scene_eval import pairwise_order_accuracy

def compute_iou(box1: list[float], box2: list[float]) -> float:
    """Computes Intersection over Union (IoU) for two bounding boxes [x1, y1, x2, y2]."""
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    if box1_area + box2_area - intersection_area == 0:
        return 0.0
    return intersection_area / float(box1_area + box2_area - intersection_area)

def unrotate_box(box: list[float], angle: int, orig_w: int, orig_h: int) -> list[float]:
    x1, y1, x2, y2 = box
    if angle == 0:
        return [x1, y1, x2, y2]
    elif angle == 90:
        return [y1, orig_h - x2, y2, orig_h - x1]
    elif angle == 180:
        return [orig_w - x2, orig_h - y2, orig_w - x1, orig_h - y1]
    elif angle == 270:
        return [orig_w - y2, x1, orig_w - y1, x2]
    return box

def _norm(v: str | None) -> str | None:
    return (v or "").strip().upper() or None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/synthetic_scenes")
    ap.add_argument("--limit", type=int, default=0, help="evaluate only first N scenes")
    ap.add_argument("--iou-threshold", type=float, default=0.5, help="IoU threshold for a TP match")
    args = ap.parse_args()

    root = Path(args.root)
    metadata_path = root / "metadata.json"
    if not metadata_path.exists():
        print(f"Error: {metadata_path} not found.")
        sys.exit(1)

    metadata = json.load(open(metadata_path))
    if args.limit:
        metadata = metadata[:args.limit]

    enhancer = ImageEnhancer()
    detector = StampDetector("runs/best_stamp_model.pt")
    extractor = create_extractor_from_config()

    tp_count = 0
    fp_count = 0
    fn_count = 0

    ocr_eval = {
        "date": {"correct": 0, "total": 0},
        "country": {"correct": 0, "total": 0},
        "direction": {"correct": 0, "total": 0},
    }

    all_pairs = []

    print(f"Evaluating {len(metadata)} scenes...\n")

    for idx, scene in enumerate(metadata):
        img_path = root / "images" / scene["image"]
        raw_img = cv2.imread(str(img_path))
        if raw_img is None:
            print(f"  skip (missing image): {scene['image']}")
            continue

        gt_stamps = scene["stamps"]
        
        # --- 1. Run Pipeline (Detection + OCR) ---
        best_count = -1
        best_det = None
        best_angle = 0
        
        # Multi-rotation detection strategy
        for angle in [0, 90, 180, 270]:
            rot_img = rotate_image(raw_img, angle)
            enhanced, _ = enhancer.process(rot_img)
            det_result = detector.detect(enhanced, extract_crops=True, source_name=scene["image"])
            
            if len(det_result.detections) > best_count:
                best_count = len(det_result.detections)
                best_det = det_result
                best_angle = angle

        # Fallback
        if best_det is None:
            enhanced, _ = enhancer.process(raw_img)
            best_det = detector.detect(enhanced, extract_crops=True, source_name=scene["image"])
            best_angle = 0

        orig_h, orig_w = raw_img.shape[:2]
        predictions = []
        for det in best_det.detections:
            if det.crop is None:
                continue
                
            orig_bbox = unrotate_box(det.bbox_xyxy, best_angle, orig_w, orig_h)
            
            # OCR Extraction
            extraction = extractor.extract(det.crop)
            predictions.append({
                "bbox": orig_bbox,
                "date": extraction.date,
                "country": extraction.country,
                "direction": extraction.direction,
                "matched": False
            })

        # --- 2. Bounding Box Matching (IoU) ---
        scene_tp = 0
        scene_fn = 0
        
        for gt in gt_stamps:
            gt_bbox = gt["bbox_xyxy"]
            best_iou = 0.0
            best_pred_idx = -1
            
            for i, pred in enumerate(predictions):
                if pred["matched"]:
                    continue
                iou = compute_iou(gt_bbox, pred["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_pred_idx = i
            
            if best_iou >= args.iou_threshold:
                # True Positive
                scene_tp += 1
                tp_count += 1
                pred = predictions[best_pred_idx]
                pred["matched"] = True
                
                # Evaluate OCR for this match
                gt_date = _norm(gt.get("date"))
                pred_date = _norm(pred["date"])
                if gt_date:
                    ocr_eval["date"]["total"] += 1
                    if gt_date == pred_date:
                        ocr_eval["date"]["correct"] += 1
                        
                gt_country = _norm(gt.get("country"))
                pred_country = _norm(pred["country"])
                if gt_country:
                    ocr_eval["country"]["total"] += 1
                    if gt_country == pred_country:
                        ocr_eval["country"]["correct"] += 1
                        
                gt_direction = _norm(gt.get("direction"))
                pred_direction = _norm(pred["direction"])
                if gt_direction:
                    ocr_eval["direction"]["total"] += 1
                    if gt_direction == pred_direction:
                        ocr_eval["direction"]["correct"] += 1
                
                # Collect for timeline eval
                all_pairs.append((gt.get("date"), pred["date"]))
            else:
                # False Negative (GT missed)
                scene_fn += 1
                fn_count += 1
                all_pairs.append((gt.get("date"), None)) # missed detection

        # False Positives are predictions that never matched a GT
        scene_fp = sum(1 for p in predictions if not p["matched"])
        fp_count += scene_fp
        
        print(f"Scene {idx+1}: {scene['image']} -> TP: {scene_tp}, FP: {scene_fp}, FN: {scene_fn}")

    # --- 3. Final Evaluation Metrics ---
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\n==============================================")
    print("   END-TO-END PIPELINE EVALUATION REPORT")
    print("==============================================\n")
    
    print("1. DETECTION PERFORMANCE (Confusion Matrix)")
    print(f"   True Positives (TP)  : {tp_count}")
    print(f"   False Positives (FP) : {fp_count}")
    print(f"   False Negatives (FN) : {fn_count}")
    print(f"   ----------------------------------")
    print(f"   Precision : {precision:.1%}")
    print(f"   Recall    : {recall:.1%}")
    print(f"   F1-Score  : {f1:.1%}\n")

    print("2. OCR EXTRACTION ACCURACY (On True Positives)")
    for field, metrics in ocr_eval.items():
        correct = metrics["correct"]
        tot = metrics["total"]
        pct = correct / tot if tot > 0 else 0.0
        print(f"   {field.capitalize():<10}: {pct:>6.1%} ({correct}/{tot})")
    print()

    print("3. TIMELINE RECONSTRUCTION")
    timeline_acc = pairwise_order_accuracy(all_pairs)
    print(f"   Pairwise Order Accuracy: {timeline_acc:.1%}")
    print("==============================================\n")

if __name__ == "__main__":
    main()
