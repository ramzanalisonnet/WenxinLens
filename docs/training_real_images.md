# Train WenxinLens With Real Architecture Images

This guide is for beginners and follows the current codebase exactly.

## 1. What is now prepared in the code

1. Runtime recognition can consume trained YOLO detector outputs through [backend/services/vision_service.py](backend/services/vision_service.py).
2. Optional CLIP fine-tuned checkpoint loading is supported through `CLIP_CHECKPOINT_PATH` in [backend/config.py](backend/config.py).
3. One-command end-to-end training is available in [training/train_architecture_pipeline.py](training/train_architecture_pipeline.py).

## 2. Prerequisites

1. Python 3.11 or 3.12 (recommended by this repo).
2. Backend dependencies installed from [backend/requirements.txt](backend/requirements.txt).
3. GPU is recommended for training speed, CPU is possible but slow.

## 3. Prepare your image folders

Create this structure:

- `datasets/raw/images/Temple_of_Heaven/*.jpg`
- `datasets/raw/images/Forbidden_City/*.jpg`
- `datasets/raw/images/Giant_Wild_Goose_Pagoda/*.jpg`
- `datasets/raw/images/Summer_Palace/*.jpg`
- `datasets/raw/images/Shaolin_Temple/*.jpg`
- `datasets/raw/images/Zhaozhou_Bridge/*.jpg`
- `datasets/raw/images/Yellow_Crane_Tower/*.jpg`
- `datasets/raw/images/Hakka_Tulou/*.jpg`

Tips:

1. Start with at least 200 images per class.
2. Keep class sizes roughly balanced.
3. Remove mislabeled images aggressively.

## 4. Run one-command pipeline

From project root:

```powershell
python training/train_architecture_pipeline.py
```

Optional custom run:

```powershell
python training/train_architecture_pipeline.py --images-dir datasets/raw/images --epochs-cls 60 --epochs-det 120 --img-size 640 --batch 16
```

What it does:

1. Runs [datasets/prepare_training_data.py](datasets/prepare_training_data.py)
2. Runs [training/evaluate_clip.py](training/evaluate_clip.py)
3. Runs [training/train_yolo.py](training/train_yolo.py) for classification
4. Runs [training/train_yolo.py](training/train_yolo.py) for detection
5. Copies best detector weight to `models/yolov8_architecture.pt`

## 5. Restart backend to use new model

After training completes:

```powershell
cd backend
$env:FAST_STARTUP='false'
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

The backend will load your detector from `YOLO_MODEL_PATH` (default: `models/yolov8_architecture.pt`).

## 6. Optional: load fine-tuned CLIP checkpoint

If you trained a CLIP checkpoint separately, set:

```dotenv
CLIP_CHECKPOINT_PATH=training/runs/clip_finetuned.pt
```

Then restart backend.

## 7. Validate recognition quickly

Call API docs endpoint at:

- `http://127.0.0.1:8010/docs`

Use `POST /api/v1/recognition/analyze` with test images from your dataset.

## 8. Troubleshooting

1. If training crashes on install issues, use Python 3.11/3.12.
2. If recognition still looks generic, verify `models/yolov8_architecture.pt` was replaced after training.
3. If CLIP checkpoint is configured but missing, backend logs a warning and uses base CLIP.
4. If GPU OOM occurs, lower `--batch` and optionally `--img-size`.
