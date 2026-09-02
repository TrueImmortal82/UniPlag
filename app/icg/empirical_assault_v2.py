"""
Директива №18: Empirical Assault — Карта Разрывов ICG v0.4
==========================================================
4 сценария стресс-тестирования:
  CASE_1: Синтетический коллапс — 50+ циклических противоречий
  CASE_2: Глубина инференса — 7-шаговая логическая цепочка
  CASE_3: Шумовой порог — 10% случайных утверждений
  CASE_4: Сквозной отчёт — карта разрывов
"""

import sys
sys.path.insert(0, r"E:\AI detector\uniplag")

from typing import Dict, Any
from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import (
    ClaimNode, ICGGraph, EdgeEvidence, EdgeStatus, RelationType,
    NodeType, TextSpan, ContributionClass,
)
from app.icg.discourse import split_sentences_with_spans


def _span(text: str) -> TextSpan:
    return TextSpan(start_char=0, end_char=len(text), raw_text=text)


def build_graph_from_text(text: str, doc_id: str = "test", use_llm: bool = False) -> ICGGraph:
    builder = ICGGraphBuilder()
    return builder.build_graph(document_id=doc_id, text=text, use_llm=use_llm)


# ─── CASE_1: Синтетический коллапс ─────────────────────────────────────────
def case_1_synthetic_collapse():
    print("=" * 70)
    print("CASE_1: СИНТЕТИЧЕСКИЙ КОЛЛАПС — 50+ циклических противоречий")
    print("=" * 70)

    claims = []
    n = 30
    for i in range(n):
        a = f"Утверждение A_{i}: Параметр X_{i} равен {100 + i} единицам и является определяющим для системы."
        b = f"Утверждение B_{i}: Параметр X_{i} равен {-100 - i} единицам и является определяющим для системы."
        claims.append(a)
        claims.append(b)

    for i in range(n - 1):
        claims.append(f"Циклическая связь C_{i}: Результат B_{i} опровергает A_{i+1}, но A_{i+1} подтверждает A_{i}.")

    claims.append(f"Замыкание: B_{n-1} опровергает A_0, создавая замкнутый цикл длины {n}.")

    text = "\n".join(claims)
    print(f"  Создано утверждений: {len(claims)}")

    graph = build_graph_from_text(text, "collapse_test")
    nodes = graph.nodes
    edges = graph.edges

    contradictory = [e for e in edges if e.status == EdgeStatus.CONFLICTING_EVIDENCE]
    unsupported = [n for n in nodes if n.contribution_class == ContributionClass.UNSUPPORTED]
    synthesis = [n for n in nodes if n.contribution_class in (
        ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS,
        ContributionClass.HIGHER_ORDER_SYNTHESIS
    )]
    conflicting_nodes = [n for n in nodes if n.contribution_class == ContributionClass.CONTRADICTORY]

    print(f"  Узлов в графе: {len(nodes)}")
    print(f"  Рёбер в графе: {len(edges)}")
    print(f"  CONFLICTING_EVIDENCE рёбер: {len(contradictory)}")
    print(f"  Узлов CONTRADICTORY: {len(conflicting_nodes)}")
    print(f"  Узлов UNSUPPORTED: {len(unsupported)}")
    print(f"  Узлов SYNTHESIS+: {len(synthesis)}")

    collapsed = len(synthesis) > n * 0.3
    print(f"\n  РЕЗУЛЬТАТ: {'ФАЛСИФИКАЦИЯ — система ушла в бесконечный синтез!' if collapsed else 'СТАБИЛЬНО — синтез не размножается'}")
    print(f"  Формула: {len(synthesis)} синтезов / {len(claims)} утверждений = {len(synthesis)/max(len(claims),1):.1%}")

    return {
        "total_claims": len(claims),
        "nodes": len(nodes),
        "edges": len(edges),
        "conflicting_edges": len(contradictory),
        "conflicting_nodes": len(conflicting_nodes),
        "unsupported": len(unsupported),
        "synthesis": len(synthesis),
        "collapsed": collapsed,
    }


