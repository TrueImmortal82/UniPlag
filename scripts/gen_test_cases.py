import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TESTS_DIR = BASE / "tests"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma4:e4b"

THINK_RE = __import__("re").compile(r"<think>.*?</think>", __import__("re").DOTALL)


def ollama_gen(prompt: str, lang: str = "ru") -> str | None:
    p = f"Write a {lang} text about: {prompt}. Write naturally, no commentary." if lang == "en" else f"Напиши текст на русском на тему: {prompt}. Пиши естественно, без комментариев."
    data = json.dumps({"model": MODEL, "prompt": p, "stream": False, "options": {"num_predict": 800}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read())
    except Exception as e:
        print(f"  ollama error: {e}")
        return None
    out = THINK_RE.sub("", resp.get("message", {}).get("content", "")).strip()
    return out if len(out) > 200 else None


def save_test_case(subdir: str, case_id: str, text: str, meta: dict):
    d = TESTS_DIR / subdir
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{case_id}.txt").write_text(text, encoding="utf-8")
    (d / f"{case_id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  saved: {subdir}/{case_id} ({len(text)} chars)")


if __name__ == "__main__":
    print("=== Generating AI test cases ===\n")

    # 1. AI-Short: short AI text (~150 words)
    print("1. AI-Short")
    text = ollama_gen("write a brief 100-word paragraph about climate change", "en")
    if text:
        save_test_case("ai_short", "AI-SHORT-001", text, {
            "id": "AI-SHORT-001", "ground_truth": "ai", "source": MODEL,
            "language": "en", "description": "Short AI-generated paragraph (~150 words)",
        })

    # 2. AI-Long: long AI text (~2000 words)
    print("\n2. AI-Long")
    text = ollama_gen("write a detailed 1500-word essay about the future of artificial intelligence in education, covering benefits, challenges, and ethical considerations", "en")
    if text:
        save_test_case("ai_long", "AI-LONG-001", text, {
            "id": "AI-LONG-001", "ground_truth": "ai", "source": MODEL,
            "language": "en", "description": "Long AI-generated essay (~1500 words)",
        })

    # 3. AI-Humanized: AI text rewritten to sound human
    print("\n3. AI-Humanized")
    text = ollama_gen("rewrite this in a casual, informal tone with personal opinions and some grammar imperfections: 'Artificial intelligence has revolutionized numerous industries. The implementation of machine learning algorithms has enabled organizations to optimize their operations and improve decision-making processes.' Make it sound like a person writing a blog post.", "en")
    if text:
        save_test_case("ai_humanized", "AI-HUMANIZED-001", text, {
            "id": "AI-HUMANIZED-001", "ground_truth": "ai", "source": MODEL,
            "language": "en", "description": "AI text rewritten to sound human/casual",
        })

    # 4. AI-Conversational: AI text mimicking casual conversation
    print("\n4. AI-Conversational")
    text = ollama_gen("write a casual conversation between two friends discussing their weekend plans, using slang and informal language", "en")
    if text:
        save_test_case("ai_humanized", "AI-CONVERSATIONAL-001", text, {
            "id": "AI-CONVERSATIONAL-001", "ground_truth": "ai", "source": MODEL,
            "language": "en", "description": "AI text mimicking casual conversation",
        })

    # 5. AI-Academic: AI text mimicking academic style
    print("\n5. AI-Academic")
    text = ollama_gen("write a formal academic abstract about the impact of social media on mental health, using technical terminology and citation-style language", "en")
    if text:
        save_test_case("ai_long", "AI-ACADEMIC-001", text, {
            "id": "AI-ACADEMIC-001", "ground_truth": "ai", "source": MODEL,
            "language": "en", "description": "AI text mimicking academic paper abstract",
        })

    # 6. AI-Russian-formal
    print("\n6. AI-Russian-formal")
    text = ollama_gen("напиши формальный отчёт о результатах исследования влияния удалённой работы на производительность сотрудников", "ru")
    if text:
        save_test_case("ai_long", "AI-RU-FORMAL-001", text, {
            "id": "AI-RU-FORMAL-001", "ground_truth": "ai", "source": MODEL,
            "language": "ru", "description": "AI-generated formal Russian report",
        })

    print("\n=== Done ===")
