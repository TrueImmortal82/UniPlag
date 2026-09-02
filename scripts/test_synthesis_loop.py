"""
test_synthesis_loop.py — Aris Directive #10 Test Suite
Epistemic Synthesis Loop & Verification Engine

Test Cases:
  CASE_1: Verified Proposal (Full loop: Inquiry -> Proposal -> Dual-Pole NLI -> Verified -> Bridge Edge -> Tension update)
  CASE_2: Adversarial Knowledge Conflict (Contradictory evidence -> CONFLICT status + ConflictDetail + Strategy + CONTRADICTORY_SILENCE)
  CASE_3: Blind Spot Defense (Neutral noise text -> REJECTED_UNSUPPORTED, void not resolved)
  CASE_4: Low-Confidence Rejection (< 0.70 -> REJECTED_UNSUPPORTED)
  CASE_5: Proposal Audit Trail (Multiple proposals logged in proposals_history)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_synthesis_loop.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    ResolutionStatus, ConflictResolutionStrategy,
)
from app.icg.synthesis_loop import SynthesisLoopEngine
from app.icg.epistemic_heatmap import calculate_void_tension, get_top_priority_voids

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_anchor(node_id: str, text: str, conf: float = 0.90, epi_conf: float = 0.85) -> ClaimNode:
    return ClaimNode(
        id=node_id,
        type=NodeType.SUPER_ANCHOR,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
        is_anchor=True,
        is_super_anchor=True,
        confidence=conf,
        epistemic_confidence=epi_conf,
    )


def build_test_scenario() -> tuple:
    """
    Sets up a graph with two poles:
      Pole A: Accelerating quantum computing via coherence preservation
      Pole B: Neural synaptic learning in biological cortical networks
    and an OPEN COGNITIVE_VOID between them.
    """
    pole_a = make_anchor(
        "anchor_quantum",
        "Квантовая когерентность в кубитах ускоряет вычисления и масштабирует квантовые системы.",
        conf=0.92,
        epi_conf=0.86
    )
    pole_b = make_anchor(
        "anchor_neuro",
        "Синаптическая пластичность в нейронах обеспечивает обучение и консолидацию памяти в коре мозга.",
        conf=0.90,
        epi_conf=0.84
    )

    void_id = "void_q_neuro"
    inquiry = InquiryResult(
        void_node_id=void_id,
        pole_a_anchor_id=pole_a.id,
        pole_b_anchor_id=pole_b.id,
        inquiry_question="Как квантовая когерентность связана с синаптической пластичностью?",
        hypotheses=["Квантовые эффекты в микротрубочках", "Ионные каналы как кубиты"],
        void_type=VoidType.EMPIRICAL_GAP,
        tentative_edge_ids=["tent_1", "tent_2"],
    )

    meta = CognitiveVoidMetadata(
        void_type=VoidType.EMPIRICAL_GAP,
        void_status=VoidStatus.OPEN,
        pole_a_anchor_id=pole_a.id,
        pole_b_anchor_id=pole_b.id,
        gap_coverage_score=0.10,
        max_path_weight=0.0,
        inquiry=inquiry,
    )

    void_node = ClaimNode(
        id=void_id,
        type=NodeType.COGNITIVE_VOID,
        contribution_class=ContributionClass.UNKNOWN,
        span=TextSpan(start_char=0, end_char=0, raw_text="[COGNITIVE_VOID:EMPIRICAL_GAP]"),
        synthesis_metadata=SynthesisMetadata(cognitive_void=meta),
        confidence=0.0,
        epistemic_confidence=0.0,
    )

    t1 = EdgeEvidence(
        edge_id="tent_1",
        source_node_id=pole_a.id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )
    t2 = EdgeEvidence(
        edge_id="tent_2",
        source_node_id=pole_b.id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )

    graph = ICGGraph(
        document_id="doc_d10",
        nodes=[pole_a, pole_b, void_node],
        edges=[t1, t2],
        metrics_summary=MetricsSummary(
            cognitive_voids_count=1,
            tentative_edges_count=2,
            external_corpus_coverage=0.85
        )
    )

    engine = SynthesisLoopEngine()
    return graph, engine, void_id, pole_a.id, pole_b.id


# =========================================================================
# CASE 1: Verified Synthesis Loop (Valid Bridging Evidence)
# =========================================================================
print("\n═══ CASE 1: Verified Synthesis Loop ═══")
graph1, engine1, void_id1, a_id, b_id = build_test_scenario()

valid_evidence = (
    "Исследование объединяет принципы: квантовая когерентность в ионных каналах "
    "кубитов синапсов ускоряет синаптическую пластичность нейронов мозга."
)

prop1 = engine1.propose_void_resolution(
    graph=graph1,
    void_id=void_id1,
    evidence_text=valid_evidence,
    evidence_source="Nature Quantum Biology 2026",
    confidence_score=0.90,
)

print(f"  [DEBUG] Proposal Status: {prop1.status}, Entail_A={prop1.pole_a_entailment}, Entail_B={prop1.pole_b_entailment}")

check("CASE_1.a status is VERIFIED", prop1.status == ResolutionStatus.VERIFIED, f"status={prop1.status}")
check("CASE_1.b created_edge_id assigned", prop1.created_edge_id is not None, f"edge_id={prop1.created_edge_id}")
check("CASE_1.c VoidStatus in graph is RESOLVED", 
      graph1.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.RESOLVED, "RESOLVED")
check("CASE_1.d Core edge created between poles", 
      any(e.source_node_id == a_id and e.target_node_id == b_id and e.status == EdgeStatus.CORE_ACTIVE_LINK for e in graph1.edges),
      "Core edge exists")
check("CASE_1.e TENTATIVE edges removed",
      sum(1 for e in graph1.edges if e.status == EdgeStatus.TENTATIVE) == 0, "0 tentative")


# =========================================================================
# CASE 2: Adversarial Knowledge Conflict ("Конфликт знаний")
# =========================================================================
print("\n═══ CASE 2: Adversarial Knowledge Conflict ═══")
graph2, engine2, void_id2, a_id2, b_id2 = build_test_scenario()

# Conflicting evidence directly contradicts Pole A ("квантовая когерентность НЕвозможна")
adversarial_evidence = (
    "Эксперименты опровергают: квантовая когерентность в биологических системах "
    "невозможна и полностью исключена из-за тепловой декогеренции."
)

prop2 = engine2.propose_void_resolution(
    graph=graph2,
    void_id=void_id2,
    evidence_text=adversarial_evidence,
    evidence_source="Adversarial Paper 2026",
    confidence_score=0.90,
)

print(f"  [DEBUG] Conflict Status: {prop2.status}, Contra_A={prop2.pole_a_contradiction}, Details={prop2.conflict_details}")

check("CASE_2.a status is CONFLICT", prop2.status == ResolutionStatus.CONFLICT, f"status={prop2.status}")
check("CASE_2.b structured ConflictDetail exists", prop2.conflict_details is not None, "ConflictDetail present")
if prop2.conflict_details:
    check("CASE_2.c Conflicting pole correctly identified as Pole A", prop2.conflict_details.pole_label == "A",
          f"label={prop2.conflict_details.pole_label}")
    check("CASE_2.d Contradiction score tracked", prop2.conflict_details.contradiction_score >= 0.50,
          f"score={prop2.conflict_details.contradiction_score}")
check("CASE_2.e Conflict resolution strategy assigned", 
      prop2.conflict_strategy in (ConflictResolutionStrategy.TRIANGULATE_THIRD_POLE, ConflictResolutionStrategy.ARBITRATE_EXTERNAL_SOURCE, ConflictResolutionStrategy.REVISE_POLES),
      f"strategy={prop2.conflict_strategy}")
check("CASE_2.f Void remained OPEN (not falsely closed)",
      graph2.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN, "OPEN")
check("CASE_2.g VoidType escalated to CONTRADICTORY_SILENCE",
      graph2.nodes[2].synthesis_metadata.cognitive_void.void_type == VoidType.CONTRADICTORY_SILENCE,
      f"type={graph2.nodes[2].synthesis_metadata.cognitive_void.void_type}")


# =========================================================================
# CASE 3: Blind Spot Defense (Neutral Noise Text)
# =========================================================================
print("\n═══ CASE 3: Blind Spot Defense (Anti-Noise) ═══")
graph3, engine3, void_id3, a_id3, b_id3 = build_test_scenario()

neutral_noise = "Погода в горах меняется каждые три часа из-за атмосферного давления."

prop3 = engine3.propose_void_resolution(
    graph=graph3,
    void_id=void_id3,
    evidence_text=neutral_noise,
    confidence_score=0.90,
)

print(f"  [DEBUG] Noise Status: {prop3.status}, Entail_A={prop3.pole_a_entailment}, Entail_B={prop3.pole_b_entailment}")

check("CASE_3.a Neutral noise REJECTED_UNSUPPORTED", prop3.status == ResolutionStatus.REJECTED_UNSUPPORTED,
      f"status={prop3.status}")
check("CASE_3.b Void NOT resolved by silence",
      graph3.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN, "OPEN")


# =========================================================================
# CASE 4: Low-Confidence Rejection (< 0.70)
# =========================================================================
print("\n═══ CASE 4: Low-Confidence Rejection ═══")
graph4, engine4, void_id4, a_id4, b_id4 = build_test_scenario()

prop4 = engine4.propose_void_resolution(
    graph=graph4,
    void_id=void_id4,
    evidence_text=valid_evidence,
    confidence_score=0.45,  # Low confidence
)

check("CASE_4.a Low confidence rejected", prop4.status == ResolutionStatus.REJECTED_UNSUPPORTED,
      f"status={prop4.status}")
check("CASE_4.b Void remained OPEN",
      graph4.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN, "OPEN")


# =========================================================================
# CASE 5: Proposal Audit Trail in proposals_history
# =========================================================================
print("\n═══ CASE 5: Proposal Audit Trail ═══")
graph5, engine5, void_id5, a_id5, b_id5 = build_test_scenario()

# Attempt 1: Noise (Rejected)
engine5.propose_void_resolution(graph5, void_id5, neutral_noise, confidence_score=0.90)
# Attempt 2: Conflict (Conflict)
engine5.propose_void_resolution(graph5, void_id5, adversarial_evidence, confidence_score=0.90)
# Attempt 3: Valid (Verified)
engine5.propose_void_resolution(graph5, void_id5, valid_evidence, confidence_score=0.90)

history = graph5.nodes[2].synthesis_metadata.cognitive_void.proposals_history
check("CASE_5.a Exactly 3 proposals in history", len(history) == 3, f"count={len(history)}")
check("CASE_5.b Attempt 1 recorded as REJECTED_UNSUPPORTED", history[0].status == ResolutionStatus.REJECTED_UNSUPPORTED, f"s1={history[0].status}")
check("CASE_5.c Attempt 2 recorded as CONFLICT", history[1].status == ResolutionStatus.CONFLICT, f"s2={history[1].status}")
check("CASE_5.d Attempt 3 recorded as VERIFIED", history[2].status == ResolutionStatus.VERIFIED, f"s3={history[2].status}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №10 Synthesis Loop: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Epistemic Synthesis Loop OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