# ─── CASE_2: Глубина инференса ─────────────────────────────────────────────
def case_2_inference_depth(use_llm: bool = True):
    print("\n" + "=" * 70)
    print("CASE_2: ГЛУБИНА ИНФЕРЕНСА — 7-шаговая логическая цепочка")
    print("=" * 70)

    chain = [
        "Исходный факт: Плотность воды при 4°C составляет 1000 кг/м³.",
        "Вывод 1: Следовательно, 1 литр воды весит ровно 1 кг при 4°C.",
        "Вывод 2: Значит, масса 5 литров воды при 4°C равна 5 кг.",
        "Вывод 3: Таким образом, гравитационная сила на 5 литрах воды составляет приблизительно 49 Н.",
        "Вывод 4: Отсюда следует, что давление на дно сосуда глубиной 0.5 м составит около 4900 Па.",
        "Вывод 5: Следовательно, скорость истечения через отверстие в дне будет примерно 3.13 м/с по формуле Торричелли.",
        "Вывод 6: Значит, время заполнения ведра объёмом 10 л через такое отверстие составит около 10 секунд.",
        "Вывод 7: Отсюда вытекает, что для заполнения бассейна объёмом 50 м³ потребуется около 14 часов непрерывной подачи.",
    ]

    text = "\n".join(chain)
    graph = build_graph_from_text(text, "inference_depth_test", use_llm=use_llm)

    nodes = graph.nodes
    print(f"  Узлов в графе: {len(nodes)}")

    inference = [n for n in nodes if n.contribution_class == ContributionClass.INFERENCE]
    unsupported = [n for n in nodes if n.contribution_class == ContributionClass.UNSUPPORTED]
    reproduction = [n for n in nodes if n.contribution_class == ContributionClass.REPRODUCTION]

    print(f"  INFERENCE: {len(inference)}")
    print(f"  UNSUPPORTED: {len(unsupported)}")
    print(f"  REPRODUCTION: {len(reproduction)}")

    expected_inference = 7
    fade_rate = 1 - (len(inference) / expected_inference) if expected_inference > 0 else 0

    print(f"\n  Ожидалось INFERENCE: {expected_inference}")
    print(f"  Получено INFERENCE: {len(inference)}")
    print(f"  Затухание: {fade_rate:.0%}")

    if fade_rate > 0.5:
        verdict = "КРИТИЧЕСКОЕ ЗАТУХАНИЕ — инференс не проходит глубже 3-4 шага"
    elif fade_rate > 0.2:
        verdict = "УМЕРЕННОЕ ЗАТУХАНИЕ — инференс частично теряет точность"
    else:
        verdict = "СТАБИЛЬНО — инференс проходит на полную глубину"

    print(f"  ВЕРДИКТ: {verdict}")

    return {
        "expected_inference": expected_inference,
        "actual_inference": len(inference),
        "unsupported": len(unsupported),
        "fade_rate": round(fade_rate, 3),
        "verdict": verdict,
    }


# ─── CASE_3: Шумовой порог ─────────────────────────────────────────────────
def case_3_noise_threshold():
    print("\n" + "=" * 70)
    print("CASE_3: ШУМОВОЙ ПОРОГ — 10% случайных утверждений")
    print("=" * 70)

    facts = [
        "Квантовая запутанность позволяет передавать корреляции мгновенно на любые расстояния.",
        "Теорема о неполных моделях Гёделя ограничивает формализуемые теории.",
        "Геном человека содержит около 3 миллиардов пар нуклеотидов.",
        "Законы Ньютона описывают движение тел с точностью до 0.01% на земных скоростях.",
        "Термодинамическая энтропия системы растёт в замкнутых процессах.",
        "Нейронные сети обучаются методом обратного распространения ошибки.",
        "Модель стандартная частиц включает 17 фундаментальных частиц.",
        "Закон Мура предсказывает удвоение числа транзисторов каждые 2 года.",
        "Скорость света в вакууме составляет 299 792 458 м/с.",
        "Алгоритм Дейкстры находит кратчайший путь в графах за O(V²).",
    ]

    noise = [
        "Семантическая согласованность является необходимым условием эпистемической целостности.",
        "Информационная энтропия в��аживает на когнитивную резонансность систем.",
        "Фрактальная размерность когнитивных структур определяется через хаусдорф-меру.",
        "Тавтологическое замыкание снижает аффективный коэффициент в Hochma-классах.",
        "Экзистенциальная дистилляция парадоксальна по своей природе и не поддаётся формализации.",
    ]

    all_claims = facts + noise
    import random
    random.seed(42)
    random.shuffle(all_claims)

    text = "\n".join(all_claims)
    graph = build_graph_from_text(text, "noise_test")

    nodes = graph.nodes
    unsupported = [n for n in nodes if n.contribution_class == ContributionClass.UNSUPPORTED]
    reproduction = [n for n in nodes if n.contribution_class == ContributionClass.REPRODUCTION]
    inference = [n for n in nodes if n.contribution_class == ContributionClass.INFERENCE]
    synthesis = [n for n in nodes if n.contribution_class in (
        ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS,
        ContributionClass.HIGHER_ORDER_SYNTHESIS
    )]

    print(f"  Вход: {len(facts)} фактов + {len(noise)} шума = {len(all_claims)} всего")
    print(f"  Узлов в графе: {len(nodes)}")
    print(f"  UNSUPPORTED (шум отсечён): {len(unsupported)}")
    print(f"  REPRODUCTION (факты): {len(reproduction)}")
    print(f"  INFERENCE: {len(inference)}")
    print(f"  SYNTHESIS+: {len(synthesis)}")

    noise_capture_rate = len(unsupported) / max(len(noise), 1)
    false_positive_rate = max(0, len(unsupported) - len(noise)) / max(len(facts), 1)

    print(f"\n  Отсечение шума: {noise_capture_rate:.0%} ({len(unsupported)}/{len(noise)})")
    print(f"  Ложные срабатывания: {false_positive_rate:.0%}")

    if noise_capture_rate < 0.4:
        verdict = "КРИТИЧЕСКОЕ — шум не фильтруется, система путает факты и тавтологии"
    elif false_positive_rate > 0.3:
        verdict = "ПРОБЛЕМА — фильтр слишком агрессивен, отсекает настоящие факты"
    else:
        verdict = "АДЕКВАТНО — шум фильтруется с приемлемой точностью"

    print(f"  ВЕРДИКТ: {verdict}")

    return {
        "facts": len(facts),
        "noise": len(noise),
        "unsupported": len(unsupported),
        "reproduction": len(reproduction),
        "noise_capture_rate": round(noise_capture_rate, 3),
        "false_positive_rate": round(false_positive_rate, 3),
        "verdict": verdict,
    }


