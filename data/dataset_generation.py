import os
import random
import json
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import argparse


def augment_background(bg, target_size=(1000, 1480)):
    """Augments the provided passport background to generate a new background"""
    w, h = bg.size
    if w > target_size[0] and h > target_size[1]:
        left = random.randint(0, w - target_size[0])
        top = random.randint(0, h - target_size[1])
        bg = bg.crop((left, top, left + target_size[0], top + target_size[1]))
    else:
        bg = bg.resize(target_size)
    
    bg = ImageEnhance.Brightness(bg).enhance(random.uniform(0.8, 1.2))
    bg = ImageEnhance.Contrast(bg).enhance(random.uniform(0.8, 1.2))
    bg = ImageEnhance.Color(bg).enhance(random.uniform(0.8, 1.2))
    
    return bg.convert("RGBA")


def augment_stamp(stamp, bg_width):
    """Randomly scales, rotates, lightens/darkens, shifts colors and blurs
    a provided stamp"""
    # random scale from 30% of page width to 70% of page width
    scale = random.uniform(0.30, 0.70)
    new_width = int(bg_width * scale)
    aspect = stamp.size[1] / stamp.size[0]
    new_height = int(new_width * aspect)
    stamp = stamp.resize((new_width, new_height), Image.LANCZOS)
    
    # random rotation -180 degrees to 180 degrees
    angle = random.uniform(-180, 180)
    stamp = stamp.rotate(angle, expand=True)
    
    # random opacity
    opacity = random.uniform(0.6, 1.0)
    r, g, b, a = stamp.split()
    a = a.point(lambda x: int(x * opacity))
    stamp = Image.merge("RGBA", (r, g, b, a))
    
    # random color shift
    stamp = ImageEnhance.Color(stamp).enhance(random.uniform(0.7, 1.0))
    
    # random blur
    blur_radius = random.uniform(0, 1.5)
    if blur_radius > 0.3:
        stamp = stamp.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # random noise on RGB only
    stamp_array = np.array(stamp)
    rgb = stamp_array[:, :, :3].astype(np.int16)
    noise = np.random.randint(-10, 10, rgb.shape, dtype=np.int16)
    stamp_array[:, :, :3] = np.clip(rgb + noise, 0, 255).astype(np.uint8)
    stamp = Image.fromarray(stamp_array)
    
    return stamp, opacity, scale, angle


def get_stamp_position(bg_w, bg_h, sw, sh, placed_stamps, max_attempts=20):
    """Creates a position for a stamp and prevents the stamp
    from completely overlapping with another"""
    max_x = max(0, bg_w - sw)
    max_y = max(0, bg_h - sh)
    
    for _ in range(max_attempts):
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        
        too_close = False
        for px, py, pw, ph in placed_stamps:
            overlap_x = max(0, min(x + sw, px + pw) - max(x, px))
            overlap_y = max(0, min(y + sh, py + ph) - max(y, py))
            overlap_area = overlap_x * overlap_y
            stamp_area = sw * sh
            
            if overlap_area > stamp_area * 0.25:
                too_close = True
                break
        
        if not too_close:
            return x, y
    
    return random.randint(0, max_x), random.randint(0, max_y)


def composite_scene(bg, stamps, n_stamps=None):
    """Generates the full passport background"""
    bg_w, bg_h = bg.size
    
    if n_stamps is None:
        n_stamps = random.randint(1, 6)
    
    scene = bg.copy()
    masks = []
    stamp_metadata = []
    placed_stamps = []
    
    selected_stamps = random.choices(stamps, k=n_stamps)
    
    for stamp in selected_stamps:
        stamp_aug, opacity, scale, angle = augment_stamp(stamp.copy(), bg_w)
        sw, sh = stamp_aug.size
        
        x, y = get_stamp_position(bg_w, bg_h, sw, sh, placed_stamps)
        placed_stamps.append((x, y, sw, sh))
        
        # create binary mask
        mask = Image.new("L", (bg_w, bg_h), 0)
        stamp_alpha = stamp_aug.split()[3]
        mask.paste(stamp_alpha, (x, y))
        masks.append(np.array(mask))
        
        # composite stamp onto scene
        scene.paste(stamp_aug, (x, y), stamp_aug)
        
        stamp_metadata.append({
            "opacity": opacity,
            "scale": scale,
            "rotation": angle,
            "position": (x, y),
            "size": (sw, sh)
        })
    
    return scene.convert("RGB"), masks, stamp_metadata


def save_yolo_detect(binary_mask, img_w, img_h, output_path, mode='a'):
    mask_uint8 = binary_mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return
    
    all_points = np.concatenate(contours)
    x, y, w, h = cv2.boundingRect(all_points)
    
    x_center = (x + w / 2) / img_w
    y_center = (y + h / 2) / img_h
    norm_w = w / img_w
    norm_h = h / img_h
    
    line = f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
    with open(output_path, mode) as f:
        f.write(line + "\n")

def generate_dataset(stamp_dir, background_dir, output_dir, n_scenes=3000, train_split=0.8):
    for split in ["train", "val"]:
        os.makedirs(os.path.join(output_dir, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, "labels"), exist_ok=True)

    print("Loading stamps...")
    stamps = []
    for f in os.listdir(stamp_dir):
        if f.lower().endswith('.png'):
            img = Image.open(os.path.join(stamp_dir, f)).convert("RGBA")
            if img.size[0] > 50 and img.size[1] > 50:
                stamps.append(img)
    print(f"Loaded {len(stamps)} stamps")

    print("Loading backgrounds...")
    backgrounds = []
    for f in os.listdir(background_dir):
        if f.lower().endswith('.png'):
            backgrounds.append(os.path.join(background_dir, f))
    print(f"Loaded {len(backgrounds)} backgrounds")

    all_metadata = []
    n_train = int(n_scenes * train_split)

    for i in range(n_scenes):
        split = "train" if i < n_train else "val"
        image_id = i + 1

        bg_path = random.choice(backgrounds)
        bg = Image.open(bg_path).convert("RGB")
        bg = augment_background(bg)
        bg_w, bg_h = bg.size

        scene, masks, stamp_metadata = composite_scene(bg, stamps)

        scene_filename = f"scene_{i:05d}.jpg"
        scene.save(os.path.join(output_dir, split, "images", scene_filename), quality=95)

        yolo_detect_path = os.path.join(output_dir, split, "labels", f"scene_{i:05d}.txt")

        for j, mask in enumerate(masks):
            binary_mask = (mask > 127).astype(np.uint8)
            save_yolo_detect(binary_mask, bg_w, bg_h, yolo_detect_path)

        all_metadata.append({
            "image": scene_filename,
            "split": split,
            "background": bg_path,
            "stamps": stamp_metadata
        })

        if i % 100 == 0:
            print(f"{i}/{n_scenes} scenes generated...")

    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(all_metadata, f, indent=2)

    print(f"Done! Generated {n_scenes} scenes in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic stamp dataset")
    parser.add_argument("--stamp_dir", type=str, default="clean_stamps_cropped", help="Path to stamp images")
    parser.add_argument("--background_dir", type=str, default="backgrounds/passport_backgrounds", help="Path to background images")
    parser.add_argument("--output_dir", type=str, default="synthetic_dataset", help="Path to output directory")
    parser.add_argument("--n_scenes", type=int, default=5000, help="Number of scenes to generate")
    args = parser.parse_args()

    generate_dataset(
        stamp_dir=args.stamp_dir,
        background_dir=args.background_dir,
        output_dir=args.output_dir,
        n_scenes=args.n_scenes
    )