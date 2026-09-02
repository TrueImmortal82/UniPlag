import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

TRAIN_DIR = BASE / "data" / "train"


def load_texts_labels():
    texts, labels = [], []
    for path in sorted(TRAIN_DIR.glob("dataset_*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                texts.append(r["text"])
                labels.append(1 if r["label"] == "ai" else 0)
    return texts, labels


if __name__ == "__main__":
    from app.ensemble import train_ensemble

    texts, labels = load_texts_labels()
    print(f"Loaded {len(texts)} samples ({sum(labels)} ai, {len(labels)-sum(labels)} human)")

    meta = train_ensemble(texts, labels)
    print(f"Ensemble trained: val_accuracy={meta['val_accuracy']:.3f} +/- {meta['val_std']:.3f}")
    print(f"Features: {meta['feature_names']}")