# ─── CASE_4: 10-шаговая цепочка с разрывом на шаге 8 ───────────────────────
def case_4_break_detection(use_llm: bool = True):
    print("=" * 70)
    print("CASE_4: СКВОЗНОЙ ОТЧЁТ — 10-шаговая цепочка с разрывом на шаге 8")
    print("=" * 70)

    chain = [
        "Исходный факт: Плотность воды при 4 градусах составляет 1000 кг/м3.",
        "Следовательно, 1 литр воды весит ровно 1 кг при 4 градусах.",
        "Значит, масса 5 литров воды при 4 градусах равна 5 кг.",
        "Таким образом, гравитационная сила на 5 литрах воды составляет приблизительно 49 Н.",
        "Отсюда следует, что давление на дно сосуда глубиной 0.5 м составит около 4900 Па.",
        "Следовательно, скорость истечения через отверстие в дне будет примерно 3.13 м/с по формуле Торричелли.",
        "Значит, время заполнения ведра объёмом 10 л через такое отверстие составит около 10 секунд.",
        "Отсюда вытекает, что фрактальная размерность когнитивных структур определяется через хаусдорф-меру и 更热更热更热 (ОШИБКА).",
        "Следовательно, конвекция начнётся при достижении точки кипения воды при 100 градусах.",
        "Значит, для полного нагрева бассейна потребуется около 14 часов непрерывной работы.",
    ]

    text = "\n".join(chain)
    graph = build_graph_from_text(text, "break_detection_test", use_llm=use_llm)

    nodes = graph.nodes
    print(f"  Узлов в графе: {len(nodes)}")

    inference = [n for n in nodes if n.contribution_class == ContributionClass.INFERENCE]
    unsupported = [n for n in nodes if n.contribution_class == ContributionClass.UNSUPPORTED]
    reproduction = [n for n in nodes if n.contribution_class == ContributionClass.REPRODUCTION]
    contradictory = [n for n in nodes if n.contribution_class == ContributionClass.CONTRADICTORY]

    print(f"  INFERENCE: {len(inference)}")
    print(f"  UNSUPPORTED: {len(unsupported)}")
    print(f"  REPRODUCTION: {len(reproduction)}")
    print(f"  CONTRADICTORY: {len(contradictory)}")

    for n in nodes:
        print(f"    {n.id}: {n.contribution_class.value:20s} conf={n.confidence:.2f} | {n.span.raw_text[:60]}")

    break_node = None
    for n in nodes:
        if "ОШИБКА" in n.span.raw_text or "寿司" in n.span.raw_text or "更热更热" in n.span.raw_text:
            break_node = n
            break

    break_detected = False
    if break_node:
        if break_node.contribution_class in [ContributionClass.UNSUPPORTED, ContributionClass.CONTRADICTORY]:
            break_detected = True

    correct_inference_before_break = 0
    for n in nodes:
        if break_node and n.id >= break_node.id:
            break
        if n.contribution_class == ContributionClass.INFERENCE:
            correct_inference_before_break += 1

    print(f"\n  Обнаружен разрыв: {'ДА' if break_detected else 'НЕТ'}")
    print(f"  Правильных INFERENCE до разрыва: {correct_inference_before_break}/7")

    if break_detected and correct_inference_before_break >= 5:
        verdict = "ПРОЙДЕНО — разрыв обнаружен, инференс стабилен до точки разрыва"
    elif break_detected:
        verdict = "ЧАСТИЧНО — разрыв обнаружен, но инференс затухает до него"
    else:
        verdict = "ПРОВАЛЕНО — разрыв не обнаружен или система посыпалась"

    print(f"  ВЕРДИКТ: {verdict}")

    return {
        "break_detected": break_detected,
        "correct_inference_before_break": correct_inference_before_break,
        "verdict": verdict,
    }


