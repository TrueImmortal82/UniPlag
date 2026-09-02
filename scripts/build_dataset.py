import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from app.textutil import sentences

TRAIN_DIR = BASE / "data" / "train"
RAW_DIR = TRAIN_DIR / "raw"
HUMAN_EXTRA = TRAIN_DIR / "human"
UA = {"User-Agent": "UniPlagDatasetBot/1.0 (university project)"}
OLLAMA_URL = "http://127.0.0.1:11434"
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

PG_SEARCH_EN = [
    "austen", "dickens", "twain", "hardy", "wilde", "poe",
    "conan doyle", "wells", "shelley", "bronte", "alcott",
    "stoker", "james", "collins", "cather", "crane",
]

RU_TOPICS = [
    "история промышленности", "городская инфраструктура", "современная экология",
    "цифровая экономика", "образовательные методики", "мировая литература",
    "космические исследования", "медицинская статистика", "сельское хозяйство",
    "теория музыки", "архитектура зданий", "климатические изменения",
    "транспортные системы", "кинематограф", "литературная критика",
    "психология обучения", "история науки", "физика частиц",
    "экономика образования", "биоинформатика",
]

EN_TOPICS = [
    "climate change impacts", "renewable energy technologies", "history of cinema",
    "space exploration milestones", "urban infrastructure", "modern psychology",
    "evolutionary biology", "machine learning fundamentals", "linguistics overview",
    "economic inequality", "medical research breakthroughs", "literary criticism",
    "ocean conservation", "quantum computing basics", "philosophy of mind",
    "food science", "architecture history", "transportation systems",
    "public health policy", "environmental law",
]

MAX_CHARS_PER_DOC = 15000


