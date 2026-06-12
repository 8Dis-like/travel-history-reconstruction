import cv2
import numpy as np
from pathlib import Path

def create_comparison_grid():
    raw_dir = Path("data/raw")
    enhanced_dir = Path("data/processed/enhanced")
    comp_dir = Path("data/processed/comparisons")
    comp_dir.mkdir(parents=True, exist_ok=True)
    
    enhanced_files = list(enhanced_dir.glob("enhanced_*.png"))
    
    if not enhanced_files:
        print("No enhanced images found. Please run test_pipeline.py first.")
        return

    print(f"Found {len(enhanced_files)} enhanced images. Generating side-by-side comparisons...")
    
    for enh_path in enhanced_files:
        raw_name = enh_path.name.replace("enhanced_", "")
        raw_path = raw_dir / raw_name
        
        if not raw_path.exists():
            continue
            
        # Read images
        raw_img = cv2.imread(str(raw_path))
        enh_img = cv2.imread(str(enh_path))
        
        # Resize to fixed height for side-by-side
        target_height = 800
        
        # Raw scaling
        raw_aspect = raw_img.shape[1] / raw_img.shape[0]
        raw_resized = cv2.resize(raw_img, (int(target_height * raw_aspect), target_height))
        
        # Enhanced scaling
        enh_aspect = enh_img.shape[1] / enh_img.shape[0]
        enh_resized = cv2.resize(enh_img, (int(target_height * enh_aspect), target_height))
        
        # Create text label areas
        raw_labeled = np.vstack([np.zeros((50, raw_resized.shape[1], 3), dtype=np.uint8), raw_resized])
        enh_labeled = np.vstack([np.zeros((50, enh_resized.shape[1], 3), dtype=np.uint8), enh_resized])
        
        cv2.putText(raw_labeled, "Original (Raw)", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(enh_labeled, "Enhanced (Auto-Orient + Deskew + CLAHE)", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Combine horizontally
        combined = np.hstack([raw_labeled, enh_labeled])
        
        # Save
        out_path = comp_dir / f"compare_{raw_name}"
        cv2.imwrite(str(out_path), combined)
        print(f"Saved {out_path.name}")

if __name__ == "__main__":
    create_comparison_grid()
