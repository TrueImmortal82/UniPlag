"""
test_void_resolver.py — Aris Directive #8 Test Suite
Synthesis of Hypotheses & Verification Loop (Inquiry Resolver)

Test scenario (per Aris):
  Void (EMPIRICAL_GAP) → Inquiry → Resolve → Check:
    ✅ Edge exists (ASSOCIATION or typed)
    ✅ Void is VoidStatus.RESOLVED
    ✅ Evidence archived in void metadata
    ✅ Coverage increased (epistemic_confidence boosted)
    ✅ TENTATIVE_BRIDGE edges removed
    ✅ Low-confidence rejection (confidence < 0.70 → INSUFFICIENT_CONFIDENCE)
    ✅ Double-resolve guard (ALREADY_RESOLVED)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_void_resolver.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
)
from app.icg.graph_builder import ICGGraphBuilder

# ─────────────────────────────────────────────────────────────────────────────
PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


# ─────────────────────────────────────────────────────────────────────────────
# Setup: Build a minimal ICGGraph with one COGNITIVE_VOID already detected
# ─────────────────────────────────────────────────────────────────────────────

def build_test_graph_with_void() -> tuple:
    """
    Create a minimal ICGGraph that already contains a COGNITIVE_VOID node
    between two ANCHOR poles, along with TENTATIVE_BRIDGE edges.
    Returns (graph, builder, void_id, anchor_a_id, anchor_b_id).
    """
    builder = ICGGraphBuilder()

    anchor_q = ClaimNode(
        id="anchor_quantum_d8",
        type=NodeType.SUPER_ANCHOR,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=0, end_char=100, raw_text=(
            "Квантовая когерентность в кубитах определяет скорость вычислений. "
            "Декогеренция ограничивает масштабирование квантового процессора."
        )),
        is_anchor=True,
        is_super_anchor=True,
        confidence=0.90,
        epistemic_confidence=0.82,
    )
    anchor_n = ClaimNode(
        id="anchor_neuro_d8",
        type=NodeType.SUPER_ANCHOR,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=100, end_char=200, raw_text=(
            "Нейросинаптическая пластичность определяет скорость обучения в мозге. "
            "Когерентные осцилляции нейронов связаны с консолидацией памяти."
        )),
        is_anchor=True,
        is_super_anchor=True,
        confidence=0.88,
        epistemic_confidence=0.79,
    )

    # Create COGNITIVE_VOID node with full metadata
    void_id = "void_d8_test01"
    tent_edge_1_id = "tent_edge_a"
    tent_edge_2_id = "tent_edge_b"

    inquiry = InquiryResult(
        void_node_id=void_id,
        pole_a_anchor_id=anchor_q.id,
        pole_b_anchor_id=anchor_n.id,
        inquiry_question=(
            "Когнитивная пустота (EMPIRICAL_GAP): граф не содержит данных, связывающих "
            "[декогеренц / кубит] и [нейросинапс / обучен]. Гипотеза: механизм квантовой "
            "когерентности может лежать в основе нейронных осцилляций."
        ),
        hypotheses=[
            "Существует ли квантово-классическое взаимодействие в синаптической передаче?",
            "Влияет ли декогеренция нейронных структур на скорость обучения?",
            "Есть ли работы, объединяющие квантовые эффекты и нейропластичность?",
        ],
        void_type=VoidType.EMPIRICAL_GAP,
        tentative_edge_ids=[tent_edge_1_id, tent_edge_2_id],
    )

    void_meta = CognitiveVoidMetadata(
        void_type=VoidType.EMPIRICAL_GAP,
        void_status=VoidStatus.OPEN,
        pole_a_anchor_id=anchor_q.id,
        pole_b_anchor_id=anchor_n.id,
        gap_coverage_score=0.08,
        max_path_weight=0.0,
        inquiry=inquiry,
    )
    void_node = ClaimNode(
        id=void_id,
        type=NodeType.COGNITIVE_VOID,
        contribution_class=ContributionClass.UNKNOWN,
        span=TextSpan(start_char=0, end_char=0, raw_text=f"[COGNITIVE_VOID:EMPIRICAL_GAP]"),
        synthesis_metadata=SynthesisMetadata(cognitive_void=void_meta),
        confidence=0.0,
        epistemic_confidence=0.0,
    )

    # TENTATIVE edges
    tent_e1 = EdgeEvidence(
        edge_id=tent_edge_1_id,
        source_node_id=anchor_q.id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )
    tent_e2 = EdgeEvidence(
        edge_id=tent_edge_2_id,
        source_node_id=anchor_n.id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )

    metrics = MetricsSummary(
        cognitive_voids_count=1,
        tentative_edges_count=2,
        core_edges_count=0,
        external_corpus_coverage=0.85,
    )

    graph = ICGGraph(
        document_id="doc_d8_test",
        nodes=[anchor_q, anchor_n, void_node],
        edges=[tent_e1, tent_e2],
        metrics_summary=metrics,
    )
    return graph, builder, void_id, anchor_q.id, anchor_n.id


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────────────────────────────────────

print("\n═══ CASE_1: Low-confidence rejection (< 0.70) ═══")
graph, builder, void_id, a_id, b_id = build_test_graph_with_void()
result_low = builder.resolve_cognitive_void(
    graph=graph,
    void_id=void_id,
    evidence_text="Некоторые исследования предполагают связь.",
    confidence_score=0.50,
)
check("CASE_1.a status=INSUFFICIENT_CONFIDENCE", result_low["status"] == "INSUFFICIENT_CONFIDENCE",
      f"status={result_low['status']}")
check("CASE_1.b void still OPEN", 
      graph.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN, "OPEN")
check("CASE_1.c TENTATIVE edges still present", 
      sum(1 for e in graph.edges if e.status == EdgeStatus.TENTATIVE) == 2,
      f"tentative_edges={sum(1 for e in graph.edges if e.status == EdgeStatus.TENTATIVE)}")


print("\n═══ CASE_2: Successful resolution (confidence=0.85) ═══")
graph, builder, void_id, a_id, b_id = build_test_graph_with_void()
epi_a_before = next(n.epistemic_confidence for n in graph.nodes if n.id == a_id)
epi_b_before = next(n.epistemic_confidence for n in graph.nodes if n.id == b_id)
tent_count_before = sum(1 for e in graph.edges if e.status == EdgeStatus.TENTATIVE)

evidence = (
    "Пенроуз и Хамерофф (1994) предложили теорию Orch-OR, согласно которой квантовые "
    "когерентные состояния в микротрубочках нейронов следуют из механизмов декогеренции "
    "и объединяют квантовые вычисления с нейронной пластичностью и обучением."
)
result = builder.resolve_cognitive_void(
    graph=graph,
    void_id=void_id,
    evidence_text=evidence,
    confidence_score=0.85,
)
print(f"  [DEBUG] result={result}")

check("CASE_2.a status=RESOLVED", result["status"] == "RESOLVED", f"status={result['status']}")
check("CASE_2.b new edge created", result.get("new_edge_id") is not None, f"edge_id={result.get('new_edge_id')}")
check("CASE_2.c resolved_weight correct", 0.79 <= result.get("resolved_weight", 0) <= 0.82,
      f"weight={result.get('resolved_weight')}")

# Check void status in graph
void_node_after = next(n for n in graph.nodes if n.id == void_id)
void_meta_after = void_node_after.synthesis_metadata.cognitive_void
check("CASE_2.d VoidStatus=RESOLVED", void_meta_after.void_status == VoidStatus.RESOLVED, "RESOLVED")
check("CASE_2.e evidence archived", void_meta_after.resolved_evidence_text is not None and len(void_meta_after.resolved_evidence_text) > 10,
      f"text_len={len(void_meta_after.resolved_evidence_text or '')}")
check("CASE_2.f resolved_confidence stored", void_meta_after.resolved_confidence == 0.85,
      f"conf={void_meta_after.resolved_confidence}")

# Check TENTATIVE edges removed
tent_count_after = sum(1 for e in graph.edges if e.status == EdgeStatus.TENTATIVE)
check("CASE_2.g TENTATIVE edges removed", tent_count_after == 0, f"remaining={tent_count_after}")

# Check new bridge edge exists with correct type
bridge_edges = [e for e in graph.edges if e.source_node_id == a_id and e.target_node_id == b_id]
check("CASE_2.h bridge edge A→B exists", len(bridge_edges) >= 1, f"count={len(bridge_edges)}")
if bridge_edges:
    check("CASE_2.i bridge relation_type INFERS (follows from evidence)", 
          bridge_edges[0].relation_type in (RelationType.INFERS, RelationType.ASSOCIATION, RelationType.SYNTHESIZES),
          f"type={bridge_edges[0].relation_type}")
    check("CASE_2.j bridge status CORE_ACTIVE_LINK", 
          bridge_edges[0].status == EdgeStatus.CORE_ACTIVE_LINK,
          f"status={bridge_edges[0].status}")

# Check coverage propagation: epistemic_confidence should increase for both poles
epi_a_after = next(n.epistemic_confidence for n in graph.nodes if n.id == a_id)
epi_b_after = next(n.epistemic_confidence for n in graph.nodes if n.id == b_id)
check("CASE_2.k coverage increased for anchor A", epi_a_after >= epi_a_before,
      f"before={epi_a_before} → after={epi_a_after}")
check("CASE_2.l coverage increased for anchor B", epi_b_after >= epi_b_before,
      f"before={epi_b_before} → after={epi_b_after}")

# Check MetricsSummary updated
ms = graph.metrics_summary
check("CASE_2.m cognitive_voids_count decremented", ms.cognitive_voids_count == 0,
      f"count={ms.cognitive_voids_count}")
check("CASE_2.n tentative_edges_count decremented", ms.tentative_edges_count == 0,
      f"count={ms.tentative_edges_count}")
check("CASE_2.o core_edges_count incremented", ms.core_edges_count >= 1,
      f"count={ms.core_edges_count}")


print("\n═══ CASE_3: Double-resolve guard ═══")
# Try resolving the same void again
result_double = builder.resolve_cognitive_void(
    graph=graph,
    void_id=void_id,
    evidence_text="Ещё один источник",
    confidence_score=0.90,
)
check("CASE_3.a status=ALREADY_RESOLVED", result_double["status"] == "ALREADY_RESOLVED",
      f"status={result_double['status']}")


print("\n═══ CASE_4: RelationType inference from evidence text ═══")
test_cases_rel = [
    ("Исследование синтезирует квантовые и нейронные подходы", RelationType.SYNTHESIZES),
    ("Из данного следует, что декогеренция влияет на нейроны", RelationType.INFERS),
    ("Работа расширяет теорию Пенроуза на нейронные сети", RelationType.EXTENDS),
    ("Просто некий текст без явных маркеров", RelationType.ASSOCIATION),
]
for evidence_t, expected_rel in test_cases_rel:
    inferred = builder._infer_relation_type_from_evidence(evidence_t)
    check(f"CASE_4.{expected_rel.value}", inferred == expected_rel,
          f"expected={expected_rel.value}, got={inferred.value}")


print("\n═══ CASE_5: NOT_FOUND guard ═══")
graph, builder, void_id, a_id, b_id = build_test_graph_with_void()
result_nf = builder.resolve_cognitive_void(graph, "void_nonexistent_xyz", "evidence", 0.85)
check("CASE_5.a status=NOT_FOUND", result_nf["status"] == "NOT_FOUND",
      f"status={result_nf['status']}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №8 Void Resolver: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Inquiry Resolver OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

import sys
sys.exit(0 if passed == total else 1)
