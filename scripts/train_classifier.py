import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

TRAIN_DIR = BASE / "data" / "train"
MODEL_DIR = BASE / "models" / "ai-detector"


def load_jsonl(path: Path) -> tuple[list[str], list[int]]:
    texts, labels = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            texts.append(r["text"])
            labels.append(1 if r["label"] == "ai" else 0)
    return texts, labels


def train_tfidf() -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.pipeline import FeatureUnion, Pipeline

    Xtr, ytr = load_jsonl(TRAIN_DIR / "dataset_train.jsonl")
    Xva, yva = load_jsonl(TRAIN_DIR / "dataset_val.jsonl")

    pipe = Pipeline([
        ("features", FeatureUnion([
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=2,
                                     max_features=250000, sublinear_tf=True)),
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100000,
                                     sublinear_tf=True)),
        ])),
        ("clf", LogisticRegression(C=10.0, max_iter=3000)),
    ])

    t0 = time.time()
    pipe.fit(Xtr, ytr)
    print(f"обучение: {time.time() - t0:.1f} с")

    proba = pipe.predict_proba(Xva)[:, 1]
    pred = (proba >= 0.5).astype(int)
    print(classification_report(yva, pred, target_names=["human", "ai"], digits=3))
    print("матрица ошибок:")
    print(confusion_matrix(yva, pred))

    acc = float((pred == yva).mean())
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(pipe, MODEL_DIR / "model.joblib")
    meta = {"backend": "sklearn", "val_accuracy": round(acc, 4),
            "n_train": len(ytr), "n_val": len(yva), "algo": "tfidf+logreg"}
    (MODEL_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"сохранено: {MODEL_DIR / 'model.joblib'} (val_accuracy={acc:.3f})")
    return meta


def train_bert(base_model: str) -> dict:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
    except ImportError as e:
        raise SystemExit("Нужны torch и transformers: pip install torch transformers") from e

    from sklearn.metrics import accuracy_score

    Xtr, ytr = load_jsonl(TRAIN_DIR / "dataset_train.jsonl")
    Xva, yva = load_jsonl(TRAIN_DIR / "dataset_val.jsonl")

    tok = AutoTokenizer.from_pretrained(base_model)

    def tok_fn(batch):
        return tok(batch["text"], truncation=True, max_length=256)

    from datasets import Dataset
    ds_tr = Dataset.from_dict({"text": Xtr, "label": ytr}).map(tok_fn, batched=True)
    ds_va = Dataset.from_dict({"text": Xva, "label": yva}).map(tok_fn, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(base_model, num_labels=2)

    def metrics(p):
        preds = p.predictions.argmax(-1)
        return {"accuracy": accuracy_score(p.label_ids, preds)}

    args = TrainingArguments(
        output_dir=str(BASE / "data" / "bert_ckpt"),
        num_train_epochs=2,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        eval_strategy="epoch",
        save_strategy="no",
        learning_rate=3e-5,
        fp16=torch.cuda.is_available(),
        report_to=[],
    )
    trainer = Trainer(model=model, args=args, train_dataset=ds_tr, eval_dataset=ds_va, compute_metrics=metrics)
    trainer.train()
    result = trainer.evaluate()
    print("eval:", result)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tok.save_pretrained(MODEL_DIR)
    for junk in (MODEL_DIR / "model.joblib",):
        if junk.exists():
            junk.unlink()
    meta = {"backend": "transformers", "base": base_model,
            "val_accuracy": round(float(result["eval_accuracy"]), 4)}
    (MODEL_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"сохранено: {MODEL_DIR}")
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", choices=["tfidf", "bert"], default="tfidf")
    ap.add_argument("--bert-base", default="cointegrated/rubert-tiny2")
    args = ap.parse_args()

    for f in ("dataset_train.jsonl", "dataset_val.jsonl"):
        if not (TRAIN_DIR / f).exists():
            raise SystemExit(f"Нет {f} — сначала запустите build_dataset.py --stage dataset")
    if args.algo == "tfidf":
        train_tfidf()
    else:
        train_bert(args.bert_base)
