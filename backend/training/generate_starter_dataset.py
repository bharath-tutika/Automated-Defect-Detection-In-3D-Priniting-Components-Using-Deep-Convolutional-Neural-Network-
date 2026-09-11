"""
Generate initial representative training and validation dataset for 3D Printing Defect Detection.
Creates real synthetic samples representing the 7 defect classes with standard YOLO annotation format.
"""

import sys
from pathlib import Path
import random
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_DIR, DEFECT_CLASSES

DATASET_DIR = BASE_DIR / "dataset"
TRAIN_IMG = DATASET_DIR / "train" / "images"
TRAIN_LBL = DATASET_DIR / "train" / "labels"
VAL_IMG = DATASET_DIR / "val" / "images"
VAL_LBL = DATASET_DIR / "val" / "labels"
TEST_IMG = DATASET_DIR / "test" / "images"
TEST_LBL = DATASET_DIR / "test" / "labels"

for p in [TRAIN_IMG, TRAIN_LBL, VAL_IMG, VAL_LBL, TEST_IMG, TEST_LBL]:
    p.mkdir(parents=True, exist_ok=True)


def draw_print_bed_background(size=640):
    """Generate realistic 3D print bed texture with grid lines."""
    img = np.full((size, size, 3), (35, 40, 45), dtype=np.uint8)
    # Add subtle texture noise
    noise = np.random.normal(0, 5, (size, size, 3)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Draw bed grid lines
    for i in range(0, size, 40):
        cv2.line(img, (i, 0), (i, size), (50, 55, 60), 1)
        cv2.line(img, (0, i), (size, i), (50, 55, 60), 1)
    return img


def generate_sample(class_id, filename_prefix, target_img_dir, target_lbl_dir, size=640):
    img = draw_print_bed_background(size)
    h, w = size, size

    # Base 3D printed object (solid cube or cylinder)
    ox1, oy1 = random.randint(150, 220), random.randint(150, 220)
    ow, oh = random.randint(180, 260), random.randint(180, 260)
    ox2, oy2 = ox1 + ow, oy1 + oh

    # Part base color (e.g. orange / blue / white / grey PLA)
    base_color = random.choice([
        (220, 160, 60),   # Cyan/Blue PLA
        (50, 140, 230),   # Orange PLA
        (200, 200, 210),  # White PLA
        (120, 180, 70),   # Green PLA
    ])

    # Draw base 3D part with layer lines
    cv2.rectangle(img, (ox1, oy1), (ox2, oy2), base_color, -1)
    for ly in range(oy1, oy2, 4):
        cv2.line(img, (ox1, ly), (ox2, ly), (int(base_color[0]*0.8), int(base_color[1]*0.8), int(base_color[2]*0.8)), 1)

    labels = []

    if class_id == 0:  # Normal / Good Print
        # Add normal annotation covering the clean part
        cx = (ox1 + ox2) / 2.0 / w
        cy = (oy1 + oy2) / 2.0 / h
        bw = ow / w
        bh = oh / h
        labels.append((0, cx, cy, bw, bh))

    elif class_id == 1:  # Stringing (thin webs between parts)
        # Draw second pillar
        px1, py1 = ox2 + 40, oy1
        px2, py2 = px1 + 80, oy2
        cv2.rectangle(img, (px1, py1), (px2, py2), base_color, -1)
        
        # Draw stringing web filaments between pillars
        for _ in range(30):
            sy1 = random.randint(oy1 + 10, oy2 - 10)
            sy2 = sy1 + random.randint(-15, 15)
            cv2.line(img, (ox2, sy1), (px1, sy2), (220, 220, 230), 1)
        
        # Defect box around stringing area
        bx1, by1 = ox2 - 5, oy1
        bx2, by2 = px1 + 5, oy2
        cx = (bx1 + bx2) / 2.0 / w
        cy = (by1 + by2) / 2.0 / h
        bw = (bx2 - bx1) / w
        bh = (by2 - by1) / h
        labels.append((1, cx, cy, bw, bh))

    elif class_id == 2:  # Warping (corner lifted off build plate)
        # Draw lifted corner with dark shadow underneath
        corner_pts = np.array([[ox1, oy2], [ox1 + 60, oy2], [ox1, oy2 - 40]], np.int32)
        cv2.fillPoly(img, [corner_pts], (20, 20, 20)) # shadow
        cv2.line(img, (ox1, oy2 - 40), (ox1 + 60, oy2), (180, 50, 50), 2)
        
        bx1, by1 = ox1 - 10, oy2 - 60
        bx2, by2 = ox1 + 80, oy2 + 10
        labels.append((2, (bx1+bx2)/2.0/w, (by1+by2)/2.0/h, (bx2-bx1)/w, (by2-by1)/h))

    elif class_id == 3:  # Layer Shift
        shift_y = oy1 + oh // 2
        shift_amount = 35
        # Shift bottom half
        img[shift_y:oy2, (ox1+shift_amount):(ox2+shift_amount)] = img[shift_y:oy2, ox1:ox2]
        img[shift_y:oy2, ox1:(ox1+shift_amount)] = (35, 40, 45) # background revealed
        
        bx1, by1 = min(ox1, ox1+shift_amount) - 10, shift_y - 20
        bx2, by2 = max(ox2, ox2+shift_amount) + 10, shift_y + 20
        labels.append((3, (bx1+bx2)/2.0/w, (by1+by2)/2.0/h, (bx2-bx1)/w, (by2-by1)/h))

    elif class_id == 4:  # Under-Extrusion (missing material gaps)
        for gy in range(oy1 + 30, oy2 - 30, 25):
            cv2.line(img, (ox1, gy), (ox2, gy), (25, 25, 30), 4)
            cv2.line(img, (ox1, gy+4), (ox2, gy+4), (40, 40, 45), 2)
        bx1, by1 = ox1 - 5, oy1 + 20
        bx2, by2 = ox2 + 5, oy2 - 20
        labels.append((4, (bx1+bx2)/2.0/w, (by1+by2)/2.0/h, (bx2-bx1)/w, (by2-by1)/h))

    elif class_id == 5:  # Over-Extrusion (blobs and zits on surface)
        for _ in range(12):
            bx = random.randint(ox1 + 10, ox2 - 10)
            by = random.randint(oy1 + 10, oy2 - 10)
            br = random.randint(6, 12)
            cv2.circle(img, (bx, by), br, (int(base_color[0]*1.3)%255, int(base_color[1]*1.3)%255, int(base_color[2]*1.3)%255), -1)
        bx1, by1 = ox1 - 5, oy1 - 5
        bx2, by2 = ox2 + 5, oy2 + 5
        labels.append((5, (bx1+bx2)/2.0/w, (by1+by2)/2.0/h, (bx2-bx1)/w, (by2-by1)/h))

    elif class_id == 6:  # Spaghetti Failure (tangled messy nest of extruded filament)
        for _ in range(120):
            pt1 = (random.randint(ox1 - 30, ox2 + 50), random.randint(oy1 - 40, oy2 + 40))
            pt2 = (pt1[0] + random.randint(-40, 40), pt1[1] + random.randint(-40, 40))
            pt3 = (pt2[0] + random.randint(-40, 40), pt2[1] + random.randint(-40, 40))
            pts = np.array([pt1, pt2, pt3], np.int32)
            cv2.polylines(img, [pts], isClosed=False, color=base_color, thickness=random.choice([1, 2, 3]))
        
        bx1, by1 = ox1 - 40, oy1 - 50
        bx2, by2 = ox2 + 60, oy2 + 50
        labels.append((6, (bx1+bx2)/2.0/w, (by1+by2)/2.0/h, (bx2-bx1)/w, (by2-by1)/h))

    # Save image
    img_path = target_img_dir / f"{filename_prefix}.jpg"
    cv2.imwrite(str(img_path), img)

    # Save YOLO format label
    lbl_path = target_lbl_dir / f"{filename_prefix}.txt"
    with open(lbl_path, "w") as f:
        for cid, cx, cy, bw, bh in labels:
            cx = max(0.01, min(0.99, cx))
            cy = max(0.01, min(0.99, cy))
            bw = max(0.02, min(0.98, bw))
            bh = max(0.02, min(0.98, bh))
            f.write(f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")


def build_dataset():
    print("Generating starter dataset for 7 defect classes...")
    # Generate 10 training samples and 3 validation samples per class
    for cid in range(7):
        cname = DEFECT_CLASSES[cid]["name"]
        for i in range(10):
            generate_sample(cid, f"train_{cname}_{i:02d}", TRAIN_IMG, TRAIN_LBL)
        for i in range(3):
            generate_sample(cid, f"val_{cname}_{i:02d}", VAL_IMG, VAL_LBL)
        for i in range(2):
            generate_sample(cid, f"test_{cname}_{i:02d}", TEST_IMG, TEST_LBL)
    print("Dataset generation complete!")


if __name__ == "__main__":
    build_dataset()
