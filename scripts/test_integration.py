import sys
import os
from pathlib import Path
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.enhancer import ImageEnhancer
from src.detection.stamp_detector import StampDetector
from src.ocr.factory import create_extractor_from_config
from src.utils.rotation import rotate_image

def test_full_pipeline():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    images = list(raw_dir.glob("*.png")) + list(raw_dir.glob("*.jpg"))
    if not images:
        print("No raw images found!")
        return
        
    sample_image = str(images[0])
    print(f"Testing pipeline on: {sample_image}")
    
    # 1. Preprocessing
    print("\n--- 1. Preprocessing ---")
    enhancer = ImageEnhancer()
    img_bgr = cv2.imread(sample_image)
    enhanced_img, report = enhancer.process(img_bgr)
    print(f"Enhanced image shape: {report.final_shape}")
    
    # 2. Detection (Multi-Rotation)
    print("\n--- 2. Stamp Detection (Multi-Rotation) ---")
    detector = StampDetector(model_path="runs/best_stamp_model.pt")
    
    best_count = -1
    best_det = None
    
    for angle in [0, 90, 180, 270]:
        rot_img = rotate_image(img_bgr, angle)
        enhanced_rot, _ = enhancer.process(rot_img)
        detection_result = detector.detect(enhanced_rot, extract_crops=True)
        
        if detection_result.count > best_count:
            best_count = detection_result.count
            best_det = detection_result
        elif detection_result.count == best_count and best_count > 0:
            avg_conf_cur = sum(d.confidence for d in best_det.detections) / best_count
            avg_conf_new = sum(d.confidence for d in detection_result.detections) / best_count
            if avg_conf_new > avg_conf_cur:
                best_det = detection_result
                
    if best_det is None:
        best_det = detector.detect(enhanced_img, extract_crops=True)

    print(f"Found {best_det.count} stamps.")
    
    # 3. OCR Extraction
    print("\n--- 3. OCR Extraction (Claude) ---")
    extractor = create_extractor_from_config()
    for i, det in enumerate(best_det.detections):
        if det.crop is not None:
            extraction = extractor.extract(det.crop)
            print(f"Stamp {i+1}:")
            print(f"  Confidence: {det.confidence:.2f}")
            print(f"  Extracted Date: {extraction.date}")
            print(f"  Extracted Country: {extraction.country}")
            print(f"  Extracted Direction: {extraction.direction}")
            print(f"  Raw Text: {extraction.raw_text}")
            print(f"  OCR Confidence: {extraction.confidence}")
            
    print("\nIntegration test complete!")

if __name__ == "__main__":
    test_full_pipeline()
