import json
import re
import urllib.request

from . import config
from .textutil import sentences

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
QUALITY_PROMPT_RU = (
    "Оцени студенческий текст по трём критериям от 0 до 10.\n\n"
    "1. ЛОГИКА (логичность изложения, последовательность аргументов, отсутствие противоречий)\n"
    "2. ЦЕННОСТЬ (глубина раскрытия темы, наличие фактов/примеров/анализа,.originality)\n"
    "3. СВЯЗНОСТЬ (связи между предложениями и абзацами, лексические повторы, ритм)\n\n"
    "Критерии оценки:\n"
    "- 0-3: слабо (шаблонные фразы без содержания, хаос, нет аргументов)\n"
    "- 4-6: удовлетворительно (есть структура, но поверхностно)\n"
    "- 7-9: хорошо (развёрнуто, логично, с фактами)\n"
    "- 10: отлично (образцовая работа)\n\n"
    'Ответь строго JSON: {{"логика": число, "ценность": число, "связность": число, "комментарий": "кратко"}}'
)

QUALITY_PROMPT_EN = (
    "Rate a student text on three criteria from 0 to 10.\n\n"
    "1. LOGIC (logical flow, argument sequence, no contradictions)\n"
    "2. VALUE (depth, facts/examples/analysis, originality)\n"
    "3. COHERENCE (transitions, vocabulary variety, rhythm)\n\n"
    "Scale:\n"
    "- 0-3: weak (template phrases, no substance)\n"
    "- 4-6: adequate (some structure, superficial)\n"
    "- 7-9: good (well-developed, logical, with facts)\n"
    "- 10: excellent\n\n"
    'Answer strictly JSON: {{"logic": number, "value": number, "coherence": number, "comment": "brief"}}'
)

NUM_RE = re.compile(r'"(?:логика|logic)"\s*:\s*([0-9]+(?:\.[0-9]+)?)')
NUM_RE2 = re.compile(r'"(?:ценность|value)"\s*:\s*([0-9]+(?:\.[0-9]+)?)')
NUM_RE3 = re.compile(r'"(?:связность|coherence)"\s*:\s*([0-9]+(?:\.[0-9]+)?)')
COMMENT_RE = re.compile(r'"(?:комментарий|comment)"\s*:\s*"([^"]*)"')


def _detect_lang(text: str) -> str:
    sample = text[:2000]
    cyr = sum(1 for ch in sample if "\u0400" <= ch <= "\u04FF")
    return "ru" if cyr / max(len(sample), 1) > 0.25 else "en"


def heuristic_quality(text: str) -> dict:
    sents = sentences(text)
    if len(sents) < 3:
        return {"logic": 5.0, "value": 5.0, "coherence": 5.0,
                "comment": "Текст слишком короткий для оценки", "method": "heuristic"}

    lens = [len(s[2].split()) for s in sents]
    avg_len = sum(lens) / len(lens)
    ttr = len(set(text.lower().split())) / max(len(text.split()), 1)
    commas = text.count(",")
    has_structure = any(re.search(r"(введение|заключение|основная часть|в первых|итого|подводя)", text.lower())
                        for _ in [1])
    facts = len(re.findall(r"\b\d{4}\b|\b\d{1,2}\.\d{1,2}\.\d{2,4}\b|[А-Я][а-я]+\s+[А-Я]\.", text))

    logic = min(10, 3 + (2 if has_structure else 0) + (1 if avg_len > 15 else 0) + (1 if commas > 5 else 0))
    value = min(10, 2 + (3 if facts > 0 else 0) + (2 if ttr > 0.55 else 0) + (1 if avg_len > 12 else 0))
    coherence = min(10, 3 + (2 if ttr > 0.6 else 0) + (2 if 10 < avg_len < 30 else 0) + (1 if commas > 3 else 0))

    return {
        "logic": round(logic, 1), "value": round(value, 1), "coherence": round(coherence, 1),
        "comment": "Эвристическая оценка (подключите Ollama для точной оценки)",
        "method": "heuristic",
    }


def ollama_quality(text: str) -> dict | None:
    model = None
    try:
        from .ai_detector import get_ollama_model
        model = get_ollama_model()
    except Exception:
        pass
    if not model:
        return None

    lang = _detect_lang(text)
    prompt = QUALITY_PROMPT_RU if lang == "ru" else QUALITY_PROMPT_EN

    payload = json.dumps({
        "model": model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": "Ты — преподаватель, оценивающий студенческие работы."},
            {"role": "user", "content": prompt + "\n\nТекст для оценки:\n" + text[:3000]},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{config.OLLAMA_URL}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            resp = json.loads(r.read())
    except Exception:
        return None

    content = THINK_RE.sub("", resp.get("message", {}).get("content", ""))
    lm = NUM_RE.search(content)
    vm = NUM_RE2.search(content)
    cm = NUM_RE3.search(content)
    comment_m = COMMENT_RE.search(content)
    if not (lm and vm and cm):
        return None

    def clamp(v):
        return max(0.0, min(10.0, float(v)))

    return {
        "logic": round(clamp(lm.group(1)), 1),
        "value": round(clamp(vm.group(1)), 1),
        "coherence": round(clamp(cm.group(1)), 1),
        "comment": (comment_m.group(1) if comment_m else "")[:500],
        "method": f"ollama:{model}",
    }


def assess(text: str) -> dict:
    from .stylometry import semantic_density
    result = ollama_quality(text)
    if result and any(v > 0 for v in [result.get("logic", 0), result.get("value", 0)]):
        result["semantic_density"] = semantic_density(text)
        return result
    result = heuristic_quality(text)
    result["semantic_density"] = semantic_density(text)
    return result
