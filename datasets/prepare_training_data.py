"""
datasets/prepare_training_data.py
Converts raw downloaded images + metadata into:
  1. YOLO v8 classification dataset (structure: train/val/test per class folder)
  2. YOLO v8 detection dataset with synthetic bounding boxes  (if bbox metadata present)
  3. A CLIP fine-tuning JSON (image_path, caption pairs)

Usage:
    python datasets/prepare_training_data.py \
        --images-dir  datasets/raw/images \
        --labels-csv  datasets/raw/museum/architecture_images.csv \
        --out-dir     datasets/processed \
        --split       0.7 0.15 0.15

Expected images-dir layout:
    images/
      Forbidden_City/   *.jpg
      Temple_of_Heaven/ *.jpg
      ...
"""

import argparse
import csv
import json
import random
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Class names (must match backend/vision/detector.py ARCHITECTURE_CLASSES order)
# ---------------------------------------------------------------------------
CLASS_NAMES = [
    "Temple of Heaven",
    "Forbidden City",
    "Giant Wild Goose Pagoda",
    "Summer Palace",
    "Shaolin Temple",
    "Zhaozhou Bridge",
    "Yellow Crane Tower",
    "Hakka Tulou",
]

CLASS_SLUG = {name: name.lower().replace(" ", "_") for name in CLASS_NAMES}
SLUG_TO_IDX = {CLASS_SLUG[n]: i for i, n in enumerate(CLASS_NAMES)}


