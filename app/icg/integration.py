"""
ICG <-> UniPlag integration layer (app/icg/integration.py)
=============================================================
Aris Directive (ICG live integration, v0.4):
  - Strict Fast/Slow path separation.
  - check_icg_fast(): main pipeline (fast deterministic contour, default).
  - check_icg_deep(): slow path (31b judges + Fact-Judge); for background/deep analysis only.
  - ICGHealth black-box is written by icg_watchdog.py.
"""
from typing import Dict, Any, Optional, Tuple
import json

from .graph_builder import ICGGraphBuilder


# Thresholds for ICG textual conclusions (no magic numbers in code).
T_HIGH_ICS = 0.60
T_MID_ICS = 0.30
T_LOW_SYNTHETIC = 0.20
T_HIGH_SYNTHETIC = 0.40
T_HIGH_EVIDENCE = 0.70
T_LOW_EVIDENCE = 0.40
T_HIGH_COHERENCE = 0.70
T_WARN_UNSUPPORTED = 0.30
T_WARN_CONTRADICTORY = 0.05
T_HIGH_ECC = 0.80


def build_icg_conclusions(summary: Dict[str, Any]) -> list[str]:
    """Textual ICG conclusions (выводы) for the unified UniPlag report.

    Converts raw graph metrics into a small, honest set of Russian-language verdicts:
    overall contribution, synthetic vs reproductive balance, evidence base, contradiction
    flags and the epistemic caveat (ECC). No numbers are invented — every statement is
    derived from the summary metrics.
    """
    s = summary
    def g(key: str, default: float = 0.0) -> float:
        v = s.get(key, default)
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    ics = g("intellectual_contribution_score")
    evidence = g("evidence_coverage")
    coherence = g("reasoning_coherence")
    novelty = g("novelty_score")
    synthesis = g("synthesis_ratio")
    higher = g("higher_order_synthesis_ratio")
    source_novel = g("source_novel_synthesis_ratio")
    inference = g("inference_ratio")
    reprod = g("reproduction_ratio")
    unsupported = g("unsupported_ratio")
    contradictory = g("contradictory_ratio")
    ecc = g("external_corpus_coverage")

    out: list[str] = []

    if ics >= T_HIGH_ICS:
        out.append(
            f"Интеллектуальный вклад высокий (ICS ≈ {ics:.2f}): авторское рассуждение "
            "преобладает над пересказом источников."
        )
    elif ics >= T_MID_ICS:
        out.append(
            f"Интеллектуальный вклад средний (ICS ≈ {ics:.2f}): самостоятельное рассуждение "
            "присутствует, но заметная доля текста опирается на воспроизведение источников."
        )
    else:
        out.append(
            f"Интеллектуальный вклад низкий (ICS ≈ {ics:.2f}): текст преимущественно "
            "воспроизводит известные положения, авторская обработка выражена слабо."
        )

    synthetic = synthesis + higher + source_novel
    if synthetic >= T_HIGH_SYNTHETIC:
        out.append(
            f"Высокий синтетический потенциал ({synthetic * 100:.0f}% операций мышления — "
            "синтез/вывод): автор соединяет источники в новые конструкции."
        )
    elif synthetic <= T_LOW_SYNTHETIC:
        out.append(
            f"Синтетический потенциал низкий ({synthetic * 100:.0f}%): оригинальные "
            "связки между источниками почти не встречаются, работа носит "
            "реферативно-воспроизводящий характер."
        )
    else:
        out.append(
            f"Синтетический потенциал умеренный ({synthetic * 100:.0f}%): отдельные "
            "авторские связки присутствуют наряду с воспроизведением."
        )

    if evidence >= T_HIGH_EVIDENCE:
        out.append(f"Доказательная база плотная: {evidence * 100:.0f}% утверждений опирается на источники или промежуточные выводы.")
    elif evidence <= T_LOW_EVIDENCE:
        out.append(f"Доказательная база разрежена ({evidence * 100:.0f}% по покрытию): значительная часть утверждений провисает без опоры.")

    if unsupported >= T_WARN_UNSUPPORTED:
        out.append(
            f"Предупреждение: {unsupported * 100:.0f}% утверждений не имеют обоснования "
            "источником или промежуточным выводом — зона риска необоснованности."
        )
    if contradictory >= T_WARN_CONTRADICTORY:
        out.append(
            f"Обнаружены противоречивые утверждения ({contradictory * 100:.1f}%): "
            "текст содержит внутренне конфликтующие тезисы, требующие авторской сверки."
        )

    if coherence >= T_HIGH_COHERENCE:
        out.append(f"Связность рассуждений высокая ({coherence * 100:.0f}%): логические цепочки выстраиваются в связный граф.")
    elif reprod > 0.6:
        out.append("Характер изложения преимущественно реферативный (воспроизведение источников без авторских переходов).")

    if evidence < T_LOW_EVIDENCE and cohort_novel(ics, novelty, synthetic):
        out.append("При низкой доказательной базе высокая оценка новизны не может быть принята без повышения покрытия источниками.")

    if ecc >= T_HIGH_ECC:
        out.append(f"Статус новизны: глобальный с высокой уверенностью корпуса (ECC ≈ {ecc:.2f}).")
    else:
        out.append(f"Статус новизны: относительно индексированного корпуса (ECC ≈ {ecc:.2f}); возможны неучтённые источники.")

    return out


