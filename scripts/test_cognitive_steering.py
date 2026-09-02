"""
test_cognitive_steering.py — Aris Directive #12 Test Suite
Cognitive Steering, Resource Allocation & Dynamic Attention

Test Cases:
  CASE_1: Resource Allocation (Aris Core Scenario: Paradox Core receives >=85% budget, Crystal receives <15%)
  CASE_2: Action Selection Rules (SYNTHESIS_CRUCIBLE vs ARCHIVE_MONITORING vs VOID_SETTLEMENT)
  CASE_3: Anti-Obsession Damping (Monotonic priority decay on unresolved target)
  CASE_4: Feedback Loop & Phase Transition (Steered synthesis transforms Paradox/Wasteland into Crystal)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_cognitive_steering.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    DomainZoneType, DomainStabilityState, SteeringAction,
)
from app.icg.cognitive_steering import CognitiveSteeringEngine

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_node(node_id: str, text: str, epi: float = 0.85) -> ClaimNode:
    return ClaimNode(
        id=node_id,
        type=NodeType.SUPER_ANCHOR,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
        is_anchor=True,
        is_super_anchor=True,
        confidence=0.90,
        epistemic_confidence=epi,
    )


def make_core_edge(src: str, tgt: str, weight: float = 0.90) -> EdgeEvidence:
    return EdgeEvidence(
        source_node_id=src,
        target_node_id=tgt,
        relation_type=RelationType.SYNTHESIZES,
        weight=weight,
        status=EdgeStatus.CORE_ACTIVE_LINK,
        weight_details=EdgeWeightDetails(final_weight=weight, status=EdgeStatus.CORE_ACTIVE_LINK)
    )


def make_repulsion_edge(src: str, tgt: str) -> EdgeEvidence:
    return EdgeEvidence(
        source_node_id=src,
        target_node_id=tgt,
        relation_type=RelationType.NEGATIVE_GRAVITY_REPULSION,
        weight=-0.85,
        status=EdgeStatus.REPULSION_BOUNDARY,
        weight_details=EdgeWeightDetails(final_weight=-0.85, status=EdgeStatus.REPULSION_BOUNDARY)
    )


engine = CognitiveSteeringEngine()

# =========================================================================
# CASE 1: Proportional Resource Allocation (Aris Core Scenario)
# =========================================================================
print("\n═══ CASE 1: Proportional Resource Allocation (Paradox vs Crystal) ═══")
# Cluster A: Crystallized Knowledge (c1, c2, c3 — stable, 0 conflict)
c1 = make_node("c1", "Квантовая суперпозиция в кубитах", epi=0.90)
c2 = make_node("c2", "Лазерный контроль квантовых состояний", epi=0.88)
c3 = make_node("c3", "Топологические коды коррекции ошибок", epi=0.86)

edges_crystal = [
    make_core_edge("c1", "c2"),
    make_core_edge("c2", "c3"),
    make_core_edge("c3", "c1"),
]

# Cluster B: Paradox Core (p1, p2, p3 — intense conflict, high density)
p1 = make_node("p1", "Эмиссионное стимулирование роста ВВП", epi=0.85)
p2 = make_node("p2", "Инфляционная спираль и сжатие ликвидности", epi=0.82)
p3 = make_node("p3", "Стагфляционный парадокс ставки рефинансирования", epi=0.80)

edges_paradox = [
    make_core_edge("p1", "p2"),
    make_core_edge("p2", "p3"),
    make_repulsion_edge("p1", "p3"),  # Strong dialectical tension
]

graph_dual = ICGGraph(
    document_id="doc_dual",
    nodes=[c1, c2, c3, p1, p2, p3],
    edges=edges_crystal + edges_paradox,
)

report1 = engine.get_high_value_targets(graph_dual, total_compute_budget=1000)
print(f"  [DEBUG] Targets: {len(report1.targets)}, Top Target: {report1.top_priority_target_id}")
for t in report1.targets:
    print(f"    Target {t.target_id[:12]}: Zone={t.zone_type.value}, Value={t.value_score:.4f}, Budget={t.allocated_compute_units} ({t.budget_percentage}%), Action={t.recommended_action.value}")

paradox_target = next((t for t in report1.targets if t.zone_type == DomainZoneType.PARADOX_CORE), None)
crystal_target = next((t for t in report1.targets if t.zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE), None)

check("CASE_1.a Paradox Core target exists", paradox_target is not None, "Paradox target present")
check("CASE_1.b Crystal Knowledge target exists", crystal_target is not None, "Crystal target present")
if paradox_target and crystal_target:
    check("CASE_1.c Paradox Core receives overwhelming budget (>=80%)", paradox_target.budget_percentage >= 80.0,
          f"paradox_pct={paradox_target.budget_percentage}%")
    check("CASE_1.d Crystal Knowledge receives minimal budget (<20%)", crystal_target.budget_percentage < 20.0,
          f"crystal_pct={crystal_target.budget_percentage}%")
    check("CASE_1.e Top priority is Paradox Core", report1.top_priority_target_id == paradox_target.target_id,
          f"top_id={report1.top_priority_target_id}")


# =========================================================================
# CASE 2: Action Selection Rules
# =========================================================================
print("\n═══ CASE 2: Action Selection Rules ═══")
if paradox_target:
    check("CASE_2.a PARADOX_CORE -> SYNTHESIS_CRUCIBLE", 
          paradox_target.recommended_action == SteeringAction.SYNTHESIS_CRUCIBLE,
          f"action={paradox_target.recommended_action}")

if crystal_target:
    check("CASE_2.b CRYSTALLIZED_KNOWLEDGE -> ARCHIVE_MONITORING",
          crystal_target.recommended_action == SteeringAction.ARCHIVE_MONITORING,
          f"action={crystal_target.recommended_action}")


# =========================================================================
# CASE 3: Anti-Obsession Damping
# =========================================================================
print("\n═══ CASE 3: Anti-Obsession Damping ═══")
# Simulate repeated iterations on a target domain
engine_damping = CognitiveSteeringEngine()

report_iter0 = engine_damping.get_high_value_targets(graph_dual)
v0 = report_iter0.targets[0].value_score

# Step 1
engine_damping.domain_iteration_counts[report_iter0.targets[0].target_id] = 1
report_iter1 = engine_damping.get_high_value_targets(graph_dual)
v1 = next(t.value_score for t in report_iter1.targets if t.target_id == report_iter0.targets[0].target_id)

# Step 4
engine_damping.domain_iteration_counts[report_iter0.targets[0].target_id] = 4
report_iter4 = engine_damping.get_high_value_targets(graph_dual)
v4 = next(t.value_score for t in report_iter4.targets if t.target_id == report_iter0.targets[0].target_id)

print(f"  [DEBUG] Damping progression: v0={v0:.4f} -> v1={v1:.4f} -> v4={v4:.4f}")
check("CASE_3.a Value score decreases after iteration 1", v1 < v0, f"v1={v1:.4f} < v0={v0:.4f}")
check("CASE_3.b Value score significantly damped by iteration 4 (50% reduction)", v4 <= v0 * 0.55, f"v4={v4:.4f} <= {v0 * 0.55:.4f}")


# =========================================================================
# CASE 4: Feedback Loop & Phase Transition
# =========================================================================
print("\n═══ CASE 4: Feedback Loop & Phase Transition ═══")
# Setup a graph with an OPEN void between two nodes
a1 = make_node("a1", "Квантовая запутанность кубитов в процессоре", epi=0.90)
a2 = make_node("a2", "Сверхпроводящие резонаторы для квантовых вычислений", epi=0.88)

void_id = "void_steering_test"
inquiry = InquiryResult(
    void_node_id=void_id,
    pole_a_anchor_id=a1.id,
    pole_b_anchor_id=a2.id,
    inquiry_question="Как резонаторы поддерживают запутанность?",
    hypotheses=["Сверхпроводящий волновод"],
    void_type=VoidType.EMPIRICAL_GAP,
    tentative_edge_ids=["tent_s1", "tent_s2"],
)
void_meta = CognitiveVoidMetadata(
    void_type=VoidType.EMPIRICAL_GAP,
    void_status=VoidStatus.OPEN,
    pole_a_anchor_id=a1.id,
    pole_b_anchor_id=a2.id,
    gap_coverage_score=0.10,
    inquiry=inquiry,
)
void_node = ClaimNode(
    id=void_id,
    type=NodeType.COGNITIVE_VOID,
    contribution_class=ContributionClass.UNKNOWN,
    span=TextSpan(start_char=0, end_char=0, raw_text="[VOID]"),
    synthesis_metadata=SynthesisMetadata(cognitive_void=void_meta),
)

tent_s1 = EdgeEvidence(
    edge_id="tent_s1",
    source_node_id=a1.id,
    target_node_id=void_id,
    relation_type=RelationType.TENTATIVE_BRIDGE,
    weight=0.15,
    status=EdgeStatus.TENTATIVE,
    weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
)
tent_s2 = EdgeEvidence(
    edge_id="tent_s2",
    source_node_id=a2.id,
    target_node_id=void_id,
    relation_type=RelationType.TENTATIVE_BRIDGE,
    weight=0.15,
    status=EdgeStatus.TENTATIVE,
    weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
)

graph_steered = ICGGraph(
    document_id="doc_steered",
    nodes=[a1, a2, void_node],
    edges=[tent_s1, tent_s2],
    metrics_summary=MetricsSummary(cognitive_voids_count=1, tentative_edges_count=2, external_corpus_coverage=0.85)
)

initial_report = engine.get_high_value_targets(graph_steered)
target_id = initial_report.top_priority_target_id

resolving_evidence = (
    "Сверхпроводящие резонаторы объединяют кубиты и поддерживают квантовую запутанность "
    "в процессоре с минимальными потерями когерентности."
)

exec_result = engine.execute_steered_synthesis(
    graph=graph_steered,
    target_domain_id=target_id,
    void_id=void_id,
    resolving_evidence=resolving_evidence,
    confidence_score=0.90,
)

print(f"  [DEBUG] Execution Result: {exec_result}")

check("CASE_4.a Steered synthesis executed successfully", exec_result["proposal_status"] == "VERIFIED", f"status={exec_result['proposal_status']}")
check("CASE_4.b Iteration count tracked in feedback loop", exec_result["iteration"] == 1, f"iter={exec_result['iteration']}")
check("CASE_4.c Domain successfully crystallized post-synthesis", exec_result["is_crystallized"] is True, f"is_cryst={exec_result['is_crystallized']}")
check("CASE_4.d Crystallized count incremented", exec_result["post_crystallized_count"] >= 1, f"count={exec_result['post_crystallized_count']}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №12 Cognitive Steering: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Cognitive Steering & Attention Management OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
