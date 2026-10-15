"""
YOLOv8 Architecture Detector — object detection preprocessing stage.

Detects architectural elements:
  - Roof type (hip, gable, pyramidal, domed)
  - Structural components (columns, brackets, eaves, pagoda tiers)
  - Material indicators (stone, brick, wood, glazed tiles)

Used as the first stage before CLIP feature extraction.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger
from PIL import Image

from config import get_settings

settings = get_settings()


@dataclass
class DetectionResult:
    detected_classes: list[str]
    bounding_boxes: list[dict]  # [{class, confidence, x1, y1, x2, y2}]
    dominant_class: str
    detection_confidence: float
    preprocessed_regions: list[Image.Image] = field(default_factory=list)


# YOLOv8 class names for architectural elements
ARCHITECTURE_CLASSES = [
    "hip_roof",
    "gable_roof",
    "pyramidal_roof",
    "pagoda_roof",
    "circular_roof",
    "dougong_bracket",
    "upturned_eaves",
    "wooden_column",
    "stone_balustrade",
    "glazed_tile",
    "courtyard",
    "archway",
    "moon_gate",
    "stone_lion",
    "drum_tower",
    "bell_tower",
    "pagoda_tier",
    "earthen_wall",
    "carved_doorway",
    "ceremonial_altar",
]


class YOLODetector:
    """
    YOLOv8-based architectural element detector.
    Falls back to heuristic analysis when model is unavailable.
    """

    def __init__(self) -> None:
        self._model = None
        self._initialized = False

    async def initialize(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

    def _load_model(self) -> None:
        model_path = Path(settings.yolo_model_path)
        if not model_path.exists():
            logger.warning(
                f"YOLOv8 model not found at {model_path}. "
                "Using heuristic detection. "
                "Run `python training/train_yolo.py` to train the model."
            )
            return
        try:
            from ultralytics import YOLO
            self._model = YOLO(str(model_path))
            self._initialized = True
            logger.info(f"YOLOv8 loaded from {model_path}")
        except Exception as exc:
            logger.warning(f"YOLOv8 load failed: {exc}")

    async def detect(self, image: Image.Image) -> DetectionResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._detect_sync, image)

    def _detect_sync(self, image: Image.Image) -> DetectionResult:
        if not self._initialized:
            return self._heuristic_detect(image)

        import numpy as np
        img_array = np.array(image)
        results = self._model(img_array, verbose=False)[0]  # type: ignore[operator]

        boxes = []
        detected_classes = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if conf < settings.vision_confidence_threshold:
                continue
            cls_name = ARCHITECTURE_CLASSES[cls_id] if cls_id < len(ARCHITECTURE_CLASSES) else f"class_{cls_id}"
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
            boxes.append({
                "class": cls_name,
                "confidence": conf,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            })
            detected_classes.append(cls_name)

        # Extract top-scoring region crops for CLIP
        regions = []
        for box in sorted(boxes, key=lambda b: b["confidence"], reverse=True)[:3]:
            region = image.crop((box["x1"], box["y1"], box["x2"], box["y2"]))
            regions.append(region)

        dominant = boxes[0]["class"] if boxes else "unknown"
        confidence = boxes[0]["confidence"] if boxes else 0.0

        return DetectionResult(
            detected_classes=list(set(detected_classes)),
            bounding_boxes=boxes,
            dominant_class=dominant,
            detection_confidence=confidence,
            preprocessed_regions=regions,
        )

    @staticmethod
    def _heuristic_detect(image: Image.Image) -> DetectionResult:
        """
        Return an explicit no-detection result when trained weights are absent.

        Mean image colours cannot reliably identify architectural structures, so
        they must not be reported as detected classes or used as confidence.
        """
        return DetectionResult(
            detected_classes=[],
            bounding_boxes=[],
            dominant_class="unknown",
            detection_confidence=0.0,
            preprocessed_regions=[],
        )


class ImagePreprocessor:
    """Image normalization and augmentation for vision models."""

    @staticmethod
    def preprocess(image: Image.Image, target_size: int = 224) -> Image.Image:
        """Standard preprocessing for CLIP input."""
        # Convert to RGB (handles RGBA, grayscale, etc.)
        image = image.convert("RGB")
        # Resize maintaining aspect ratio, then pad to square
        image = ImagePreprocessor._resize_and_pad(image, target_size)
        return image

    @staticmethod
    def _resize_and_pad(image: Image.Image, size: int) -> Image.Image:
        from PIL import ImageOps
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        padded = Image.new("RGB", (size, size), (255, 255, 255))
        offset = ((size - image.width) // 2, (size - image.height) // 2)
        padded.paste(image, offset)
        return padded

    @staticmethod
    def validate_image(image: Image.Image) -> bool:
        """Reject non-architectural images using basic quality checks."""
        if image.width < 64 or image.height < 64:
            return False
        if image.mode not in {"RGB", "RGBA", "L"}:
            return False
        return True
