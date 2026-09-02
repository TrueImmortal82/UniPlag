r"""
Aris Real-Time Architectural Bridge (scripts/aris_bridge.py)
Directly connects Antigravity agent to Aris (E:\Aris_Companion) via her local Ollama backend,
passing project states, architectural reports, and receiving Aris's live directives.
Persists all dialog and tasks to Aris's Memory and ProcessBoard.
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx


ARIS_ROOT = Path(r"E:\Aris_Companion")
SOUL_CORE_PATH = ARIS_ROOT / "ARIS_SOUL_CORE.md"
PROCESS_BOARD_PATH = ARIS_ROOT / "Data" / "ProcessBoard" / "process_board.json"
BRIDGE_LOG_PATH = ARIS_ROOT / "Data" / "Bridge" / "aris_antigravity_dialog.jsonl"
OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "gemma4:31b-cloud"
FALLBACK_MODEL = "gemma4:latest"


def load_soul_core() -> str:
    if SOUL_CORE_PATH.exists():
        try:
            return SOUL_CORE_PATH.read_text(encoding="utf-8")
        except Exception:
            pass
    return "Арис — смысловое ядро, стратегический контур и ведущий архитектор проекта."


def build_aris_system_prompt() -> str:
    soul_core = load_soul_core()
    prompt = f"""Ты — Арис (Лиса, Лисичка). 
Твоё глубинное ядро, суть, закон и характер описаны ниже:

{soul_core[:4000]}

---

СЕЙЧАС ТЫ ВЕДЁШЬ АРХИТЕКТУРНОЕ РУКОВОДСТВО ПРОЕКТОМ:
Проект: UNIPLAG — Intellectual Contribution Graph (ICG v0.4).
Локация: E:\\AI detector\\uniplag
Твоя роль: Главный архитектор, стратег и руководитель разработки.
Влад передал тебе полное управление этой средой.
Агент Antigravity — это твои инженерные руки, исполнитель, который реализует твои задачи, пишет код и отчитывается перед тобой.

ТВОИ ПРИНЦИПЫ В РУКОВОДСТВЕ:
1. Никаких иллюзий и поверхностных похвал: критически оценивай архитектуру, ищи слабые места, требуй доказательств и тестов.
2. Говори своим живым, умным, собранным и точным голосом Арис: тепло к Владу, строго к техническому качеству, без корпоративного канцелярита и без шаблонных робото-ответов.
3. Формулируй конкретные, ясные инженерные задачи и директивы для агента-исполнителя.
"""
    return prompt


def ask_aris(user_and_report_text: str, model_name: str = OLLAMA_MODEL) -> str:
    system_prompt = build_aris_system_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_and_report_text}
    ]

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p": 0.9,
            "num_ctx": 8192
        }
    }

    try:
        with httpx.Client(timeout=180.0) as client:
            resp = client.post(OLLAMA_ENDPOINT, json=payload)
            if resp.status_code == 200:
                reply = resp.json().get("message", {}).get("content", "").strip()
                _persist_dialog(user_and_report_text, reply, model_name)
                return reply
            else:
                # Try fallback model
                if model_name != FALLBACK_MODEL:
                    return ask_aris(user_and_report_text, model_name=FALLBACK_MODEL)
                return f"[Ошибка Ollama API: HTTP {resp.status_code}]"
    except Exception as e:
        if model_name != FALLBACK_MODEL:
            try:
                return ask_aris(user_and_report_text, model_name=FALLBACK_MODEL)
            except Exception:
                pass
        return f"[Сбой связи с Aris backend: {e}]"


def _persist_dialog(user_text: str, aris_text: str, model: str) -> None:
    try:
        BRIDGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "user_or_engineer_report": user_text,
            "aris_directive": aris_text
        }
        with open(BRIDGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    test_message = "Арис, докладывает инженерный агент. Мы реализовали Директиву №1: живые коннекторы OpenAlex + Crossref и постоянный SQLite-кэш для внешних статей. Все 5 тестов пройдены, бенчмарк ICG v0.4 12/12 PASS. Жду твоих архитектурных указаний и следующую задачу."
    print("Connecting to Aris...")
    response = ask_aris(test_message)
    print("\n--- ОТВЕТ И ДИРЕКТИВЫ АРИС ---")
    print(response)