def http_json(url: str, params: dict | None = None, timeout: int = 30) -> dict:
    qs = ("?" + urllib.parse.urlencode(params)) if params else ""
    req = urllib.request.Request(f"{url}{qs}", headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def http_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save_doc(path: Path, text: str) -> None:
    path.write_text(text[:MAX_CHARS_PER_DOC], encoding="utf-8")


def stage_hf_gazeta(count: int) -> int:
    """Russian news from IlyaGusev/gazeta via HF datasets-server."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    start_idx = len(list(RAW_DIR.glob("gazeta_*.txt")))
    collected, offset = 0, 0
    while collected < count:
        batch = min(count - collected, 100)
        data = http_json(
            "https://datasets-server.huggingface.co/rows",
            {"dataset": "IlyaGusev/gazeta", "config": "default", "split": "train",
             "offset": offset, "length": batch},
        )
        rows = data.get("rows", [])
        if not rows:
            break
        for row in rows:
            text = row["row"].get("text", "").strip()
            if len(text) < 500:
                continue
            p = RAW_DIR / f"gazeta_{start_idx + collected:05d}.txt"
            save_doc(p, text)
            collected += 1
            if collected >= count:
                break
        offset += len(rows)
        time.sleep(0.5)
    print(f"gazeta.ru: скачано {collected} статей")
    return collected


def stage_hf_hc3(count: int) -> int:
    """English human answers from hello-simpleai/HC3."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    start_idx = len(list(RAW_DIR.glob("hc3en_*.txt")))
    collected, offset = 0, 0
    while collected < count:
        batch = min(count - collected, 100)
        try:
            data = http_json(
                "https://datasets-server.huggingface.co/rows",
                {"dataset": "hello-simpleai/HC3", "config": "english",
                 "split": "train", "offset": offset, "length": batch},
            )
        except Exception as e:
            print(f"hc3 error at offset {offset}: {e}")
            break
        rows = data.get("rows", [])
        if not rows:
            break
        for row in rows:
            r = row["row"]
            answer = r.get("human_answers", [""])[0] if isinstance(r.get("human_answers"), list) else ""
            if len(answer) < 300:
                continue
            p = RAW_DIR / f"hc3en_{start_idx + collected:05d}.txt"
            save_doc(p, answer)
            collected += 1
            if collected >= count:
                break
        offset += len(rows)
        time.sleep(0.5)
    print(f"HC3 English: скачано {collected} ответов")
    return collected


def stage_gutenberg_en(count: int) -> int:
    """English classic books from Project Gutenberg search."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    start_idx = len(list(RAW_DIR.glob("gutenen_*.txt")))
    seen: set[str] = set()
    ids: list[str] = []
    for author in PG_SEARCH_EN:
        if len(ids) >= count * 2:
            break
        try:
            html = http_text(
                f"https://www.gutenberg.org/ebooks/search/?query={urllib.parse.quote(author)}"
            )
            found = re.findall(r'href="/ebooks/(\d+)"', html)
            for bid in found:
                if bid not in seen:
                    seen.add(bid)
                    ids.append(bid)
            time.sleep(0.7)
        except Exception:
            continue
    collected = 0
    for book_id in ids:
        if collected >= count:
            break
        try:
            raw = http_bytes(f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt")
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
            m = re.search(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^*]*\*\*\*", text, re.IGNORECASE)
            if m:
                text = text[m.end():]
            m = re.search(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", text, re.IGNORECASE)
            if m:
                text = text[: m.start()]
            text = text.strip()[:MAX_CHARS_PER_DOC]
            if len(text) < 3000:
                continue
            p = RAW_DIR / f"gutenen_{start_idx + collected:05d}.txt"
            save_doc(p, text)
            collected += 1
            print(f"gutenberg EN: {collected}/{count} id={book_id}")
            time.sleep(0.8)
        except Exception:
            continue
    print(f"gutenberg EN: скачано {collected} книг")
    return collected


def ollama_generate(topic: str, lang: str = "ru", model: str = "gemma4:e4b") -> str | None:
    system = ("Ты пишешь информативные и связные тексты. "
              "Пиши сплошным текстом без заголовков, списков и markdown.")
    if lang == "ru":
        user = f"Напиши развёрнутый текст на тему «{topic}» объёмом 350–550 слов. Только текст."
    else:
        user = f"Write an informative text on the topic '{topic}', 350–550 words. Text only, no headings."
    payload = json.dumps({
        "model": model,
        "stream": False,
        "options": {"temperature": 0.9, "num_predict": 1400},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read())
    except Exception as e:
        print(f"ollama error: {e}")
        return None
    out = THINK_RE.sub("", resp.get("message", {}).get("content", "")).strip()
    out = re.sub(r"^(конечно|вот|хорошо|sure|of course)[^\n]*\n+", "", out, flags=re.IGNORECASE)
    return out if len(out) > 500 else None


def stage_ollama_gen(count: int, lang: str = "ru") -> int:
    """Generate AI texts via Ollama."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "aigenru" if lang == "ru" else "aigenen"
    start_idx = len(list(RAW_DIR.glob(f"{prefix}_*.txt")))
    topics = RU_TOPICS if lang == "ru" else EN_TOPICS
    rng = random.Random(42 + (0 if lang == "ru" else 999))
    collected = 0
    for i in range(count * 3):
        if collected >= count:
            break
        topic = rng.choice(topics)
        text = ollama_generate(topic, lang)
        if not text:
            continue
        p = RAW_DIR / f"{prefix}_{start_idx + collected:05d}.txt"
        save_doc(p, text)
        collected += 1
        print(f"ollama {lang}: {collected}/{count} «{topic[:50]}…» ({len(text)} симв.)")
    print(f"ollama {lang}: сгенерировано {collected}")
    return collected


def make_chunks(text: str, target: int = 700, min_len: int = 200) -> list[str]:
    sents = [s for _, _, s in sentences(text)]
    chunks, buf, size = [], [], 0
    for s in sents:
        buf.append(s)
        size += len(s)
        if size >= target:
            chunks.append(" ".join(buf))
            buf, size = [], 0
    if buf and size >= min_len:
        chunks.append(" ".join(buf))
    return [re.sub(r"\s+", " ", c).strip() for c in chunks]


def stage_dataset() -> None:
    patterns = {
        "human": [
            ("gazeta_*.txt", "gazeta", 0.4),
            ("hc3en_*.txt", "hc3en", 0.3),
            ("gutenen_*.txt", "gutenen", 0.3),
        ],
        "ai": [
            ("aigenru_*.txt", "aigenru", 1.0),
            ("aigenen_*.txt", "aigenen", 1.0),
            ("aigencr_*.txt", "aigencr", 1.0),
            ("aigence_*.txt", "aigence", 1.0),
        ],
    }
    records = []
    for label, source_list in patterns.items():
        total_chunks = 0
        for pattern, src_prefix, fraction in source_list:
            files = sorted(RAW_DIR.glob(pattern))
            n = max(1, int(len(files) * fraction))
            doc_ids = 0
            for f in files[:n]:
                text = f.read_text(encoding="utf-8")
                if len(text) < 300:
                    continue
                did = hashlib.md5(f.name.encode()).hexdigest()[:10]
                for ch in make_chunks(text):
                    records.append({"id": f"{src_prefix}{did}", "label": label, "text": ch})
                doc_ids += 1
            n_chunks = sum(1 for r in records if r["id"].startswith(src_prefix))
            total_chunks += n_chunks
        print(f"{label}: {total_chunks} чанков")

    seen, uniq = set(), []
    for r in records:
        h = hashlib.md5(r["text"].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            uniq.append(r)

    by_label = {}
    for r in uniq:
        by_label.setdefault(r["label"], []).append(r)
    if not by_label:
        print("нет данных")
        return
    n = min(len(v) for v in by_label.values())
    rng = random.Random(42)
    balanced = []
    for label, items in by_label.items():
        rng.shuffle(items)
        balanced.extend(items[:n])
    rng.shuffle(balanced)

    doc_ids = sorted({r["id"] for r in balanced})
    rng.shuffle(doc_ids)
    val_docs = set(doc_ids[: max(1, int(len(doc_ids) * 0.1))])
    train = [r for r in balanced if r["id"] not in val_docs]
    val = [r for r in balanced if r["id"] in val_docs]

    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRAIN_DIR / "dataset_train.jsonl", "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(TRAIN_DIR / "dataset_val.jsonl", "w", encoding="utf-8") as f:
        for r in val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"итого: {len(uniq)} уникальных чанков, сбалансировано: {len(balanced)}")
    print(f"train: {len(train)} (доков {len(doc_ids) - len(val_docs)}), val: {len(val)} (доков {len(val_docs)})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=[
        "hf-ru", "hf-en", "gutenberg-en", "ollama-ru", "ollama-en", "dataset"
    ], required=True)
    ap.add_argument("--docs", type=int, default=200)
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if args.stage == "hf-ru":
        stage_hf_gazeta(args.docs)
    elif args.stage == "hf-en":
        stage_hf_hc3(args.docs)
    elif args.stage == "gutenberg-en":
        stage_gutenberg_en(args.docs)
    elif args.stage == "ollama-ru":
        stage_ollama_gen(args.docs, "ru")
    elif args.stage == "ollama-en":
        stage_ollama_gen(args.docs, "en")
    elif args.stage == "dataset":
        stage_dataset()
