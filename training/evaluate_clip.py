"""
training/evaluate_clip.py
Zero-shot and fine-tuned evaluation of CLIP on the WenxinLens
architecture classification benchmark.

Usage:
    # Zero-shot evaluation with stock ViT-L-14
    python training/evaluate_clip.py --split test

    # Evaluate a fine-tuned checkpoint
    python training/evaluate_clip.py --checkpoint training/runs/clip_finetuned.pt --split test
"""

import argparse
import json
from pathlib import Path

import torch
from PIL import Image

try:
    import open_clip  # type: ignore
except ImportError:
    raise SystemExit("open_clip not installed. Run: pip install open-clip-torch")

# ---------------------------------------------------------------------------
# Class prompts  (mirrors backend/services/vision_service.py)
# ---------------------------------------------------------------------------
CLASS_PROMPTS: dict[str, list[str]] = {
    "Temple of Heaven": [
        "a photo of Temple of Heaven, circular blue-tiled Ming dynasty altar",
        "Tiantan Beijing, triple-eaved ceremonial hall",
    ],
    "Forbidden City": [
        "a photo of the Forbidden City, yellow-roofed imperial palace Beijing",
        "Palace Museum China, massive courtyard complex red walls",
    ],
    "Giant Wild Goose Pagoda": [
        "a photo of Giant Wild Goose Pagoda, seven-storey Tang dynasty brick tower Xi'an",
    ],
    "Summer Palace": [
        "a photo of Summer Palace, Qing dynasty lake garden palace Beijing",
    ],
    "Shaolin Temple": [
        "a photo of Shaolin Temple, Buddhist monastery on Mount Song Henan",
    ],
    "Zhaozhou Bridge": [
        "a photo of Zhaozhou Bridge, ancient stone arch bridge over Xiaohe River",
    ],
    "Yellow Crane Tower": [
        "a photo of Yellow Crane Tower, traditional pagoda on Snake Hill Wuhan",
    ],
    "Hakka Tulou": [
        "a photo of Hakka Tulou, circular rammed-earth communal dwelling Fujian",
    ],
}

CLASS_NAMES = list(CLASS_PROMPTS.keys())


def load_model(checkpoint: str | None, device: torch.device):
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="openai", device=device
    )
    if checkpoint:
        state = torch.load(checkpoint, map_location=device)
        model.load_state_dict(state, strict=False)
        print(f"Loaded fine-tuned weights from {checkpoint}")
    model.eval()
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    return model, preprocess, tokenizer


def build_text_features(model, tokenizer, device: torch.device) -> torch.Tensor:
    all_prompts = [p for prompts in CLASS_PROMPTS.values() for p in prompts]
    class_boundaries = []
    idx = 0
    for prompts in CLASS_PROMPTS.values():
        class_boundaries.append((idx, idx + len(prompts)))
        idx += len(prompts)

    tokens = tokenizer(all_prompts).to(device)
    with torch.no_grad():
        feats = model.encode_text(tokens)
        feats = feats / feats.norm(dim=-1, keepdim=True)

    # Average prompts per class
    averaged = []
    for start, end in class_boundaries:
        averaged.append(feats[start:end].mean(dim=0))
    text_features = torch.stack(averaged)  # (num_classes, dim)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features


def evaluate(data_dir: Path, split: str, model, preprocess, tokenizer, device: torch.device) -> dict:
    split_dir = data_dir / "classification" / split
    if not split_dir.exists():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    text_features = build_text_features(model, tokenizer, device)

    correct = 0
    total   = 0
    per_class: dict[str, dict[str, int]] = {c: {"correct": 0, "total": 0} for c in CLASS_NAMES}

    for class_dir in sorted(split_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        # Map folder name back to class name
        gt_name = class_dir.name.replace("_", " ").title()
        if gt_name not in CLASS_NAMES:
            # Try fuzzy match
            candidates = [c for c in CLASS_NAMES if c.lower() in gt_name.lower() or gt_name.lower() in c.lower()]
            if not candidates:
                print(f"  [!] Skipping unknown class folder: {class_dir.name}")
                continue
            gt_name = candidates[0]
        gt_idx = CLASS_NAMES.index(gt_name)

        for img_path in class_dir.glob("*.jpg"):
            try:
                img = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(device)
            except Exception:
                continue

            with torch.no_grad():
                img_feat = model.encode_image(img)
                img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
                sims = (img_feat @ text_features.T).squeeze(0)
                pred_idx = sims.argmax().item()

            if pred_idx == gt_idx:
                correct += 1
                per_class[gt_name]["correct"] += 1
            total += 1
            per_class[gt_name]["total"] += 1

    accuracy = correct / total if total > 0 else 0.0
    return {"accuracy": accuracy, "correct": correct, "total": total, "per_class": per_class}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir",   default="datasets/processed")
    parser.add_argument("--split",      default="test", choices=["train", "val", "test"])
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--out-json",   default=None)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model, preprocess, tokenizer = load_model(args.checkpoint, device)
    results = evaluate(Path(args.data_dir), args.split, model, preprocess, tokenizer, device)

    print(f"\nOverall accuracy ({args.split}): {results['accuracy']:.4f}  "
          f"({results['correct']}/{results['total']})")
    print("\nPer-class breakdown:")
    for cls, counts in results["per_class"].items():
        t = counts["total"]
        c = counts["correct"]
        acc = c / t if t else 0
        print(f"  {cls:<30s}  {acc:.3f}  ({c}/{t})")

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nResults saved to {args.out_json}")


if __name__ == "__main__":
    main()
