import json

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline, FeatureUnion

from . import config
from .stylometry import extract_stylometric_features, semantic_density, FEATURE_NAMES


def _build_tfidf_pipeline():
    return Pipeline([
        ("features", FeatureUnion([
            ("char", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5),
                min_df=2, max_features=200000, sublinear_tf=True,
            )),
            ("word", TfidfVectorizer(
                ngram_range=(1, 2), min_df=2, max_features=80000,
                sublinear_tf=True,
            )),
        ])),
        ("clf", LogisticRegression(C=10.0, max_iter=3000)),
    ])


def _build_char_ngrams_pipeline():
    return Pipeline([
        ("char", TfidfVectorizer(
            analyzer="char", ngram_range=(3, 6),
            min_df=2, max_features=300000, sublinear_tf=True,
        )),
        ("clf", LogisticRegression(C=5.0, max_iter=3000)),
    ])


def _build_stylometry_pipeline():
    return Pipeline([
        ("clf", LogisticRegression(C=1.0, max_iter=1000)),
    ])


class EnsembleClassifier:
    def __init__(self):
        self.tfidf_pipe = _build_tfidf_pipeline()
        self.char_pipe = _build_char_ngrams_pipeline()
        self.styl_pipe = _build_stylometry_pipeline()
        self.meta_learner = LogisticRegression(C=1.0, max_iter=1000)
        self.is_fitted = False
        self.meta = {}

    def _extract_styl_features(self, texts: list[str]) -> np.ndarray:
        features = []
        for t in texts:
            feat = extract_stylometric_features(t)
            features.append([feat.get(name, 0.0) for name in FEATURE_NAMES])
        return np.array(features)

    def fit(self, texts: list[str], labels: list[int]) -> dict:
        n = len(texts)
        n_base = int(n * 0.7)
        indices = np.random.RandomState(42).permutation(n)
        base_idx = indices[:n_base]
        meta_idx = indices[n_base:]

        base_texts = [texts[i] for i in base_idx]
        base_labels = [labels[i] for i in base_idx]
        meta_texts = [texts[i] for i in meta_idx]
        meta_labels = [labels[i] for i in meta_idx]

        if len(meta_texts) < 10:
            base_texts = texts
            base_labels = labels
            meta_texts = texts
            meta_labels = labels

        self.tfidf_pipe.fit(base_texts, base_labels)
        self.char_pipe.fit(base_texts, base_labels)

        styl_X = self._extract_styl_features(base_texts)
        self.styl_pipe.fit(styl_X, base_labels)

        meta_features = self._get_base_predictions(meta_texts)
        self.meta_learner.fit(meta_features, meta_labels)

        self.is_fitted = True

        cv_scores = cross_val_score(
            self.meta_learner, meta_features, meta_labels,
            cv=min(5, len(meta_labels)), scoring="accuracy"
        )

        config.AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.tfidf_pipe, config.AI_MODEL_DIR / "tfidf_pipe.joblib")
        joblib.dump(self.char_pipe, config.AI_MODEL_DIR / "char_pipe.joblib")
        joblib.dump(self.styl_pipe, config.AI_MODEL_DIR / "styl_pipe.joblib")
        joblib.dump(self.meta_learner, config.AI_MODEL_DIR / "meta_learner.joblib")

        self.meta = {
            "algo": "ensemble-v2-tfidf+char+stylometry+meta",
            "val_accuracy": round(float(cv_scores.mean()), 4),
            "val_std": round(float(cv_scores.std()), 4),
            "n_train": len(labels),
            "n_base": len(base_texts),
            "n_meta": len(meta_texts),
            "feature_names": FEATURE_NAMES,
            "components": ["tfidf(char+word)", "char_ngrams(3-6)", "stylometry(18)", "meta_learner"],
        }
        (config.AI_MODEL_DIR / "ensemble_meta.json").write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self.meta

    def _get_base_predictions(self, texts: list[str]) -> np.ndarray:
        tfidf_proba = self.tfidf_pipe.predict_proba(texts)[:, 1]
        char_proba = self.char_pipe.predict_proba(texts)[:, 1]

        styl_X = self._extract_styl_features(texts)
        styl_proba = self.styl_pipe.predict_proba(styl_X)[:, 1]

        return np.column_stack([tfidf_proba, char_proba, styl_proba])

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        base_preds = self._get_base_predictions(texts)
        return self.meta_learner.predict_proba(base_preds)

    def predict(self, texts: list[str]) -> np.ndarray:
        proba = self.predict_proba(texts)
        return (proba[:, 1] >= 0.5).astype(int)

    def score_text(self, text: str) -> dict:
        base_preds = self._get_base_predictions([text])
        meta_proba = self.meta_learner.predict_proba(base_preds)[0]

        tfidf_score = float(base_preds[0][0])
        char_score = float(base_preds[0][1])
        styl_score = float(base_preds[0][2])
        final_score = float(meta_proba[1])

        sd = semantic_density(text)

        if final_score < 0.3:
            confidence = "low"
        elif final_score < 0.6:
            confidence = "medium"
        else:
            confidence = "high"

        uncertainty = (
            abs(styl_score - final_score) * 0.2 +
            abs(char_score - final_score) * 0.2 +
            abs(tfidf_score - final_score) * 0.1 +
            (0.15 if sd < 0.3 else 0.0) +
            (0.1 if sd > 0.7 else 0.0)
        )
        width = max(0.05, min(0.3, uncertainty))
        lo = max(0.0, final_score - width)
        hi = min(1.0, final_score + width)

        return {
            "combined": round(final_score, 4),
            "tfidf": round(tfidf_score, 4),
            "char_ngrams": round(char_score, 4),
            "stylometry": round(styl_score, 4),
            "density": round(sd, 4),
            "confidence": confidence,
            "confidence_interval": f"{lo:.0%}–{hi:.0%}",
        }


_ensemble_instance: EnsembleClassifier | None = None


def get_ensemble() -> EnsembleClassifier | None:
    global _ensemble_instance
    if _ensemble_instance is not None:
        return _ensemble_instance

    if not (config.AI_MODEL_DIR / "meta_learner.joblib").exists():
        return None

    ens = EnsembleClassifier()
    try:
        ens.tfidf_pipe = joblib.load(config.AI_MODEL_DIR / "tfidf_pipe.joblib")
        ens.char_pipe = joblib.load(config.AI_MODEL_DIR / "char_pipe.joblib")
        ens.styl_pipe = joblib.load(config.AI_MODEL_DIR / "styl_pipe.joblib")
        ens.meta_learner = joblib.load(config.AI_MODEL_DIR / "meta_learner.joblib")
        meta_path = config.AI_MODEL_DIR / "ensemble_meta.json"
        if meta_path.exists():
            ens.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ens.is_fitted = True
        _ensemble_instance = ens
        return ens
    except Exception:
        return None


def score_text(text: str) -> dict | None:
    ens = get_ensemble()
    if ens is None:
        return None
    return ens.score_text(text)


def train_ensemble(texts: list[str], labels: list[int]) -> dict:
    ens = EnsembleClassifier()
    return ens.fit(texts, labels)
