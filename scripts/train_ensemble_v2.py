import json
import sys
import time
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
    n_ai = sum(labels)
    n_human = len(labels) - n_ai
    print(f"Dataset: {len(texts)} samples (AI: {n_ai}, human: {n_human})")

    t0 = time.time()
    meta = train_ensemble(texts, labels)
    elapsed = time.time() - t0

    print(f"\nTraining complete in {elapsed:.1f}s")
    print(f"val_accuracy: {meta['val_accuracy']:.4f} +/- {meta['val_std']:.4f}")
    print(f"n_base: {meta['n_base']}, n_meta: {meta['n_meta']}")
    print(f"components: {meta['components']}")
    print(f"saved to: {BASE / 'models' / 'ai-detector'}")
