import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import cv2
import numpy as np
from src.detection.stamp_detector import StampDetector
from src.preprocessing.enhancer import ImageEnhancer
from scripts.eval_end_to_end import unrotate_box, compute_iou

def main():
    root = Path("data/synthetic_scenes")
    metadata = json.load(open(root / "metadata.json"))
    
    enhancer = ImageEnhancer()
    detector = StampDetector("runs/best_stamp_model.pt")
    
    for idx, scene in enumerate(metadata):
        print(f"\n--- Scene {idx+1}: {scene['image']} ---")
        img_path = root / "images" / scene["image"]
        raw_img = cv2.imread(str(img_path))
        orig_h, orig_w = raw_img.shape[:2]
        print(f"Original shape: {orig_w}x{orig_h}")
        
        best_count = -1
        best_det = None
        best_angle = 0
        
        for angle in [0, 90, 180, 270]:
            h, w = raw_img.shape[:2]
            center = (w / 2, h / 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            cos = abs(matrix[0, 0])
            sin = abs(matrix[0, 1])
            new_w = int(h * sin + w * cos)
            new_h = int(h * cos + w * sin)
            matrix[0, 2] += (new_w - w) / 2
            matrix[1, 2] += (new_h - h) / 2
            rot_img = cv2.warpAffine(raw_img, matrix, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
            
            enhanced, report = enhancer.process(rot_img)
            det_result = detector.detect(enhanced, extract_crops=False)
            print(f"  Angle {angle}: {len(det_result.detections)} detections (Enhancer auto-orient: {report.rotation_applied_deg})")
            
            if len(det_result.detections) > best_count:
                best_count = len(det_result.detections)
                best_det = det_result
                best_angle = angle
                
        print(f"Chosen angle: {best_angle} with {best_count} detections")
        
        for i, det in enumerate(best_det.detections):
            bbox = unrotate_box(det.bbox_xyxy, best_angle, orig_w, orig_h)
            print(f"  Pred {i+1}: raw {det.bbox_xyxy} -> unrotated {bbox}")
            
        for i, gt in enumerate(scene["stamps"]):
            print(f"  GT {i+1}: {gt['bbox_xyxy']}")
            
            for j, det in enumerate(best_det.detections):
                pred_bbox = unrotate_box(det.bbox_xyxy, best_angle, orig_w, orig_h)
                iou = compute_iou(gt['bbox_xyxy'], pred_bbox)
                print(f"    IoU GT {i+1} vs Pred {j+1}: {iou:.3f}")

if __name__ == "__main__":
    main()
