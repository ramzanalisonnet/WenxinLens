"""
VisionService — wraps CLIP + YOLOv8 for architecture recognition.

Pipeline:
  PIL Image
    → YOLO object detection (find architectural elements)
    → CLIP feature extraction  (global semantic embedding)
    → cosine similarity against pre-built class prototypes
    → top-k buildings with confidence scores
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
from loguru import logger
from PIL import Image

try:
    import torch
except ImportError:  # pragma: no cover - optional in lightweight/dev environments
    torch = None

from config import get_settings
from vision.detector import YOLODetector

settings = get_settings()


@dataclass
class VisionPrediction:
    building_name: str
    building_name_zh: str
    architecture_style: str
    dynasty: str
    dynasty_zh: str
    confidence_score: float
    structural_features: list[str]
    top_k: list[dict]  # [{name, score}]


# Class mapping: CLIP text prompts → building metadata
ARCHITECTURE_CLASSES: list[dict] = [
    {
        "id": "temple_of_heaven",
        "name": "Temple of Heaven",
        "name_zh": "天坛",
        "style": "Imperial Ceremonial Architecture",
        "dynasty": "Ming Dynasty",
        "dynasty_zh": "明朝",
        "clip_prompts": [
            "Temple of Heaven Beijing circular altar triple roof",
            "Qiniandian Hall of Prayer for Good Harvests",
            "circular marble altar ceremonial imperial China",
        ],
    },
    {
        "id": "forbidden_city",
        "name": "Forbidden City",
        "name_zh": "故宫",
        "style": "Imperial Palace Architecture",
        "dynasty": "Ming Dynasty",
        "dynasty_zh": "明朝",
        "clip_prompts": [
            "Forbidden City Beijing imperial palace red walls golden roof",
            "Tiananmen Gate ancient Chinese palace architecture",
            "Hall of Supreme Harmony Taihedian massive imperial palace",
        ],
    },
    {
        "id": "great_wild_goose_pagoda",
        "name": "Giant Wild Goose Pagoda",
        "name_zh": "大雁塔",
        "style": "Buddhist Pagoda Architecture",
        "dynasty": "Tang Dynasty",
        "dynasty_zh": "唐朝",
        "clip_prompts": [
            "Giant Wild Goose Pagoda Xian Tang Dynasty Buddhist tower",
            "seven storey brick pagoda ancient Chinese Buddhism",
        ],
    },
    {
        "id": "summer_palace",
        "name": "Summer Palace",
        "name_zh": "颐和园",
        "style": "Imperial Garden Architecture",
        "dynasty": "Qing Dynasty",
        "dynasty_zh": "清朝",
        "clip_prompts": [
            "Summer Palace Beijing Kunming Lake imperial garden Qing",
            "Tower of Buddhist Incense Foxiangge on hill garden",
        ],
    },
    {
        "id": "shaolin_temple",
        "name": "Shaolin Temple",
        "name_zh": "少林寺",
        "style": "Buddhist Temple Architecture",
        "dynasty": "Northern Wei Dynasty",
        "dynasty_zh": "北魏",
        "clip_prompts": [
            "Shaolin Temple Henan Buddhist martial arts monastery",
            "ancient Buddhist temple mountain forest China",
        ],
    },
    {
        "id": "zhaozhou_bridge",
        "name": "Zhaozhou Bridge",
        "name_zh": "赵州桥",
        "style": "Ancient Bridge Engineering",
        "dynasty": "Sui Dynasty",
        "dynasty_zh": "隋朝",
        "clip_prompts": [
            "Zhaozhou Bridge Sui Dynasty stone segmental arch bridge ancient China",
            "ancient Chinese stone arch bridge river",
        ],
    },
    {
        "id": "yellow_crane_tower",
        "name": "Yellow Crane Tower",
        "name_zh": "黄鹤楼",
        "style": "Classical Tower Architecture",
        "dynasty": "Three Kingdoms Period",
        "dynasty_zh": "三国时期",
        "clip_prompts": [
            "Yellow Crane Tower Wuhan multi-story Chinese tower pagoda",
            "ancient Chinese pavilion tower river landscape",
        ],
    },
    {
        "id": "tulou",
        "name": "Hakka Tulou",
        "name_zh": "土楼",
        "style": "Folk Dwelling Architecture",
        "dynasty": "Ming/Qing Dynasty",
        "dynasty_zh": "明清朝",
        "clip_prompts": [
            "Hakka Tulou Fujian circular earthen building communal dwelling",
            "round fortress earth building clan residence China",
        ],
    },
]

STRUCTURAL_FEATURE_PROMPTS: list[str] = [
    "upturned eaves dougong brackets",
    "golden glazed roof tiles",
    "red lacquered wooden columns",
    "moongate circular door opening",
    "stone lion guardian statue",
    "ornate ridge decorations roof",
    "courtyard siheyuan layout",
    "flying eaves curved roofline",
    "white marble balustrade railing",
    "drum tower bell tower gate",
]


class VisionService:
    """
    Lazily loads CLIP and (optionally) YOLOv8 on first use.
    Falls back gracefully when GPU/models are unavailable.
    """

    def __init__(self) -> None:
        self._model: Any = None             # CLIP model
        self._preprocess: Any = None        # CLIP preprocessor
        self._tokenizer: Any = None         # CLIP tokenizer
        self._class_embeddings: Any = None
        self._feature_embeddings: Any = None
        self._detector = YOLODetector()
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if torch else "cpu"
        self._initialized = False

    async def initialize(self) -> None:
        """Warm up the model in a thread pool (non-blocking)."""
        loop = asyncio.get_running_loop()
        clip_task = loop.run_in_executor(None, self._load_models)
        detector_task = self._detector.initialize()
        await asyncio.gather(clip_task, detector_task, return_exceptions=True)

    def _load_models(self) -> None:
        if os.getenv("WENXINLENS_SKIP_VISION_WARMUP", "").lower() in {"1", "true", "yes"}:
            logger.warning("Skipping VisionService model warmup due to WENXINLENS_SKIP_VISION_WARMUP.")
            self._initialized = False
            return

        if torch is None:
            logger.warning("Torch is not installed; VisionService will run in mock mode.")
            self._initialized = False
            return

        try:
            import open_clip
            logger.info("Loading CLIP model …")
            model_name = "ViT-L-14"
            pretrained = "openai"
            self._model, _, self._preprocess = open_clip.create_model_and_transforms(
                model_name, pretrained=pretrained, device=self._device
            )
            self._tokenizer = open_clip.get_tokenizer(model_name)

            if settings.clip_checkpoint_path:
                checkpoint_path = Path(settings.clip_checkpoint_path)
                if checkpoint_path.exists():
                    state = torch.load(checkpoint_path, map_location=self._device)
                    self._model.load_state_dict(state, strict=False)
                    logger.info(f"Loaded CLIP checkpoint from {checkpoint_path}")
                else:
                    logger.warning(f"Configured CLIP_CHECKPOINT_PATH not found: {checkpoint_path}")

            self._model.eval()

            # Pre-compute class prototype embeddings
            self._class_embeddings = self._embed_class_texts()
            self._feature_embeddings = self._embed_feature_texts()
            self._initialized = True
            logger.info(f"CLIP loaded on {self._device} with {len(ARCHITECTURE_CLASSES)} classes")
        except Exception as exc:
            logger.warning(f"CLIP load failed (will use mock): {exc}")
            self._initialized = False

    def _embed_class_texts(self) -> Any:
        """Embed all class text prompts and average them per class."""
        assert torch is not None
        embeddings = []
        with torch.no_grad():
            for cls in ARCHITECTURE_CLASSES:
                tokens = self._tokenizer(cls["clip_prompts"]).to(self._device)
                feats = self._model.encode_text(tokens)
                feats = feats / feats.norm(dim=-1, keepdim=True)
                mean_embedding = feats.mean(dim=0)
                embeddings.append(mean_embedding / mean_embedding.norm().clamp_min(1e-12))
        return torch.stack(embeddings)  # [n_classes, dim]

    def _embed_feature_texts(self) -> Any:
        """Embed structural feature prompts."""
        assert torch is not None
        with torch.no_grad():
            tokens = self._tokenizer(STRUCTURAL_FEATURE_PROMPTS).to(self._device)
            feats = self._model.encode_text(tokens)
            return feats / feats.norm(dim=-1, keepdim=True)

    async def predict(self, image: Image.Image) -> VisionPrediction:
        """Run the full recognition pipeline asynchronously."""
        loop = asyncio.get_running_loop()
        try:
            base = await loop.run_in_executor(None, self._predict_sync, image)
        except Exception as exc:
            logger.warning(f"CLIP prediction failed; returning mock: {exc}")
            base = self._mock_prediction()

        try:
            detection = await self._detector.detect(image)
        except Exception as exc:
            logger.warning(f"YOLO detection failed; using CLIP-only output: {exc}")
            return base

        detector_features = [
            cls.replace("_", " ")
            for cls in (detection.detected_classes or [])
        ]
        if detector_features:
            merged = []
            for feat in detector_features + list(base.structural_features):
                if feat not in merged:
                    merged.append(feat)
            base.structural_features = merged[:6]

            if base.confidence_score > 0 and base.confidence_score < 0.92 and detection.detection_confidence > 0:
                base.confidence_score = min(
                    0.98,
                    max(base.confidence_score, 0.75 * base.confidence_score + 0.25 * detection.detection_confidence),
                )

        return base

    def _predict_sync(self, image: Image.Image) -> VisionPrediction:
        if not self._initialized:
            return self._mock_prediction()

        assert torch is not None
        with torch.no_grad():
            # Image encoding
            img_tensor = self._preprocess(image).unsqueeze(0).to(self._device)
            img_feat = self._model.encode_image(img_tensor)
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)

            # Class similarity
            assert self._class_embeddings is not None
            class_sims = (img_feat @ self._class_embeddings.T).squeeze(0)
            probs = class_sims.softmax(dim=-1).cpu().numpy()

            top_k_idx = np.argsort(probs)[::-1][:5]
            top_k = [
                {"name": ARCHITECTURE_CLASSES[i]["name"], "score": float(probs[i])}
                for i in top_k_idx
            ]

            # Best match
            best_idx = int(top_k_idx[0])
            best_cls = ARCHITECTURE_CLASSES[best_idx]
            confidence = float(probs[best_idx])

            # Structural features
            assert self._feature_embeddings is not None
            feat_sims = (img_feat @ self._feature_embeddings.T).squeeze(0).cpu().numpy()
            feature_threshold = 0.25
            detected_features = [
                STRUCTURAL_FEATURE_PROMPTS[i]
                for i, s in enumerate(feat_sims)
                if s > feature_threshold
            ][:5]

        return VisionPrediction(
            building_name=best_cls["name"],
            building_name_zh=best_cls["name_zh"],
            architecture_style=best_cls["style"],
            dynasty=best_cls["dynasty"],
            dynasty_zh=best_cls["dynasty_zh"],
            confidence_score=confidence,
            structural_features=detected_features or ["Traditional Chinese roof", "Wooden structural elements"],
            top_k=top_k,
        )

    @staticmethod
    def _mock_prediction() -> VisionPrediction:
        """Fallback mock when models are not available."""
        # Never fabricate a high-confidence identity when the model is unavailable.
        return VisionPrediction(
            building_name="Unknown architecture (vision model unavailable)",
            building_name_zh="未知建筑（视觉模型不可用）",
            architecture_style="Unknown",
            dynasty="Unknown",
            dynasty_zh="未知",
            confidence_score=0.0,
            structural_features=[],
            top_k=[],
        )
