import json
import math
import re
import statistics
import urllib.request

from . import config
from .textutil import sentences

RU_MARKERS = [
    "таким образом", "кроме того", "в заключение", "важно отметить", "стоит отметить",
    "необходимо отметить", "следует отметить", "в современном мире", "играет важную роль",
    "более того", "подводя итог", "резюмируя", "в целом можно сказать", "с одной стороны",
    "с другой стороны", "в частности", "данный", "является", "представляет собой",
]
EN_MARKERS = [
    "in conclusion", "moreover", "furthermore", "it is important to note", "in today's world",
    "plays a crucial role", "overall", "additionally", "in summary", "it is worth noting",
]

JUDGE_PROMPT = (
    "Определи вероятность (0–100), что текст написан языковой моделью, а не человеком.\n"
    "Критерии человека: конкретные личные детали и факты, разговорные конструкции, "
    "неровный ритм фраз, специфические подробности (имена, места, цифры), отступления от темы.\n"
    "Критерии ИИ: обтекаемые общие фразы без конкретики, шаблонные связки "
    "(таким образом, кроме того, важно отметить), идеальная однородная структура.\n"
    "Сначала кратко перечисли найденные признаки, затем поставь оценку.\n"
    'Ответь строго JSON: {"признаки": "...", "ai": число}'
)

OLLAMA_SAMPLES = 3

_pipeline = None
_sk_model = None
_sk_meta: dict = {}
_ollama_model: str | None = None
_ollama_error: str = ""
import threading

OLLAMA_PREFERRED = ("qwen2.5", "llama3.2", "gemma4", "gemma2", "gemma", "mistral", "granite3.3", "phi4")
DEFAULT_AUTOPULL_MODEL = "qwen2.5:1.5b"
_pulling_lock = threading.Lock()
_is_pulling = False
_pull_status = ""


def _try_sklearn():
    global _sk_model, _sk_meta
    path = config.AI_MODEL_DIR / "model.joblib"
    if not path.exists():
        return None
    if _sk_model is None:
        import joblib
        _sk_model = joblib.load(path)
        meta_path = config.AI_MODEL_DIR / "meta.json"
        if meta_path.exists():
            _sk_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return _sk_model


def _try_ml():
    global _pipeline
    if not config.AI_MODEL_DIR.exists():
        return None
    if not (config.AI_MODEL_DIR / "config.json").exists():
        return None
    try:
        from transformers import pipeline
    except ImportError:
        return None
    if _pipeline is None:
        _pipeline = pipeline(
            "text-classification",
            model=str(config.AI_MODEL_DIR),
            tokenizer=str(config.AI_MODEL_DIR),
            truncation=True,
            max_length=512,
        )
    return _pipeline


def _pick_ollama_model(models: list[dict]) -> str | None:
    names = [m.get("name", "") for m in models]
    if config.OLLAMA_MODEL:
        for n in names:
            if n == config.OLLAMA_MODEL or n.split(":")[0] == config.OLLAMA_MODEL:
                return n
        return None
    for pref in OLLAMA_PREFERRED:
        for n in names:
            if n.startswith(pref) and "embed" not in n and "-cloud" not in n and "vision" not in n:
                return n
    for m in models:
        caps = m.get("capabilities") or []
        name = m.get("name", "")
        if "completion" in caps and "embedding" not in caps and "vision" not in caps and "-cloud" not in name:
            return name
    return None


