"""
training/train_architecture_pipeline.py
One-command training pipeline for WenxinLens using real architecture images.

What it does:
1) Prepare dataset splits from datasets/raw/images
2) Evaluate CLIP baseline on test split
3) Train YOLO classifier
4) Train YOLO detector
5) Copy best detector weights to backend model path (models/yolov8_architecture.pt)

Usage examples:
  python training/train_architecture_pipeline.py
  python training/train_architecture_pipeline.py --images-dir datasets/raw/images --epochs-cls 60 --epochs-det 120
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(args: list[str], cwd: Path | None = None) -> None:
    print("\n$", " ".join(args))
    proc = subprocess.run(args, cwd=str(cwd) if cwd else None)
    if proc.returncode != 0:
        raise SystemExit(f"Command failed with code {proc.returncode}: {' '.join(args)}")


def find_latest_best(run_root: Path, run_name: str) -> Path | None:
    candidates = list(run_root.glob(f"{run_name}*/weights/best.pt"))
    # Ultralytics detect runs may be nested under runs/detect/<project>/<name>/weights/best.pt
    candidates += list((run_root.parent / "runs" / "detect").glob(f"**/{run_name}*/weights/best.pt"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def validate_images_dir(images_dir: Path) -> None:
    if not images_dir.exists():
        raise SystemExit(
            f"Images directory not found: {images_dir}\n"
            "Create class folders first, e.g. datasets/raw/images/Forbidden_City/*.jpg"
        )

    class_dirs = [p for p in images_dir.iterdir() if p.is_dir()]
    if not class_dirs:
        raise SystemExit(f"No class folders found in {images_dir}")

    total_images = 0
    for class_dir in class_dirs:
        count = len(list(class_dir.glob("*.jpg"))) + len(list(class_dir.glob("*.jpeg"))) + len(list(class_dir.glob("*.png")))
        total_images += count
        print(f"  - {class_dir.name}: {count} images")

    if total_images < 80:
        print("[warn] Very small dataset. Try at least ~200 images per class for practical results.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train WenxinLens architecture recognizer pipeline")
    parser.add_argument("--images-dir", default="datasets/raw/images")
    parser.add_argument("--data-dir", default="datasets/processed")
    parser.add_argument("--out-dir", default="training/runs")
    parser.add_argument("--split", nargs=3, type=float, default=[0.7, 0.15, 0.15], metavar=("TRAIN", "VAL", "TEST"))
    parser.add_argument("--epochs-cls", type=int, default=50)
    parser.add_argument("--epochs-det", type=int, default=100)
    parser.add_argument("--img-size", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--skip-clip-eval", action="store_true")
    parser.add_argument("--deploy-detector-path", default="models/yolov8_architecture.pt")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    py = sys.executable

    images_dir = project_root / args.images_dir
    data_dir = project_root / args.data_dir
    out_dir = project_root / args.out_dir
    deploy_detector_path = project_root / args.deploy_detector_path
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Validating dataset folders...")
    validate_images_dir(images_dir)

    run_cmd(
        [
            py,
            "datasets/prepare_training_data.py",
            "--images-dir",
            str(images_dir),
            "--out-dir",
            str(data_dir),
            "--split",
            str(args.split[0]),
            str(args.split[1]),
            str(args.split[2]),
        ],
        cwd=project_root,
    )

    if not args.skip_clip_eval:
        run_cmd(
            [
                py,
                "training/evaluate_clip.py",
                "--data-dir",
                str(data_dir),
                "--split",
                "test",
                "--out-json",
                str(out_dir / "clip_eval_test.json"),
            ],
            cwd=project_root,
        )

    run_cmd(
        [
            py,
            "training/train_yolo.py",
            "--task",
            "classify",
            "--epochs",
            str(args.epochs_cls),
            "--img-size",
            str(args.img_size),
            "--batch",
            str(args.batch),
            "--device",
            str(args.device),
            "--workers",
            str(args.workers),
            "--model-base",
            "yolov8m-cls.pt",
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(out_dir),
            *( ["--amp"] if args.amp else [] ),
        ],
        cwd=project_root,
    )

    run_cmd(
        [
            py,
            "training/train_yolo.py",
            "--task",
            "detect",
            "--epochs",
            str(args.epochs_det),
            "--img-size",
            str(args.img_size),
            "--batch",
            str(args.batch),
            "--device",
            str(args.device),
            "--workers",
            str(args.workers),
            "--model-base",
            "yolov8m.pt",
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(out_dir),
            *( ["--amp"] if args.amp else [] ),
        ],
        cwd=project_root,
    )

    det_best = find_latest_best(out_dir, "wenxinlens_det")
    if not det_best:
        raise SystemExit("Could not find trained detector best.pt under training/runs")

    deploy_detector_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(det_best, deploy_detector_path)

    print("\nTraining pipeline complete.")
    print(f"Detector weights deployed to: {deploy_detector_path}")
    print("Next: restart backend to load new YOLO detector weights.")


if __name__ == "__main__":
    main()