def cohort_novel(ics: float, novelty: float, synthetic: float) -> bool:
    return novelty >= 0.5 and ics >= 0.5 and synthetic >= 0.3


def _build_graph_fast(document_id: str, text: str) -> Any:
    builder = ICGGraphBuilder()
    return builder.build_graph(document_id=document_id, text=text, use_llm=False)


def _build_graph_deep(document_id: str, text: str) -> Any:
    builder = ICGGraphBuilder()
    return builder.build_graph(document_id=document_id, text=text, use_llm=True)


def _summarize(graph: Any) -> Dict[str, Any]:
    m = graph.metrics_summary
    return {
        "intellectual_contribution_score": round(float(m.intellectual_contribution_score), 4),
        "reproduction_ratio": round(float(m.reproduction_ratio), 4),
        "synthesis_ratio": round(float(m.synthesis_ratio), 4),
        "source_novel_synthesis_ratio": round(float(m.source_novel_synthesis_ratio), 4),
        "higher_order_synthesis_ratio": round(float(m.higher_order_synthesis_ratio), 4),
        "original_contribution_ratio": round(float(m.original_contribution_ratio), 4),
        "inference_ratio": round(float(m.inference_ratio), 4),
        "unsupported_ratio": round(float(m.unsupported_ratio), 4),
        "contradictory_ratio": round(float(m.contradictory_ratio), 4),
        "novelty_score": round(float(m.novelty_score), 4),
        "synthesis_depth": round(float(m.synthesis_depth), 4),
        "inference_depth": round(float(m.inference_depth), 4),
        "evidence_coverage": round(float(m.evidence_coverage), 4),
        "reasoning_coherence": round(float(m.reasoning_coherence), 4),
        "external_corpus_coverage": round(float(m.external_corpus_coverage), 4),
        "global_epistemic_confidence": round(float(m.global_epistemic_confidence), 4),
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
    }


def check_icg_fast(document_id: str, text: str) -> Tuple[float, Dict[str, Any], str]:
    """Fast contour: returns (icg_score_0_100, summary_dict, json_payload)."""
    graph = _build_graph_fast(document_id, text)
    score = round(float(graph.metrics_summary.intellectual_contribution_score) * 100.0, 1)
    summary = _summarize(graph)
    payload = {
        "contour": "fast",
        "score": score,
        "summary": summary,
        "ratios": {
            "synthesis": summary["synthesis_ratio"] + summary["source_novel_synthesis_ratio"]
                       + summary["higher_order_synthesis_ratio"],
            "inference": summary["inference_ratio"],
            "unsupported": summary["unsupported_ratio"],
            "contradictory": summary["contradictory_ratio"],
            "reproduction": summary["reproduction_ratio"],
        },
    }
    # Aris Directive: keep the user-facing ICG section (report.html) working —
    # embed the full graph dump so `metrics_summary` / `nodes` remain available.
    try:
        dump = graph.model_dump()
        if isinstance(dump, dict):
            payload["metrics_summary"] = dump.get("metrics_summary", {})
            payload["nodes"] = dump.get("nodes", [])
    except Exception:
        pass
    # Текстовые выводы ICG для общего отчёта UniPlag.
    payload["conclusions"] = build_icg_conclusions(summary)
    return score, summary, json.dumps(payload, ensure_ascii=False)


def check_icg_deep(document_id: str, text: str) -> Tuple[float, Dict[str, Any], str]:
    """Slow path (31b judges + Fact-Judge). For background/deep analysis; NOT for HTTP request."""
    graph = _build_graph_deep(document_id, text)
    score = round(float(graph.metrics_summary.intellectual_contribution_score) * 100.0, 1)
    summary = _summarize(graph)
    payload = {
        "contour": "deep",
        "score": score,
        "summary": summary,
        "ratios": {
            "synthesis": summary["synthesis_ratio"] + summary["source_novel_synthesis_ratio"]
                       + summary["higher_order_synthesis_ratio"],
            "inference": summary["inference_ratio"],
            "unsupported": summary["unsupported_ratio"],
            "contradictory": summary["contradictory_ratio"],
            "reproduction": summary["reproduction_ratio"],
        },
    }
    try:
        dump = graph.model_dump()
        if isinstance(dump, dict):
            payload["metrics_summary"] = dump.get("metrics_summary", {})
            payload["nodes"] = dump.get("nodes", [])
    except Exception:
        pass
    payload["conclusions"] = build_icg_conclusions(summary)
    return score, summary, json.dumps(payload, ensure_ascii=False)
