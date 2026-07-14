from __future__ import annotations

"""Benchmark: ClaudeExtractor accuracy on the real stamp fixtures across rotation angles.

Rotates in-memory copies of each fixture by several angles and checks whether
date/country/direction still extract correctly. Useful for comparing models
(swap the model in src/ocr/claude_extractor.py) or spot-checking extraction
quality after prompt/pipeline changes. Uses whatever model create_extractor
returns by default.

Findings so far: claude-haiku-4-5 scored 15/20 (failures were mostly misread
date digits, worst at 45deg); claude-sonnet-5 scored 20/20 on the same set —
i.e. accuracy was model-limited, not a rotation problem, so no CV deskew step
is used.

Does not modify the fixture files on disk — only rotates copies in memory.

Run with:
    ANTHROPIC_API_KEY=sk-... python scripts/test_rotation_robustness.py
(or rely on the .env file at repo root, which is loaded automatically)
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ocr.factory import create_extractor_from_config  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "stamps"

ANGLES_DEG = [0, 10, 20, 30, 45]

GROUND_TRUTH = {
    "usa_entry_1997.png": {"date": "1997-06-23", "country": "USA", "direction": "ENTRY"},
    "usa_entry_1998.png": {"date": "1998-08-26", "country": "USA", "direction": "ENTRY"},
    "hongkong_entry_1999.png": {"date": "1999-04-21", "country": "HKG", "direction": "ENTRY"},
    "colombia_entry_1997.png": {"date": "1997-06-01", "country": "COL", "direction": "ENTRY"},
}


def rotate_image(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate around center, expanding the canvas so nothing gets cropped."""
    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    matrix[0, 2] += (new_w - w) / 2
    matrix[1, 2] += (new_h - h) / 2

    return cv2.warpAffine(
        image, matrix, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255)
    )


def main() -> None:
    extractor = create_extractor_from_config()

    results: dict[float, list[bool]] = {angle: [] for angle in ANGLES_DEG}
    confidences: dict[float, list[float]] = {angle: [] for angle in ANGLES_DEG}

    for filename, truth in GROUND_TRUTH.items():
        path = FIXTURES_DIR / filename
        original = cv2.imread(str(path))
        assert original is not None, f"could not load {path}"

        print(f"\n=== {filename} ===")
        for angle in ANGLES_DEG:
            rotated = original.copy() if angle == 0 else rotate_image(original, angle)
            result = extractor.extract(rotated)

            correct = (
                result.date == truth["date"]
                and result.country == truth["country"]
                and result.direction == truth["direction"]
            )
            results[angle].append(correct)
            confidences[angle].append(result.confidence)

            status = "OK" if correct else "WRONG"
            print(
                f"  {angle:>3}deg  [{status:>5}]  date={result.date!r:12} "
                f"country={result.country!r:6} direction={result.direction!r:8} "
                f"confidence={result.confidence:.2f}"
            )

    print("\n=== Summary (accuracy across all 4 stamps, by rotation angle) ===")
    for angle in ANGLES_DEG:
        n_correct = sum(results[angle])
        n_total = len(results[angle])
        avg_conf = sum(confidences[angle]) / len(confidences[angle])
        print(f"  {angle:>3}deg: {n_correct}/{n_total} correct, avg confidence {avg_conf:.2f}")


if __name__ == "__main__":
    main()
