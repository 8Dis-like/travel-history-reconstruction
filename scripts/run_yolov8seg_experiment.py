"""
Convert mask PNGs to YOLO segmentation polygon labels, then fine-tune
YOLOv8s-seg and validate to get mask metrics for Table 4.2.
"""
import cv2
import numpy as np
import os
import glob
from pathlib import Path

def mask_to_yolo_polygons(mask_path, img_w, img_h):
    """Convert a binary mask PNG to YOLO polygon format."""
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return []
    
    # Resize mask to image dimensions if needed
    if mask.shape[0] != img_h or mask.shape[1] != img_w:
        mask = cv2.resize(mask, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
    
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    polygons = []
    for contour in contours:
        if len(contour) < 3:
            continue
        # Simplify contour
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 3:
            continue
        # Normalize coordinates
        points = approx.reshape(-1, 2).astype(float)
        points[:, 0] /= img_w
        points[:, 1] /= img_h
        polygons.append(points)
    
    return polygons

def convert_split(split_dir):
    """Convert all masks in a split to YOLO seg label format."""
    images_dir = os.path.join(split_dir, "images")
    masks_dir = os.path.join(split_dir, "masks")
    labels_seg_dir = os.path.join(split_dir, "labels_seg")
    os.makedirs(labels_seg_dir, exist_ok=True)
    
    image_files = sorted(glob.glob(os.path.join(images_dir, "*.jpg")) + 
                         glob.glob(os.path.join(images_dir, "*.png")))
    
    converted = 0
    for img_path in image_files:
        img_name = Path(img_path).stem
        img = cv2.imread(img_path)
        if img is None:
            continue
        img_h, img_w = img.shape[:2]
        
        # Find all mask files for this image
        mask_files = sorted(glob.glob(os.path.join(masks_dir, f"{img_name}_mask_*.png")))
        
        lines = []
        for mask_path in mask_files:
            polygons = mask_to_yolo_polygons(mask_path, img_w, img_h)
            for poly in polygons:
                coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in poly)
                lines.append(f"0 {coords}")
        
        label_path = os.path.join(labels_seg_dir, f"{img_name}.txt")
        with open(label_path, "w") as f:
            f.write("\n".join(lines) + "\n" if lines else "")
        converted += 1
    
    print(f"  Converted {converted} images in {split_dir}")
    return labels_seg_dir

def main():
    base = r"G:\Abroad\UCLA\MSEng\Capstone\Securiport"
    dataset_dir = os.path.join(base, "data", "synthetic_dataset")
    
    print("Step 1: Converting masks to YOLO polygon labels...")
    for split in ["train", "val"]:
        split_dir = os.path.join(dataset_dir, split)
        convert_split(split_dir)
    
    # Create a seg dataset yaml
    seg_yaml_path = os.path.join(base, "dataset_seg.yaml")
    with open(seg_yaml_path, "w") as f:
        f.write(f"path: {dataset_dir}\n")
        f.write("train: train/images\n")
        f.write("val: val/images\n")
        f.write("\n# Classes\n")
        f.write("names:\n")
        f.write("  0: stamp\n")
    
    # Rename labels_seg -> labels (backup original labels first)
    import shutil
    for split in ["train", "val"]:
        split_dir = os.path.join(dataset_dir, split)
        labels_orig = os.path.join(split_dir, "labels")
        labels_bbox = os.path.join(split_dir, "labels_bbox")
        labels_seg = os.path.join(split_dir, "labels_seg")
        
        if os.path.exists(labels_orig) and not os.path.exists(labels_bbox):
            os.rename(labels_orig, labels_bbox)
            print(f"  Backed up {labels_orig} -> {labels_bbox}")
        
        if os.path.exists(labels_seg) and not os.path.exists(labels_orig):
            os.rename(labels_seg, labels_orig)
            print(f"  Activated {labels_seg} -> {labels_orig}")
    
    # Delete any cache files
    for split in ["train", "val"]:
        cache_file = os.path.join(dataset_dir, split, "labels.cache")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"  Removed cache: {cache_file}")
    
    print("\nStep 2: Fine-tuning YOLOv8s-seg...")
    from ultralytics import YOLO
    model = YOLO("yolov8s-seg.pt")  # Download pretrained seg model
    model.train(
        data=seg_yaml_path,
        epochs=10,
        imgsz=640,
        batch=16,
        project="runs/detect",
        name="stamp_finetune_seg",
        pretrained=True,
    )
    
    print("\nStep 3: Validating YOLOv8s-seg...")
    best_path = os.path.join(base, "runs", "detect", "stamp_finetune_seg", "weights", "best.pt")
    model = YOLO(best_path)
    results = model.val(data=seg_yaml_path, split="val")
    
    print("\n" + "="*60)
    print("TABLE 4.2: Synthetic Validation (YOLOv8-seg)")
    print("="*60)
    print(f"Box mAP50:      {results.box.map50:.4f}")
    print(f"Box mAP50:95:   {results.box.map:.4f}")
    print(f"Box Precision:  {results.box.mp:.4f}")
    print(f"Box Recall:     {results.box.mr:.4f}")
    print(f"Mask mAP50:     {results.seg.map50:.4f}")
    print(f"Mask mAP50:95:  {results.seg.map:.4f}")
    print(f"Mask Precision: {results.seg.mp:.4f}")
    print(f"Mask Recall:    {results.seg.mr:.4f}")
    print("="*60)
    
    # Restore original bbox labels
    print("\nStep 4: Restoring original bbox labels...")
    for split in ["train", "val"]:
        split_dir = os.path.join(dataset_dir, split)
        labels_orig = os.path.join(split_dir, "labels")
        labels_bbox = os.path.join(split_dir, "labels_bbox")
        labels_seg_restore = os.path.join(split_dir, "labels_seg")
        
        if os.path.exists(labels_orig):
            os.rename(labels_orig, labels_seg_restore)
        if os.path.exists(labels_bbox):
            os.rename(labels_bbox, labels_orig)
            print(f"  Restored {labels_bbox} -> {labels_orig}")

if __name__ == "__main__":
    main()
