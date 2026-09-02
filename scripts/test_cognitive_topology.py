"""
test_cognitive_topology.py — Aris Directive #11 Test Suite
Cognitive Topology, Dynamic Clustering & Epistemic Landscape

Test Cases:
  CASE_1: Crystallized Knowledge Zone (High density, 0 contradictions, STABLE)
  CASE_2: Turbulence Zone & Paradox Core (High density + high contradiction -> OVERHEATED, UNSTABLE)
  CASE_3: Cognitive Wasteland Zone (Sparse density, unresolved voids -> COGNITIVE_WASTELAND)
  CASE_4: Domain Collapse Scenario (Aris Mandatory Requirement: Destabilizing crystal -> TURBULENCE_ZONE / UNSTABLE)
  CASE_5: Domain Abstraction to MacroSuperNode (internal_entropy + strongest_boundary_weights preserved)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_cognitive_topology.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    DomainZoneType, DomainStabilityState, CognitiveDomain,
)
from app.icg.topology import TopologyAnalyzer

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_node(node_id: str, text: str, conf: float = 0.90, epi: float = 0.85) -> ClaimNode:
    return ClaimNode(
        id=node_id,
        type=NodeType.SUPER_ANCHOR,
        contribution_class=ContributionClass.SYNTHESIS,
        span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
        is_anchor=True,
        is_super_anchor=True,
        confidence=conf,
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


def make_void(void_id: str, pole_a_id: str, pole_b_id: str) -> ClaimNode:
    inquiry = InquiryResult(
        void_node_id=void_id,
        pole_a_anchor_id=pole_a_id,
        pole_b_anchor_id=pole_b_id,
        inquiry_question=f"Question for {void_id}",
        hypotheses=["H1"],
        void_type=VoidType.EMPIRICAL_GAP,
    )
    meta = CognitiveVoidMetadata(
        void_type=VoidType.EMPIRICAL_GAP,
        void_status=VoidStatus.OPEN,
        pole_a_anchor_id=pole_a_id,
        pole_b_anchor_id=pole_b_id,
        inquiry=inquiry,
    )
    return ClaimNode(
        id=void_id,
        type=NodeType.COGNITIVE_VOID,
        contribution_class=ContributionClass.UNKNOWN,
        span=TextSpan(start_char=0, end_char=0, raw_text="[VOID]"),
        synthesis_metadata=SynthesisMetadata(cognitive_void=meta),
    )


analyzer = TopologyAnalyzer()

# =========================================================================
# CASE 1: Crystallized Knowledge Zone
# =========================================================================
print("\n═══ CASE 1: Crystallized Knowledge Zone ═══")
# 4 tightly coupled nodes with verified positive edges and 0 conflicts
c1 = make_node("c1", "Квантовая суперпозиция в резонаторе", epi=0.88)
c2 = make_node("c2", "Управление кубитами через лазерные импульсы", epi=0.86)
c3 = make_node("c3", "Квантовая коррекция ошибок на торических кодах", epi=0.85)

edges_crystal = [
    make_core_edge("c1", "c2"),
    make_core_edge("c2", "c3"),
    make_core_edge("c3", "c1"),
]

graph_crystal = ICGGraph(
    document_id="doc_crystal",
    nodes=[c1, c2, c3],
    edges=edges_crystal,
)

report1 = analyzer.analyze_topology(graph_crystal)
print(f"  [DEBUG] Crystal Domains: {len(report1.domains)}, Type: {report1.domains[0].zone_type}, Stability: {report1.domains[0].stability_score:.4f}")

check("CASE_1.a 1 Cognitive Domain detected", len(report1.domains) == 1, f"count={len(report1.domains)}")
check("CASE_1.b Zone type is CRYSTALLIZED_KNOWLEDGE", report1.domains[0].zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE, f"zone={report1.domains[0].zone_type}")
check("CASE_1.c Stability state is STABLE", report1.domains[0].stability_state == DomainStabilityState.STABLE, f"state={report1.domains[0].stability_state}")
check("CASE_1.d Stability score is high (>0.50)", report1.domains[0].stability_score > 0.50, f"score={report1.domains[0].stability_score}")
check("CASE_1.e Contradiction ratio is 0.0", report1.domains[0].contradiction_ratio == 0.0, f"ratio={report1.domains[0].contradiction_ratio}")


# =========================================================================
# CASE 2: Turbulence Zone & Paradox Core
# =========================================================================
print("\n═══ CASE 2: Turbulence Zone & Paradox Core (Overheated) ═══")
t1 = make_node("t1", "Быстрый экономический рост через монетарную эмиссию", epi=0.88)
t2 = make_node("t2", "Инфляционная спираль и обесценение сбережений", epi=0.85)
t3 = make_node("t3", "Стагфляционный парадокс и валютный кризис", epi=0.82)

edges_turb = [
    make_core_edge("t1", "t2"),
    make_core_edge("t2", "t3"),
    make_repulsion_edge("t1", "t3"),  # Strong repulsion
]

graph_turb = ICGGraph(
    document_id="doc_turb",
    nodes=[t1, t2, t3],
    edges=edges_turb,
)

report2 = analyzer.analyze_topology(graph_turb)
print(f"  [DEBUG] Turb Domains: {len(report2.domains)}, Type: {report2.domains[0].zone_type}, Stability: {report2.domains[0].stability_score:.4f}, Overheated: {report2.domains[0].is_overheated}")

check("CASE_2.a Zone type is PARADOX_CORE or TURBULENCE_ZONE", 
      report2.domains[0].zone_type in (DomainZoneType.PARADOX_CORE, DomainZoneType.TURBULENCE_ZONE),
      f"zone={report2.domains[0].zone_type}")
check("CASE_2.b Stability state is UNSTABLE", report2.domains[0].stability_state == DomainStabilityState.UNSTABLE, f"state={report2.domains[0].stability_state}")
check("CASE_2.c Domain is flagged as OVERHEATED", report2.domains[0].is_overheated is True, "overheated=True")
check("CASE_2.d Contradiction alert generated", report2.domains[0].contradiction_alert_required is True, "alert=True")
check("CASE_2.e Contradiction ratio is significant (>0.20)", report2.domains[0].contradiction_ratio >= 0.20, f"ratio={report2.domains[0].contradiction_ratio}")


# =========================================================================
# CASE 3: Cognitive Wasteland Zone
# =========================================================================
print("\n═══ CASE 3: Cognitive Wasteland Zone ═══")
w1 = make_node("w1", "Гипотетическое наблюдение квантовой памяти", epi=0.45)
w2 = make_node("w2", "Непроверенный тезис о синапсах", epi=0.40)
void_w = make_void("void_waste_1", "w1", "w2")

graph_waste = ICGGraph(
    document_id="doc_waste",
    nodes=[w1, w2, void_w],
    edges=[],  # Sparse, 0 positive edges
)

report3 = analyzer.analyze_topology(graph_waste)
print(f"  [DEBUG] Waste Domains: {len(report3.domains)}, Types: {[d.zone_type for d in report3.domains]}")

check("CASE_3.a Cognitive Wasteland identified",
      any(d.zone_type == DomainZoneType.COGNITIVE_WASTELAND for d in report3.domains),
      f"types={[d.zone_type for d in report3.domains]}")
check("CASE_3.b Wasteland state is UNSTABLE",
      all(d.stability_state == DomainStabilityState.UNSTABLE for d in report3.domains if d.zone_type == DomainZoneType.COGNITIVE_WASTELAND),
      "all wasteland UNSTABLE")


# =========================================================================
# CASE 4: Domain Collapse Scenario (Aris Core Requirement)
# =========================================================================
print("\n═══ CASE 4: Domain Collapse Scenario (Destabilization of Crystal) ═══")
# Inject a hostile node into the crystal cluster with repulsion edges to c1 and c2
hostile_node = make_node("hostile_anti_quantum", "Полное отрицание квантовых эффектов в любых макросистемах", epi=0.70)
edge_hostile_1 = make_repulsion_edge("hostile_anti_quantum", "c1")
edge_hostile_2 = make_repulsion_edge("hostile_anti_quantum", "c2")
edge_hostile_pos = make_core_edge("hostile_anti_quantum", "c3", 0.50)  # Partially connected

graph_collapsed = ICGGraph(
    document_id="doc_collapsed",
    nodes=[c1, c2, c3, hostile_node],
    edges=edges_crystal + [edge_hostile_1, edge_hostile_2, edge_hostile_pos],
)

report_collapsed = analyzer.analyze_topology(graph_collapsed)
collapsed_domain = report_collapsed.domains[0]
print(f"  [DEBUG] Collapsed Domain: Type={collapsed_domain.zone_type}, State={collapsed_domain.stability_state}, StabilityScore={collapsed_domain.stability_score:.4f}, ContraRatio={collapsed_domain.contradiction_ratio:.4f}")

check("CASE_4.a Crystal collapsed to TURBULENCE_ZONE or PARADOX_CORE", 
      collapsed_domain.zone_type in (DomainZoneType.TURBULENCE_ZONE, DomainZoneType.PARADOX_CORE),
      f"zone={collapsed_domain.zone_type}")
check("CASE_4.b State flipped from STABLE to UNSTABLE", collapsed_domain.stability_state == DomainStabilityState.UNSTABLE, f"state={collapsed_domain.stability_state}")
check("CASE_4.c Exponential drop in stability score", collapsed_domain.stability_score < report1.domains[0].stability_score * 0.5,
      f"before={report1.domains[0].stability_score:.4f} -> after={collapsed_domain.stability_score:.4f}")
check("CASE_4.d Contradiction alert activated", collapsed_domain.contradiction_alert_required is True, "alert=True")


# =========================================================================
# CASE 5: Domain Abstraction & MacroSuperNode
# =========================================================================
print("\n═══ CASE 5: Domain Abstraction & MacroSuperNode ═══")
# Connect crystal domain to an external domain
ext1 = make_node("ext1", "Внешний домен машинного обучения", epi=0.90)
edge_bridge = make_core_edge("c1", "ext1", 0.78)

graph_multi = ICGGraph(
    document_id="doc_multi",
    nodes=[c1, c2, c3, ext1],
    edges=edges_crystal + [edge_bridge],
)

report_multi = analyzer.analyze_topology(graph_multi)
super_nodes = report_multi.super_nodes
print(f"  [DEBUG] Super-Nodes Generated: {len(super_nodes)}")

check("CASE_5.a Super-Nodes generated for stable domains", len(super_nodes) >= 1, f"count={len(super_nodes)}")
if super_nodes:
    sn = super_nodes[0]
    print(f"  [DEBUG] SuperNode: {sn.label}, Entropy={sn.internal_entropy}, BoundaryWeights={sn.strongest_boundary_weights}")
    check("CASE_5.b internal_entropy computed (variance/dispersion)", sn.internal_entropy >= 0.0, f"entropy={sn.internal_entropy}")
    check("CASE_5.c Member count accurate", sn.member_count == 3, f"count={sn.member_count}")
    check("CASE_5.d Boundary edges preserved", sn.boundary_edge_count >= 1, f"boundary={sn.boundary_edge_count}")
    check("CASE_5.e Strongest boundary weight recorded", len(sn.strongest_boundary_weights) >= 1, f"weights={sn.strongest_boundary_weights}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №11 Cognitive Topology: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Cognitive Topology & Clustering OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
