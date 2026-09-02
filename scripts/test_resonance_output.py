"""
test_resonance_output.py — Aris Directive #17 Test Suite
Resonance Output Validation, Utility Gain & Anti-Echo Loop Verification

Test Cases:
  CASE_1: Semantic Thesis Generation for Cross-Domain Quantum <-> Macroeconomics Tunnel
  CASE_2: Non-Tautology Proof & High Utility Gain (TautologyScore <= 0.20, U_gain >= 0.70)
  CASE_3: Detection & Degradation of Inert Analogy (Vague metaphor penalized, bridge weight halved)
  CASE_4: Stress-Test of Intellectual Echo & Circular Reasoning (Ungrounded loops detected & degraded to ghost status)
  CASE_5: End-to-End Epistemic Quality K_qual Integration & Graph Protection

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_resonance_output.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    ICGGraph, EdgeWeightDetails,
    ProposedCrossDomainBridge, SynthesisThesis,
)
from app.icg.semantic_bridge import SemanticBridgeHarvester
from app.icg.resonance_validator import ResonanceOutputValidator

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_anchor(node_id: str, text: str, epi: float = 0.90) -> ClaimNode:
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


harvester = SemanticBridgeHarvester()
validator = ResonanceOutputValidator()

# Setup Core Domains: Quantum Mechanics <-> Macroeconomics
qm1 = make_anchor("qm1", "Квантовая запутанность обеспечивает мгновенную нелокальную корреляцию состояний частиц.", epi=0.92)
qm2 = make_anchor("qm2", "Теорема Белла математически доказывает отсутствие локального скрытого реализма.", epi=0.90)
qm_edge = make_core_edge("qm1", "qm2")

econ1 = make_anchor("econ1", "Каскадная корреляция рыночных активов создает системный риск финансовой сети.", epi=0.90)
econ2 = make_anchor("econ2", "Теория арбитражного ценообразования связывает нелокальные риски портфелей.", epi=0.88)
econ_edge = make_core_edge("econ1", "econ2")

graph = ICGGraph(
    document_id="doc_resonance_val",
    nodes=[qm1, qm2, econ1, econ2],
    edges=[qm_edge, econ_edge],
)

# Reinforced bridge connecting qm1 and econ1
bridge_valid = ProposedCrossDomainBridge(
    source_node_id="qm1",
    target_node_id="econ1",
    source_domain_id="dom_qm",
    target_domain_id="dom_econ",
    semantic_similarity=0.62,
    topological_isomorphism=1.0,
    resonance_score=0.65,
    proposed_hypothesis="Изоморфизм спектральной теории графов между квантовой запутанностью и каскадными финансовыми рисками.",
    is_validated=True,
    reinforcement_state="REINFORCED",
)

edge_valid = EdgeEvidence(
    edge_id=f"synth_{bridge_valid.bridge_id}",
    source_node_id="qm1",
    target_node_id="econ1",
    relation_type=RelationType.SYNTHESIZES,
    weight=0.92,
    status=EdgeStatus.REINFORCED_SYNTHETIC_LINK,
    weight_details=EdgeWeightDetails(final_weight=0.92, status=EdgeStatus.REINFORCED_SYNTHETIC_LINK)
)
graph.edges.append(edge_valid)


# =========================================================================
# CASE 1: Semantic Thesis Generation (Aris Mandate: Concrete Output)
# =========================================================================
print("\n═══ CASE 1: Semantic Thesis Generation ═══")
substantive_claim = (
    "Спектральная плотность матрицы ковариации связей квантовой запутанности и "
    "распределения каскадных корреляций финансовых активов описываются единым формализмом инвариантной энтропии."
)

thesis_valid = validator.generate_synthesis_thesis(graph, bridge_valid, substantive_claim)
print(f"  [DEBUG] Generated Synthesis Thesis ID: {thesis_valid.thesis_id}")
print(f"    Claim: «{thesis_valid.synthesis_claim}»")
print(f"    Novelty: {thesis_valid.novelty_score:.4f}, ExplanatoryPower: {thesis_valid.explanatory_power:.4f}, Verifiability: {thesis_valid.verifiability_score:.4f}")
print(f"    TautologyScore: {thesis_valid.tautology_score:.4f}, UtilityGain: {thesis_valid.utility_gain:.4f}")

check("CASE_1.a Structured SynthesisThesis generated successfully", bool(thesis_valid.thesis_id), f"id={thesis_valid.thesis_id}")
check("CASE_1.b Synthesis claim contains non-trivial domain synthesis", len(thesis_valid.synthesis_claim) > 50, "Claim Length OK")


# =========================================================================
# CASE 2: Non-Tautology Proof & High Utility Gain (Aris Requirement #1 & #3)
# =========================================================================
print("\n═══ CASE 2: Non-Tautology Proof & High Utility Gain ═══")
check("CASE_2.a TautologyScore is strictly low (<= 0.20)", thesis_valid.tautology_score <= 0.20, f"tautology={thesis_valid.tautology_score:.4f}")
check("CASE_2.b Verifiability score is high (>= 0.80) due to operational math terminology", thesis_valid.verifiability_score >= 0.80, f"verifiability={thesis_valid.verifiability_score:.4f}")
check("CASE_2.c Utility Gain U_gain is high (>= 0.70)", thesis_valid.utility_gain >= 0.70, f"u_gain={thesis_valid.utility_gain:.4f}")
check("CASE_2.d is_tautological flag is strictly False", thesis_valid.is_tautological is False, "is_tautological=False")


# =========================================================================
# CASE 3: Detection & Degradation of Inert Analogy (Aris Requirement #1)
# =========================================================================
print("\n═══ CASE 3: Detection & Degradation of Inert Analogy ═══")
# Candidate bridge with empty, vague phrasing referencing premises without new substance
inert_claim = "Теорема Белла и теория арбитражного ценообразования обе весьма неопределенны, сложны и абстрактны."
bridge_inert = ProposedCrossDomainBridge(
    source_node_id="qm2",
    target_node_id="econ2",
    source_domain_id="dom_qm",
    target_domain_id="dom_econ",
    semantic_similarity=0.40,
    topological_isomorphism=0.50,
    resonance_score=0.45,
    proposed_hypothesis="Пустая аналогия о неопределенности.",
    is_validated=True,
    reinforcement_state="REINFORCED",
)

edge_inert = EdgeEvidence(
    edge_id=f"synth_{bridge_inert.bridge_id}",
    source_node_id="qm2",
    target_node_id="econ2",
    relation_type=RelationType.SYNTHESIZES,
    weight=0.85,
    status=EdgeStatus.REINFORCED_SYNTHETIC_LINK,
    weight_details=EdgeWeightDetails(final_weight=0.85, status=EdgeStatus.REINFORCED_SYNTHETIC_LINK)
)
graph.edges.append(edge_inert)

thesis_inert = validator.generate_synthesis_thesis(graph, bridge_inert, inert_claim)
print(f"  [DEBUG] Inert Thesis TautologyScore: {thesis_inert.tautology_score:.4f}, U_gain: {thesis_inert.utility_gain:.4f}, IsTaut: {thesis_inert.is_tautological}")

filter_ok = validator.apply_utility_filter(graph, bridge_inert, thesis_inert)
print(f"  [DEBUG] Post-Filter Edge Weight: {edge_inert.weight:.3f}, Status: {edge_inert.status}")

check("CASE_3.a Inert analogy identified as tautological (TautologyScore >= 0.70)", thesis_inert.tautology_score >= 0.70, f"tautology={thesis_inert.tautology_score:.4f}")
check("CASE_3.b Inert analogy Utility Gain is suppressed (U_gain < 0.20)", thesis_inert.utility_gain < 0.20, f"u_gain={thesis_inert.utility_gain:.4f}")
check("CASE_3.c Bridge weight penalized & halved (0.85 -> 0.425)", edge_inert.weight == 0.425, f"weight={edge_inert.weight}")
check("CASE_3.d Bridge demoted to SPECULATIVE_LINK", edge_inert.status == EdgeStatus.SPECULATIVE_LINK, f"status={edge_inert.status}")


# =========================================================================
# CASE 4: Intellectual Echo & Circular Reasoning Detection (Aris Req #2)
# =========================================================================
print("\n═══ CASE 4: Intellectual Echo & Circular Reasoning Detection ═══")
# Construct a 3-node ungrounded circular echo loop: loop1 -> loop2 -> loop3 -> loop1
l1 = ClaimNode(id="l1", type=NodeType.CLAIM, span=TextSpan(start_char=0, end_char=20, raw_text="Гипотеза 1"), epistemic_confidence=0.50)
l2 = ClaimNode(id="l2", type=NodeType.CLAIM, span=TextSpan(start_char=0, end_char=20, raw_text="Гипотеза 2"), epistemic_confidence=0.50)
l3 = ClaimNode(id="l3", type=NodeType.CLAIM, span=TextSpan(start_char=0, end_char=20, raw_text="Гипотеза 3"), epistemic_confidence=0.50)

e_l1_l2 = EdgeEvidence(source_node_id="l1", target_node_id="l2", relation_type=RelationType.SYNTHESIZES, weight=0.80, status=EdgeStatus.SYNTHETIC_LINK)
e_l2_l3 = EdgeEvidence(source_node_id="l2", target_node_id="l3", relation_type=RelationType.SYNTHESIZES, weight=0.80, status=EdgeStatus.SYNTHETIC_LINK)
e_l3_l1 = EdgeEvidence(source_node_id="l3", target_node_id="l1", relation_type=RelationType.SYNTHESIZES, weight=0.80, status=EdgeStatus.SYNTHETIC_LINK)

graph_circular = ICGGraph(
    document_id="doc_circular",
    nodes=[l1, l2, l3],
    edges=[e_l1_l2, e_l2_l3, e_l3_l1],
)

degraded_cycles = validator.detect_and_degrade_circular_loops(graph_circular)
print(f"  [DEBUG] Degraded Circular Cycles Count: {len(degraded_cycles)}")
print(f"    Cycle Nodes: {degraded_cycles}")
print(f"    Cycle Edge Weights: {[e.weight for e in graph_circular.edges]}")
print(f"    Cycle Edge Statuses: {[e.status for e in graph_circular.edges]}")

check("CASE_4.a Self-referential circular loop detected", len(degraded_cycles) == 1, f"cycles={len(degraded_cycles)}")
check("CASE_4.b All circular edges degraded to ghost status (weights <= 0.20)",
      all(e.weight <= 0.20 for e in graph_circular.edges),
      f"weights={[e.weight for e in graph_circular.edges]}")
check("CASE_4.c All circular edges converted to SPECULATIVE_LINK",
      all(e.status == EdgeStatus.SPECULATIVE_LINK for e in graph_circular.edges),
      f"statuses={[e.status for e in graph_circular.edges]}")


# =========================================================================
# CASE 5: End-to-End Epistemic Quality K_qual Integration
# =========================================================================
print("\n═══ CASE 5: End-to-End Epistemic Quality K_qual Integration ═══")
# In graph with speculative inert link, K_qual is correctly damped
score_with_speculative = harvester.compute_synthesis_coefficient(graph)
print(f"  [DEBUG] Synthesis Score With Speculative Link: K_qual={score_with_speculative.k_qual:.4f}")

# Remove the demoted inert link to evaluate pure verified synthesis
graph_pure = ICGGraph(
    document_id="doc_pure",
    nodes=[qm1, qm2, econ1, econ2],
    edges=[qm_edge, econ_edge, edge_valid],
)
score_pure = harvester.compute_synthesis_coefficient(graph_pure)
print(f"  [DEBUG] Pure Verified Synthesis Score: K_quant={score_pure.k_quant:.4f}, K_qual={score_pure.k_qual:.4f}, K_composite={score_pure.k_composite:.4f}")

check("CASE_5.a Verified High-Utility pure synthesis achieves K_qual >= 0.70", score_pure.k_qual >= 0.70, f"k_qual={score_pure.k_qual:.4f}")
check("CASE_5.b Active reinforced bridges count correctly preserved", score_pure.active_bridges_count == 1, f"active_bridges={score_pure.active_bridges_count}")
check("CASE_5.c Speculative inert link dampens K_qual (Directive #15 safety)", score_with_speculative.k_qual < score_pure.k_qual, f"{score_with_speculative.k_qual:.4f} < {score_pure.k_qual:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №17 Resonance Output Validation: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Resonance Output Validation & Utility Gain OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
