"""
training/train_yolo.py
Fine-tunes YOLOv8 on the WenxinLens architecture detection dataset.

Prerequisites:
    pip install ultralytics>=8.1

Usage:
    # Classification task (feature-backbone fine-tune)
    python training/train_yolo.py --task classify --epochs 50

    # Object detection task (whole-image proxy boxes, adjust anchors later)
    python training/train_yolo.py --task detect --epochs 100
"""

import argparse
from pathlib import Path


def train(
    task: str,
    epochs: int,
    img_size: int,
    batch: int,
    model_base: str,
    data_dir: Path,
    out_dir: Path,
) -> None:
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        raise SystemExit("ultralytics is not installed. Run: pip install ultralytics>=8.1")

    if task == "classify":
        data_path = str(data_dir / "classification")
        model = YOLO(model_base)         # e.g. yolov8m-cls.pt
        results = model.train(
            data=data_path,
            epochs=epochs,
            imgsz=img_size,
            batch=batch,
            project=str(out_dir),
            name="wenxinlens_cls",
            pretrained=True,
            patience=10,
            save=True,
            seed=42,
        )
        best = Path(results.save_dir) / "weights" / "best.pt"  # type: ignore[attr-defined]
        print(f"\nClassification training done. Best weights: {best}")

    elif task == "detect":
        yaml_path = str(data_dir / "detection" / "data.yaml")
        model = YOLO(model_base)         # e.g. yolov8m.pt
        results = model.train(
            data=yaml_path,
            epochs=epochs,
            imgsz=img_size,
            batch=batch,
            project=str(out_dir),
            name="wenxinlens_det",
            pretrained=True,
            patience=15,
            save=True,
            seed=42,
        )
        best = Path(results.save_dir) / "weights" / "best.pt"  # type: ignore[attr-defined]
        print(f"\nDetection training done. Best weights: {best}")

    else:
        raise ValueError(f"Unknown task: {task}. Choose 'classify' or 'detect'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv8 for WenxinLens")
    parser.add_argument("--task",       choices=["classify", "detect"], default="classify")
    parser.add_argument("--epochs",     type=int, default=50)
    parser.add_argument("--img-size",   type=int, default=640)
    parser.add_argument("--batch",      type=int, default=16)
    parser.add_argument("--model-base", default="yolov8m-cls.pt",
                        help="Pretrained model slug or .pt path (default: yolov8m-cls.pt, use yolov8m.pt for detect)")
    parser.add_argument("--data-dir",   default="datasets/processed")
    parser.add_argument("--out-dir",    default="training/runs")
    args = parser.parse_args()

    train(
        task=args.task,
        epochs=args.epochs,
        img_size=args.img_size,
        batch=args.batch,
        model_base=args.model_base,
        data_dir=Path(args.data_dir),
        out_dir=Path(args.out_dir),
    )


if __name__ == "__main__":
    main()