def auto_pull_optimal_model(model_name: str = DEFAULT_AUTOPULL_MODEL) -> bool:
    """Asynchronously pulls the optimal lightweight model in Ollama if none is installed."""
    global _is_pulling, _pull_status, _ollama_model
    with _pulling_lock:
        if _is_pulling:
            return True
        _is_pulling = True
        _pull_status = f"Загрузка оптимальной модели {model_name}..."

    def _pull_worker():
        global _is_pulling, _pull_status, _ollama_model
        try:
            payload = json.dumps({"name": model_name, "stream": False}).encode("utf-8")
            req = urllib.request.Request(
                f"{config.OLLAMA_URL}/api/pull",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                _ = resp.read()
            _ollama_model = model_name
            _pull_status = f"Модель {model_name} успешно загружена и готова к работе."
            print(f"✅ [Ollama] Оптимальная модель {model_name} успешно загружена.")
        except Exception as e:
            _pull_status = f"Ошибка загрузки модели {model_name}: {e}"
            print(f"⚠️ [Ollama] Не удалось загрузить модель {model_name}: {e}")
        finally:
            _is_pulling = False

    t = threading.Thread(target=_pull_worker, daemon=True)
    t.start()
    return True


def get_ollama_status() -> dict:
    """Returns the current operational status of the Ollama service and active model."""
    global _ollama_model, _ollama_error, _is_pulling, _pull_status
    try:
        with urllib.request.urlopen(f"{config.OLLAMA_URL}/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = data.get("models", [])
            active = _pick_ollama_model(models)
            return {
                "available": True,
                "url": config.OLLAMA_URL,
                "active_model": active,
                "installed_models": [m.get("name") for m in models],
                "is_pulling": _is_pulling,
                "pull_status": _pull_status,
                "status_message": f"Подключено к Ollama. Активная модель: {active}" if active else "Ollama активна, но модели не установлены. Запускается автозагрузка...",
            }
    except Exception as e:
        return {
            "available": False,
            "url": config.OLLAMA_URL,
            "active_model": None,
            "installed_models": [],
            "is_pulling": False,
            "pull_status": "",
            "status_message": f"Ollama не обнаружена на {config.OLLAMA_URL}. Установите Ollama с https://ollama.com",
        }


def get_ollama_model() -> str | None:
    global _ollama_model, _ollama_error
    if _ollama_model:
        return _ollama_model
    try:
        with urllib.request.urlopen(f"{config.OLLAMA_URL}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
    except Exception as e:
        _ollama_error = f"Ollama недоступна на {config.OLLAMA_URL} ({e.__class__.__name__}). Установите Ollama: https://ollama.com"
        return None
    models = data.get("models", [])
    _ollama_model = _pick_ollama_model(models)
    if not _ollama_model:
        _ollama_error = f"В Ollama нет подходящей текстовой модели. Запускаем автоматическую загрузку {DEFAULT_AUTOPULL_MODEL}..."
        auto_pull_optimal_model(DEFAULT_AUTOPULL_MODEL)
    return _ollama_model


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_AI_NUM_RE = re.compile(r'"ai"\s*:\s*([0-9]+(?:\.[0-9]+)?)')


def ollama_score_chunk(model: str, chunk: str) -> float | None:
    payload = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": (
                "Ты — лингвист-эксперт по диагностике машинно-сгенерированных текстов. "
                "Оцениваешь только текст и возвращаешь строго JSON."
            )},
            {"role": "user", "content": JUDGE_PROMPT + "\n\nТекст для оценки:\n" + chunk[:3000]},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{config.OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read())
        except Exception:
            return None
        content = _THINK_RE.sub("", resp.get("message", {}).get("content", ""))
        m = _AI_NUM_RE.search(content)
        if m:
            return min(max(float(m.group(1)), 0.0), 100.0) / 100.0
    return None


def ollama_score_stable(model: str, chunk: str) -> float | None:
    scores = []
    for _ in range(OLLAMA_SAMPLES):
        s = ollama_score_chunk(model, chunk)
        if s is None:
            return None
        scores.append(s)
    return statistics.median(scores)


def chunk_sentences(sents: list[tuple[int, int, str]]) -> list[tuple[int, int]]:
    chunks = []
    start_i = 0
    size = 0
    for i, (a, b, s) in enumerate(sents):
        size += len(s)
        if size >= config.OLLAMA_CHUNK_CHARS or i == len(sents) - 1:
            chunks.append((sents[start_i][0], b))
            start_i = i + 1
            size = 0
    return chunks


def _heuristic_sentence_score(sent: str, avg_len: float, marker_hits: set[str]) -> float:
    score = 0.0
    low = sent.lower()
    for m in RU_MARKERS + EN_MARKERS:
        if m in low and m not in marker_hits:
            marker_hits.add(m)
            score += 0.12
    words = len(sent.split())
    if words >= 25:
        score += 0.15
    if words >= 35:
        score += 0.1
    commas = sent.count(",")
    if words > 15 and commas / max(words, 1) < 0.02:
        score += 0.08
    return min(score, 0.9)


def _heuristic_pass(sents, mean_len: float, burstiness: float) -> tuple[list[dict], float, set[str]]:
    marker_hits: set[str] = set()
    per_sent, probs = [], []
    for a, b, s in sents:
        p = _heuristic_sentence_score(s, mean_len, marker_hits)
        base = 0.25 + (0.12 if burstiness < 0.5 else 0.0)
        p_total = min(base + p * (0.6 if len(sents) > 4 else 0.4), 0.95)
        probs.append(p_total)
        per_sent.append({"start": a, "end": b, "text": s[:200], "ai": round(p_total, 3)})
    return per_sent, sum(probs) / len(probs), marker_hits


def detect(text: str) -> dict:
    sents = sentences(text)
    if len(sents) < 2 or len(text.strip()) < 200:
        return {"score": -1.0, "method": "none", "sentences": [],
                "note": "Текст слишком короткий для анализа"}

    lens = [len(s[2].split()) for s in sents]
    mean_len = sum(lens) / len(lens)
    std_len = math.sqrt(sum((x - mean_len) ** 2 for x in lens) / len(lens))
    burstiness = std_len / max(mean_len, 1)

    heur_per, heur_score, markers = _heuristic_pass(sents, mean_len, burstiness)

    ml = _try_ml()
    if ml is not None:
        results = ml([s[2][:1500] for s in sents])
        per_sent, probs = [], []
        for (a, b, s), r in zip(sents, results):
            label = r["label"].lower()
            p_ai = r["score"] if label in ("ai", "fake", "generated", "label_1") else 1.0 - r["score"]
            probs.append(p_ai)
            per_sent.append({"start": a, "end": b, "text": s[:200], "ai": round(p_ai, 3)})
        return {
            "score": round(sum(probs) / len(probs), 3),
            "burstiness": round(burstiness, 3),
            "mean_sentence_words": round(mean_len, 1),
            "markers_found": [],
            "method": f"ml:{config.AI_MODEL_DIR.name}",
            "sentences": per_sent,
            "note": "",
        }

    sk = _try_sklearn()
    if sk is not None:
        from .ensemble import score_text as ensemble_score_text
        ens = ensemble_score_text(text)

        if ens is not None:
            final_score = ens["combined"]
            per_sent = [{"start": a, "end": b, "text": s[:200], "ai": 0.0} for a, b, s in sents]
            for ca, cb in chunk_sentences(sents):
                chunk_score = float(sk.predict_proba([text[ca:cb]])[0][1])
                blended = 0.4 * chunk_score + 0.6 * final_score
                for item in per_sent:
                    if ca <= item["start"] < cb:
                        item["ai"] = round(min(1.0, blended), 3)

            meta = ens.get("_meta", {})
            acc = meta.get("val_accuracy")
            note = "Ансамбль v2: TF-IDF + char n-grams + стилометрия + meta-learner"
            if acc:
                note += f"; val={acc:.0%}"
            note += f"; confidence={ens['confidence']}"

            return {
                "score": round(final_score, 3),
                "burstiness": round(burstiness, 3),
                "mean_sentence_words": round(mean_len, 1),
                "markers_found": [],
                "method": "ensemble-v2",
                "sentences": per_sent,
                "note": note,
                "ensemble": ens,
            }
        else:
            per_sent = [{"start": a, "end": b, "text": s[:200], "ai": 0.0} for a, b, s in sents]
            weighted_sum = weight_total = 0.0
            for ca, cb in chunk_sentences(sents):
                proba = float(sk.predict_proba([text[ca:cb]])[0][1])
                w = max(cb - ca, 1)
                weighted_sum += proba * w
                weight_total += w
                for item in per_sent:
                    if ca <= item["start"] < cb:
                        item["ai"] = round(proba, 3)
            acc = _sk_meta.get("val_accuracy")
            note = "TF-IDF (fallback: ensemble v2 not loaded)"
            if acc:
                note += f"; val={acc:.0%}"
            return {
                "score": round(weighted_sum / max(weight_total, 1), 3),
                "burstiness": round(burstiness, 3),
                "mean_sentence_words": round(mean_len, 1),
                "markers_found": [],
                "method": "ml-sklearn",
                "sentences": per_sent,
                "note": note,
            }

    global _ollama_error
    model = get_ollama_model()
    if model:
        per_sent = [{"start": a, "end": b, "text": s[:200], "ai": 0.0} for a, b, s in sents]
        chunk_scores = []
        failed = False
        for ca, cb in chunk_sentences(sents):
            p = ollama_score_stable(model, text[ca:cb])
            if p is None:
                failed = True
                break
            chunk_scores.append(p)
            for item in per_sent:
                if ca <= item["start"] < cb:
                    item["ai"] = round(p, 3)
        if not failed and chunk_scores:
            llm_score = sum(chunk_scores) / len(chunk_scores)
            final = max(min(0.7 * llm_score + 0.3 * heur_score, 1.0), 0.0)
            note = "Оценка LLM-судьи ориентировочна; для точной детекции подключите ML-модель (см. README)"
            if len(text.strip()) < 1200:
                note += ". Короткий текст снижает надёжность любой оценки"
            return {
                "score": round(final, 3),
                "burstiness": round(burstiness, 3),
                "mean_sentence_words": round(mean_len, 1),
                "markers_found": sorted(markers),
                "method": f"ollama:{model}",
                "sentences": per_sent,
                "note": note,
            }
        reason = f"Ollama ({model}) не ответила корректно"
        _ollama_error = reason
    else:
        reason = _ollama_error or "модель не настроена"

    return {
        "score": round(heur_score, 3),
        "burstiness": round(burstiness, 3),
        "mean_sentence_words": round(mean_len, 1),
        "markers_found": sorted(markers),
        "method": "heuristic",
        "sentences": heur_per,
        "note": f"Эвристический режим ({reason}). Подключите Ollama или локальную ML-модель (см. README)",
    }


if __name__ == "__main__":
    demo = (
        "В современном мире информационные технологии играют важную роль. "
        "Таким образом, необходимо отметить, что цифровые системы являются неотъемлемой частью образования. "
        "Кроме того, важно отметить, что использование искусственного интеллекта представляет собой значительный шаг вперёд. "
        "Подводя итог, можно сказать, что данные технологии будут развиваться дальше."
    )
    print(json.dumps(detect(demo), ensure_ascii=False, indent=2))