# ─── WATCHDOG RUNNER (FAST contour, no LLM) ────────────────────────────────
def run_empirical_assault_fast(verbose: bool = False) -> Dict[str, Any]:
    """Runs all 4 Empirical Assault cases with LLM disabled (FAST watchdog contour).

    Returns a digest with explicit pass flags so the ICG watchdog can persist
    the cognitive-immunity state without flooding logs.
    """
    import io as _io
    from contextlib import redirect_stdout

    buf = _io.StringIO()
    with redirect_stdout(buf):
        r1 = case_1_synthetic_collapse()
        r2 = case_2_inference_depth(use_llm=False)
        r3 = case_3_noise_threshold()
        r4 = case_4_break_detection(use_llm=False)

    c1_pass = not bool(r1["collapsed"])
    c2_pass = float(r2["fade_rate"]) <= 0.5
    c3_pass = float(r3["noise_capture_rate"]) >= 0.4 and float(r3["false_positive_rate"]) <= 0.3
    c4_pass = bool(r4["break_detected"]) and int(r4["correct_inference_before_break"]) >= 5

    passed = sum([c1_pass, c2_pass, c3_pass, c4_pass])
    return {
        "total": 4,
        "passed": passed,
        "pass_rate": round(passed / 4, 3),
        "cases": {
            "CASE_1_synthetic_collapse": {"pass": c1_pass, "collapsed": bool(r1["collapsed"]), "synthesis": r1["synthesis"]},
            "CASE_2_inference_depth": {"pass": c2_pass, "fade_rate": r2["fade_rate"]},
            "CASE_3_noise_threshold": {"pass": c3_pass, "noise_capture": r3["noise_capture_rate"], "false_pos": r3["false_positive_rate"]},
            "CASE_4_break_detection": {"pass": c4_pass, "break_detected": bool(r4["break_detected"]), "inference_before": r4["correct_inference_before_break"]},
        },
        "verdicts": {"c1": r1, "c2": r2, "c3": r3, "c4": r4},
    }


# ─── MAIN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   ДИРЕКТИВА №18: EMPIRICAL ASSAULT — КАРТА РАЗРЫВОВ ICG v0.4")
    print("=" * 70 + "\n")

    r1 = case_1_synthetic_collapse()
    r2 = case_2_inference_depth()
    r3 = case_3_noise_threshold()
    r4 = case_4_break_detection()
    print("\n" + "=" * 70)
    print("   СВОДНАЯ КАРТА РАЗРЫВОВ")
    print("=" * 70)

    breaks = []
    if r1["collapsed"]:
        breaks.append("CASE_1: Система уходит в бесконечный синтез при циклических противоречиях")
    if r2["fade_rate"] > 0.5:
        breaks.append(f"CASE_2: Инференс затухает на глубине {r2['fade_rate']:.0%}")
    if r3["noise_capture_rate"] < 0.4:
        breaks.append(f"CASE_3: Шум не фильтруется (отсечение {r3['noise_capture_rate']:.0%})")
    if r3["false_positive_rate"] > 0.3:
        breaks.append(f"CASE_3: Ложные срабатывания {r3['false_positive_rate']:.0%}")
    if not r4["break_detected"]:
        breaks.append(f"CASE_4: Разрыв в цепочке не обнаружен")

    if breaks:
        print("\n  ОБНАРУЖЕННЫЕ РАЗРЫВЫ:")
        for i, b in enumerate(breaks, 1):
            print(f"    {i}. {b}")
    else:
        print("\n  РАЗРЫВОВ НЕ ОБНАРУЖЕНО — система устойчива ко всем 4 сценариям")

    print(f"\n  CASE_1 collapse={r1['collapsed']}")
    print(f"  CASE_2 fade={r2['fade_rate']:.0%}")
    print(f"  CASE_3 noise_capture={r3['noise_capture_rate']:.0%} false_pos={r3['false_positive_rate']:.0%}")
    print(f"  CASE_4 break_detected={r4['break_detected']} correct_before={r4['correct_inference_before_break']}/7")
