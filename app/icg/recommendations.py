"""
UniPlag & ICG Pedagogical Recommendation Engine (app/icg/recommendations.py)
=============================================================================
Analyzes epistemic DAG metrics, synthesis ratios, inference anchors, and argumentation
quality to generate personalized, actionable recommendations for students.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional


def generate_icg_recommendations(
    icg_data: Optional[Dict[str, Any]],
    plag_score: float,
    ai_score: float,
    icg_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Generates structured, multi-dimensional pedagogical guidance for students
    to improve the academic quality, intellectual contribution, and reasoning structure of their works.
    """
    if not icg_data:
        icg_data = {}

    summary = icg_data.get("summary") or icg_data.get("metrics_summary") or {}
    ratios = icg_data.get("ratios") or {}

    # Extract core metrics with fallbacks
    ics = icg_score if icg_score is not None else (summary.get("intellectual_contribution_score", 0.0) * 100.0)
    synthesis_ratio = ratios.get("synthesis", summary.get("synthesis_ratio", 0.0))
    novel_synthesis = ratios.get("source_novel_synthesis", summary.get("source_novel_synthesis_ratio", 0.0))
    higher_synthesis = ratios.get("higher_order_synthesis", summary.get("higher_order_synthesis_ratio", 0.0))
    total_synthesis = synthesis_ratio + novel_synthesis + higher_synthesis

    inference_ratio = ratios.get("inference", summary.get("inference_ratio", 0.0))
    reproduction_ratio = ratios.get("reproduction", summary.get("reproduction_ratio", 0.0))
    unsupported_ratio = ratios.get("unsupported", summary.get("unsupported_ratio", 0.0))
    contradictory_ratio = ratios.get("contradictory", summary.get("contradictory_ratio", 0.0))
    
    novelty_score = summary.get("novelty_score", 0.0)
    coherence = summary.get("reasoning_coherence", 0.0)
    evidence_coverage = summary.get("evidence_coverage", 0.0)

    strengths: List[str] = []
    growth_areas: List[Dict[str, str]] = []
    action_checklist: List[str] = []
    phrasing_templates: List[Dict[str, str]] = []

    # 1. Evaluate Strengths
    if total_synthesis >= 0.25:
        strengths.append(
            f"Отличный уровень синтеза источников ({round(total_synthesis * 100)}%): "
            "вы успешно сопоставляете различные точки зрения и объединяете данные нескольких авторов."
        )
    if inference_ratio >= 0.20:
        strengths.append(
            f"Выраженная авторская позиция ({round(inference_ratio * 100)}% выводов): "
            "в работе присутствуют самостоятельные логические заключения, вытекающие из анализа."
        )
    if unsupported_ratio <= 0.10:
        strengths.append(
            "Высокая доказательная дисциплина: практически все утверждения подкреплены ссылками или фактами."
        )
    if 100.0 - plag_score >= 80.0:
        strengths.append(
            f"Высокая оригинальность текста ({round(100.0 - plag_score, 1)}%): корректная работа с заимствованиями."
        )
    if not strengths:
        strengths.append("Работа обладает понятной базовой структурой и готова к аналитическому усилению.")

    # 2. Identify Top Priority & Growth Areas
    top_priority = ""

    # Priority A: Critical Contradictions
    if contradictory_ratio > 0.08:
        top_priority = "Устранение логических противоречий между разделами работы."
        growth_areas.append({
            "title": "Логическая согласованность тезисов",
            "tag": "Критично",
            "tag_class": "bad",
            "advice": (
                f"Выявлено {round(contradictory_ratio * 100)}% противоречивых суждений. "
                "Проверьте, чтобы выводы в заключительных параграфах не опровергали исходные предпосылки во введении. "
                "Уточните границы применимости используемых определений."
            ),
        })
        action_checklist.append("Провести сквозную вычитку терминов и промежуточных выводов для устранения взаимоисключающих тезисов.")

    # Priority B: High Unsupported Claims
    if unsupported_ratio > 0.20:
        if not top_priority:
            top_priority = "Обоснование бездоказательных утверждений ссылками на авторитетные источники."
        growth_areas.append({
            "title": "Доказательная база и цитирование",
            "tag": "Важно",
            "tag_class": "bad" if unsupported_ratio > 0.35 else "warn",
            "advice": (
                f"Около {round(unsupported_ratio * 100)}% тезисов в работе не содержат ссылок на литературу или расчёты. "
                "Каждое утверждение о свойствах объекта или тенденциях должно подтверждаться ссылкой на ГОСТ/исследование или расчётом."
            ),
        })
        action_checklist.append("Добавить библиографические ссылки на научные статьи или стандарты ко всем эмпирическим фактам.")

    # Priority C: Low Synthesis (Pure isolated reproduction)
    if total_synthesis < 0.15:
        if not top_priority:
            top_priority = "Преодоление реферативности — переход к междисциплинарному синтезу литературы."
        growth_areas.append({
            "title": "Синтез и сопоставление источников",
            "tag": "Точка роста",
            "tag_class": "warn",
            "advice": (
                f"Текущий уровень синтеза составляет лишь {round(total_synthesis * 100)}%. "
                "Избегайте изолированного пересказа («Автор А сказал... Затем автор Б сказал...»). "
                "Сравнивайте их: укажите, в чём автор Б дополняет автора А, а в чём их методики расходятся."
            ),
        })
        action_checklist.append("Переписать обзорную главу, объединив авторов в сравнительные смысловые кластеры.")

    # Priority D: Low Inference (Lack of own conclusions)
    if inference_ratio < 0.12:
        if not top_priority:
            top_priority = "Усиление самостоятельных выводов и авторского вклада."
        growth_areas.append({
            "title": "Формулирование авторских выводов",
            "tag": "Точка роста",
            "tag_class": "warn",
            "advice": (
                f"Доля самостоятельных выводов составляет {round(inference_ratio * 100)}%. "
                "Завершайте каждый подраздел обобщающим абзацем: «Таким образом, проведённый анализ показывает...», "
                "«Из этого следует необходимость разработки нового алгоритма...»."
            ),
        })
        action_checklist.append("Добавить в конец каждого параграфа 2–3 предложения с собственным резюме.")

    # Priority E: AI Paraphrase / Density Notice
    if ai_score >= 0.40:
        growth_areas.append({
            "title": "Стилометрическая глубина и авторский почерк",
            "tag": "Стиль",
            "tag_class": "warn",
            "advice": (
                "Текст содержит характерные паттерны сглаженных языковых моделей (шаблонные вводные конструкции, повторяющийся синтаксис). "
                "Добавьте конкретные предметные детали, схемы, математические формулы и специфическую терминологию предметной области."
            ),
        })
        action_checklist.append("Разбавить текст конкретными практическими кейсами, формулами и таблицами сравнения параметров.")

    if not top_priority:
        top_priority = "Поддержание текущего высокого академического уровня и подготовка к защите."

    if not action_checklist:
        action_checklist.append("Оформить библиографический список по ГОСТ 7.0.100-2018.")
        action_checklist.append("Подготовить тезисы доклада с акцентом на авторский синтез и выводы.")

    # 3. Phrasing Templates for Boosting ICG
    phrasing_templates = [
        {
            "goal": "Для глубокого синтеза источников (Synthesis)",
            "example": "«Сопоставляя методику оценки, предложенную [1], с результатами исследования [2], можно констатировать, что ограничение первого подхода преодолевается за счёт внедрения...»",
        },
        {
            "goal": "Для авторского вывода (Inference)",
            "example": "«На основе проведённого факторного анализа мы приходим к выводу, что ключевым драйвером эффективности выступает... что подтверждается полученной зависимостью...»",
        },
        {
            "goal": "Для разрешения противоречий (Paradox Resolution)",
            "example": "«Несмотря на кажущееся противоречие между выводами [3] и [4], данное расхождение объясняется различными граничными условиями эксперимента, а именно...»",
        },
    ]

    # Summary verdict text
    if ics >= 65.0:
        verdict = "Работа демонстрирует высокий исследовательский потенциал и самостоятельный научный синтез."
        verdict_class = "ok"
    elif ics >= 40.0:
        verdict = "Работа имеет хороший фундамент, но требует усиления сопоставительного анализа и авторских выводов."
        verdict_class = "warn"
    else:
        verdict = "Работа носит преимущественно реферативный характер. Требуется глубокая переработка структуры рассуждений."
        verdict_class = "bad"

    return {
        "ics_score": round(ics, 1),
        "verdict": verdict,
        "verdict_class": verdict_class,
        "top_priority": top_priority,
        "strengths": strengths,
        "growth_areas": growth_areas,
        "action_checklist": action_checklist,
        "phrasing_templates": phrasing_templates,
    }