# ---------------------------------------------------------------------------
# Classification dataset (train/val/test)
# ---------------------------------------------------------------------------
def build_classification_dataset(
    images_dir: Path,
    out_dir: Path,
    split: tuple[float, float, float],
) -> None:
    cls_out = out_dir / "classification"
    for split_name in ("train", "val", "test"):
        (cls_out / split_name).mkdir(parents=True, exist_ok=True)

    total = 0
    for class_dir in sorted(images_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png")) + list(class_dir.glob("*.jpeg"))
        if not images:
            continue
        random.shuffle(images)
        n = len(images)
        n_train = int(n * split[0])
        n_val   = int(n * split[1])

        splits_map = {
            "train": images[:n_train],
            "val":   images[n_train:n_train + n_val],
            "test":  images[n_train + n_val:],
        }
        for split_name, split_imgs in splits_map.items():
            dst = cls_out / split_name / class_dir.name
            dst.mkdir(exist_ok=True)
            for img in split_imgs:
                shutil.copy2(img, dst / img.name)
                total += 1

        print(f"  {class_dir.name}: {n} images → train={n_train}, val={n_val}, test={n - n_train - n_val}")

    print(f"Classification dataset: {total} images -> {cls_out}")


# ---------------------------------------------------------------------------
# YOLO detection dataset (uses class-folder images, whole-image bbox as proxy)
# ---------------------------------------------------------------------------
def build_detection_dataset(images_dir: Path, out_dir: Path, split: tuple[float, float, float]) -> None:
    det_out = out_dir / "detection"
    for split_name in ("train", "val", "test"):
        (det_out / split_name / "images").mkdir(parents=True, exist_ok=True)
        (det_out / split_name / "labels").mkdir(parents=True, exist_ok=True)

    # Write data.yaml
    yaml_content = "path: {path}\ntrain: train/images\nval: val/images\ntest: test/images\n\nnc: {nc}\nnames: {names}\n".format(
        path=str(det_out.resolve()).replace('\\', '/'),
        nc=len(CLASS_NAMES),
        names=CLASS_NAMES,
    )
    (det_out / "data.yaml").write_text(yaml_content, encoding="utf-8")

    from PIL import Image as PILImage  # type: ignore

    total = 0
    for class_dir in sorted(images_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        slug = class_dir.name.lower().replace(" ", "_")
        if slug not in SLUG_TO_IDX:
            continue
        class_idx = SLUG_TO_IDX[slug]
        images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        random.shuffle(images)
        n = len(images)
        n_train = int(n * split[0])
        n_val   = int(n * split[1])

        splits_map = {
            "train": images[:n_train],
            "val":   images[n_train:n_train + n_val],
            "test":  images[n_train + n_val:],
        }
        for split_name, split_imgs in splits_map.items():
            for img_path in split_imgs:
                try:
                    with PILImage.open(img_path) as im:
                        w, h = im.size
                except Exception:
                    continue
                dst_img = det_out / split_name / "images" / img_path.name
                shutil.copy2(img_path, dst_img)
                # Whole-image bounding box in YOLO format (cx cy w h normalised)
                label_path = det_out / split_name / "labels" / (img_path.stem + ".txt")
                label_path.write_text(f"{class_idx} 0.5 0.5 1.0 1.0\n", encoding="utf-8")
                total += 1

    print(f"Detection dataset: {total} annotated images -> {det_out}")


# ---------------------------------------------------------------------------
# CLIP fine-tuning pairs
# ---------------------------------------------------------------------------
CAPTIONS: dict[str, list[str]] = {
    "Temple of Heaven": [
        "The Temple of Heaven in Beijing, a circular Ming dynasty altar complex with a blue-tiled triple-roofed Hall of Prayer for Good Harvests",
        "Ancient Chinese imperial temple with distinctive circular design and blue glazed tile roof",
        "Temple of Heaven, Tiantan, ceremonial architecture symbolising the connection between earth and heaven",
    ],
    "Forbidden City": [
        "The Forbidden City, an imperial palace complex with yellow glazed tile roofs and red walls in Beijing",
        "Chinese imperial palace with traditional hip and gable roofs, red columns and intricate dougong brackets",
        "Palace Museum Beijing, UNESCO world heritage site, vast courtyard encircled by walls",
    ],
    "Giant Wild Goose Pagoda": [
        "The Giant Wild Goose Pagoda, a seven-storey Tang dynasty Buddhist pagoda in Xi'an",
        "Ancient brick pagoda built to house Buddhist sutras brought from India by Xuanzang",
        "Goose pagoda Xi'an, limestone and brick, square-plan tiered tower",
    ],
    "Summer Palace": [
        "The Summer Palace in Beijing, a Qing dynasty imperial garden with a marble boat on Kunming Lake",
        "Classical Chinese garden palace with long covered corridor, pagodas and artificial hills",
        "Yi He Yuan, summer retreat of the Qing emperors outside Beijing",
    ],
    "Hakka Tulou": [
        "A Hakka Tulou, massive circular earthen communal dwelling in Fujian, China",
        "Round earthen fortress walled village of the Hakka people, multi-storey rammed earth structure",
        "Tulou, a UNESCO world heritage fortified earthen house of southern Fujian",
    ],
}


def build_clip_pairs(images_dir: Path, out_dir: Path) -> None:
    pairs = []
    for class_dir in sorted(images_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        name = class_dir.name.replace("_", " ").title()
        captions = CAPTIONS.get(name, [f"A photograph of {name}, Chinese ancient architecture"])
        for img_path in class_dir.glob("*.jpg"):
            caption = random.choice(captions)
            pairs.append({"image": str(img_path), "caption": caption, "class": name})

    out_path = out_dir / "clip_pairs.json"
    out_path.write_text(json.dumps(pairs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"CLIP pairs: {len(pairs)} entries -> {out_path}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", default="datasets/raw/images")
    parser.add_argument("--out-dir",    default="datasets/processed")
    parser.add_argument("--split", nargs=3, type=float, default=[0.7, 0.15, 0.15], metavar=("TRAIN", "VAL", "TEST"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    images_dir = Path(args.images_dir)
    out_dir    = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    split_tuple = tuple(args.split)  # type: ignore[arg-type]

    if not images_dir.exists():
        print(f"[!] Images directory not found: {images_dir}")
        print("    Populate it with sub-folders named after each class (e.g. 'Forbidden_City/')")
        return

    build_classification_dataset(images_dir, out_dir, split_tuple)
    build_detection_dataset(images_dir, out_dir, split_tuple)
    build_clip_pairs(images_dir, out_dir)
    print("\nDataset preparation complete.")


if __name__ == "__main__":
    main()
