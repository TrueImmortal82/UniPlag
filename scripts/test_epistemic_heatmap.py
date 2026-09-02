"""
test_epistemic_heatmap.py — Aris Directive #9 Test Suite
Epistemic Heatmap & Priority Queue (Cognitive Tension Ranking)

Test Cases:
  CASE_1: Basic Tension Calculation & Formula Breakdown
  CASE_2: Central Bottleneck Void vs Peripheral Void (Priority Queue Ordering)
  CASE_3: Dynamic Tension Propagation on Void Resolution
  CASE_4: Priority Queue Limit & Filter of Resolved Voids
  CASE_5: 5-Node Synthetic Cluster Validation (Aris Core Requirement)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_epistemic_heatmap.py
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
from app.icg.epistemic_heatmap import (
    calculate_void_tension,
    get_top_priority_voids,
    recompute_neighbor_tensions,
    TensionRecord,
    W_ANCHOR, W_CONNECTIVITY, W_TENTATIVE, W_CENTRALITY,
)

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_claim_node(node_id: str, text: str, conf: float = 0.85, epi_conf: float = 0.80, is_anchor: bool = True) -> ClaimNode:
    return ClaimNode(
        id=node_id,
        type=NodeType.SUPER_ANCHOR if is_anchor else NodeType.CLAIM,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
        is_anchor=is_anchor,
        is_super_anchor=is_anchor,
        confidence=conf,
        epistemic_confidence=epi_conf,
    )


def make_core_edge(src: str, tgt: str, weight: float = 0.85) -> EdgeEvidence:
    return EdgeEvidence(
        source_node_id=src,
        target_node_id=tgt,
        relation_type=RelationType.INFERS,
        weight=weight,
        status=EdgeStatus.CORE_ACTIVE_LINK,
        weight_details=EdgeWeightDetails(final_weight=weight, status=EdgeStatus.CORE_ACTIVE_LINK)
    )


def make_void(void_id: str, pole_a_id: str, pole_b_id: str, void_type: VoidType = VoidType.EMPIRICAL_GAP) -> tuple:
    inquiry = InquiryResult(
        void_node_id=void_id,
        pole_a_anchor_id=pole_a_id,
        pole_b_anchor_id=pole_b_id,
        inquiry_question=f"Question for {void_id}",
        hypotheses=["Hypothesis 1", "Hypothesis 2"],
        void_type=void_type,
        tentative_edge_ids=[f"tent_{void_id}_a", f"tent_{void_id}_b"],
    )
    meta = CognitiveVoidMetadata(
        void_type=void_type,
        void_status=VoidStatus.OPEN,
        pole_a_anchor_id=pole_a_id,
        pole_b_anchor_id=pole_b_id,
        gap_coverage_score=0.10,
        max_path_weight=0.0,
        inquiry=inquiry,
    )
    void_node = ClaimNode(
        id=void_id,
        type=NodeType.COGNITIVE_VOID,
        contribution_class=ContributionClass.UNKNOWN,
        span=TextSpan(start_char=0, end_char=0, raw_text=f"[COGNITIVE_VOID:{void_type.value}]"),
        synthesis_metadata=SynthesisMetadata(cognitive_void=meta),
        confidence=0.0,
        epistemic_confidence=0.0,
    )
    t_edge1 = EdgeEvidence(
        edge_id=f"tent_{void_id}_a",
        source_node_id=pole_a_id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )
    t_edge2 = EdgeEvidence(
        edge_id=f"tent_{void_id}_b",
        source_node_id=pole_b_id,
        target_node_id=void_id,
        relation_type=RelationType.TENTATIVE_BRIDGE,
        weight=0.15,
        status=EdgeStatus.TENTATIVE,
        weight_details=EdgeWeightDetails(final_weight=0.15, status=EdgeStatus.TENTATIVE),
    )
    return void_node, [t_edge1, t_edge2]


# =========================================================================
# CASE 1: Basic Tension Calculation
# =========================================================================
print("\n═══ CASE 1: Basic Tension Calculation ═══")
a1 = make_claim_node("a1", "Anchor A text", conf=0.90, epi_conf=0.85)
a2 = make_claim_node("a2", "Anchor B text", conf=0.90, epi_conf=0.85)
v1, t_edges1 = make_void("void_1", "a1", "a2")

graph1 = ICGGraph(
    document_id="doc_1",
    nodes=[a1, a2, v1],
    edges=t_edges1,
    metrics_summary=MetricsSummary(external_corpus_coverage=0.85)
)

tension_rec = calculate_void_tension("void_1", graph1)
check("CASE_1.a tension record generated", tension_rec is not None, f"rec={tension_rec}")
if tension_rec:
    check("CASE_1.b tension in range (0.0, 1.0]", 0.0 < tension_rec.tension <= 1.0, f"tension={tension_rec.tension}")
    check("CASE_1.c avg_pole_epistemic accurate", tension_rec.avg_pole_epistemic == 0.85, f"avg={tension_rec.avg_pole_epistemic}")
    check("CASE_1.d tentative_count is 2", tension_rec.tentative_count == 2, f"tentative_count={tension_rec.tentative_count}")


# =========================================================================
# CASE 2 & 5: 5-Node Synthetic Cluster (Central Bottleneck vs Peripheral Void)
# =========================================================================
print("\n═══ CASE 2 & 5: Central Bottleneck vs Peripheral Void (Aris Scenario) ═══")
# Nodes:
# N1, N2 (Subcluster Left)
# N3, N4 (Subcluster Right)
# N5 (Isolated Peripheral Node)
#
# Central Void (v_central): connects N1 to N3 (bridges left & right dense clusters)
# Peripheral Void (v_periph): connects N1 to N5 (N5 has 0 core edges, low confidence)

n1 = make_claim_node("n1", "Quantum coherent computation core", conf=0.95, epi_conf=0.92)
n2 = make_claim_node("n2", "Quantum error correction stabilizer", conf=0.90, epi_conf=0.88)
n3 = make_claim_node("n3", "Neural deep learning architecture", conf=0.95, epi_conf=0.90)
n4 = make_claim_node("n4", "Synaptic plasticity model", conf=0.88, epi_conf=0.84)
n5 = make_claim_node("n5", "Peripheral anecdotal observation", conf=0.40, epi_conf=0.30, is_anchor=False)

# Internal cluster edges
e12 = make_core_edge("n1", "n2", 0.90)
e21 = make_core_edge("n2", "n1", 0.85)
e34 = make_core_edge("n3", "n4", 0.92)
e43 = make_core_edge("n4", "n3", 0.88)

v_central, t_central = make_void("void_central", "n1", "n3", VoidType.EMPIRICAL_GAP)
v_periph, t_periph = make_void("void_peripheral", "n1", "n5", VoidType.LOGICAL_DISCONTINUITY)

graph_cluster = ICGGraph(
    document_id="doc_cluster",
    nodes=[n1, n2, n3, n4, n5, v_central, v_periph],
    edges=[e12, e21, e34, e43] + t_central + t_periph,
    metrics_summary=MetricsSummary(external_corpus_coverage=0.85)
)

t_rec_central = calculate_void_tension("void_central", graph_cluster)
t_rec_periph = calculate_void_tension("void_peripheral", graph_cluster)

print(f"  [DEBUG] Central Void Tension:    {t_rec_central.tension:.4f} (AvgEpi={t_rec_central.avg_pole_epistemic}, Conn={t_rec_central.connectivity_score}, Centrality={t_rec_central.centrality_score})")
print(f"  [DEBUG] Peripheral Void Tension: {t_rec_periph.tension:.4f} (AvgEpi={t_rec_periph.avg_pole_epistemic}, Conn={t_rec_periph.connectivity_score}, Centrality={t_rec_periph.centrality_score})")

check("CASE_2.a Central Tension > Peripheral Tension", t_rec_central.tension > t_rec_periph.tension,
      f"central={t_rec_central.tension:.4f} > periph={t_rec_periph.tension:.4f}")

# Test Priority Queue
top_voids = get_top_priority_voids(graph_cluster, limit=10)
check("CASE_2.b Priority Queue returned 2 voids", len(top_voids) == 2, f"len={len(top_voids)}")
check("CASE_2.c Central void is Rank #1 in Priority Queue", top_voids[0].void_id == "void_central",
      f"rank1={top_voids[0].void_id}")
check("CASE_2.d Peripheral void is Rank #2", top_voids[1].void_id == "void_peripheral",
      f"rank2={top_voids[1].void_id}")


# =========================================================================
# CASE 3: Dynamic Tension Propagation on Void Resolution
# =========================================================================
print("\n═══ CASE 3: Dynamic Tension Propagation on Void Resolution ═══")
builder = ICGGraphBuilder()

# Before resolution: check peripheral void tension
periph_tension_before = calculate_void_tension("void_peripheral", graph_cluster).tension

# Resolve Central Void
evidence = "Исследование подтверждает синтез квантовой когерентности и нейродинамики."
resolve_res = builder.resolve_cognitive_void(
    graph=graph_cluster,
    void_id="void_central",
    evidence_text=evidence,
    confidence_score=0.90,
)
check("CASE_3.a Central Void resolved successfully", resolve_res["status"] == "RESOLVED", f"status={resolve_res['status']}")

# Check that central void is no longer in Priority Queue (it is RESOLVED)
top_after_res = get_top_priority_voids(graph_cluster)
check("CASE_3.b Resolved void removed from active priority queue",
      all(v.void_id != "void_central" for v in top_after_res),
      f"remaining_in_queue={[v.void_id for v in top_after_res]}")

# Check that neighbor tensions were updated and peripheral void tension increased or was tracked
affected = resolve_res.get("affected_neighbor_tensions", {})
check("CASE_3.c Affected neighbor tensions tracked in return", "void_peripheral" in affected,
      f"affected={affected}")

periph_tension_after = calculate_void_tension("void_peripheral", graph_cluster).tension
print(f"  [DEBUG] Peripheral tension before={periph_tension_before:.4f} → after={periph_tension_after:.4f}")
check("CASE_3.d Peripheral void tension updated/propagated", periph_tension_after >= periph_tension_before,
      f"before={periph_tension_before:.4f} → after={periph_tension_after:.4f}")


# =========================================================================
# CASE 4: Priority Queue Limit & Filtering
# =========================================================================
print("\n═══ CASE 4: Priority Queue Limit ═══")
top_1 = get_top_priority_voids(graph_cluster, limit=1)
check("CASE_4.a Limit=1 strictly obeyed", len(top_1) == 1, f"len={len(top_1)}")
check("CASE_4.b Serialization to dict works", "tension" in top_1[0].to_dict(), f"dict={top_1[0].to_dict()}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №9 Epistemic Heatmap: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Epistemic Heatmap & Priority Queue OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
