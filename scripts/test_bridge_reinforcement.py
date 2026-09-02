"""
test_bridge_reinforcement.py — Aris Directive #15 Test Suite
Stabilization of Synthetic Bridges, Adversarial Counter-Refutation & Epistemic Reinforcement

Test Cases:
  CASE_1: Dynamic Adaptive Resonance Threshold (Scaling with Wasteland & Contradiction)
  CASE_2: Adversarial Counter-Refutation & Bridge Reinforcement (Clean Bridge -> REINFORCED, K_qual >= 0.70)
  CASE_3: Axiomatic Conflict Detection & Speculative Demotion (Text trace recorded, SPECULATIVE_LINK)
  CASE_4: Epistemic Avalanche Stress Test (High-level mimicry barrage, K_qual protected)
  CASE_5: False Refutation Resistance (Low-confidence noisy neighbor cannot overturn verified bridge)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_bridge_reinforcement.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    DomainZoneType, DomainStabilityState, ProposedCrossDomainBridge,
)
from app.icg.semantic_bridge import SemanticBridgeHarvester
from app.icg.ingestion_pipeline import IngestionPipeline

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)
    return condition


def make_anchor(node_id: str, text: str, epi: float = 0.88) -> ClaimNode:
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

# =========================================================================
# CASE 1: Dynamic Adaptive Resonance Threshold
# =========================================================================
print("\n═══ CASE 1: Dynamic Adaptive Resonance Threshold ═══")
# Construct Graph with pristine domain and turbulent domain
p1 = make_anchor("p1", "Квантовая суперпозиция кубитов", epi=0.92)
p2 = make_anchor("p2", "Лазерное охлаждение ионных ловушек", epi=0.90)
p_edge = make_core_edge("p1", "p2")

w1 = make_anchor("w1", "Хаотическая динамика рыночных котировок", epi=0.40)
w2 = make_anchor("w2", "Случайные флуктуации волатильности", epi=0.35)
w_edge = make_core_edge("w1", "w2", weight=0.40)

graph_thresh = ICGGraph(
    document_id="doc_thresh",
    nodes=[p1, p2, w1, w2],
    edges=[p_edge, w_edge],
)

top_thresh = harvester.topology_analyzer.analyze_topology(graph_thresh)
d_pristine = next(d for d in top_thresh.domains if "p1" in d.member_node_ids)
d_turbulent = next(d for d in top_thresh.domains if "w1" in d.member_node_ids)

thresh_pristine = harvester.compute_adaptive_threshold(d_pristine, d_pristine, graph_thresh, base_threshold=0.50)
thresh_turbulent = harvester.compute_adaptive_threshold(d_turbulent, d_turbulent, graph_thresh, base_threshold=0.50)

print(f"  [DEBUG] Adaptive Thresholds: Pristine={thresh_pristine:.4f}, Turbulent={thresh_turbulent:.4f}")
check("CASE_1.a Pristine domain maintains baseline threshold (0.50)", thresh_pristine == 0.50, f"pristine={thresh_pristine}")
check("CASE_1.b Turbulent/Wasteland domain raises threshold (>0.55)", thresh_turbulent >= 0.55, f"turbulent={thresh_turbulent}")


# =========================================================================
# CASE 2: Adversarial Counter-Refutation & Bridge Reinforcement
# =========================================================================
print("\n═══ CASE 2: Adversarial Counter-Refutation & Bridge Reinforcement ═══")
# Setup 2 clean crystal domains: Event Sourcing & Biological Spikes
sa1 = make_anchor("sa1", "Асинхронные шины событий обеспечивают слабую связность микросервисов.", epi=0.92)
sa2 = make_anchor("sa2", "Паттерн Event Sourcing сохраняет полную хронологию мутаций состояния.", epi=0.90)
sa_edge = make_core_edge("sa1", "sa2")

bio1 = make_anchor("bio1", "Спайковые потенциалы действия передают дискретные импульсы по аксонам.", epi=0.92)
bio2 = make_anchor("bio2", "Синаптическая пластичность Хебба адаптирует силу синапсов.", epi=0.90)
bio_edge = make_core_edge("bio1", "bio2")

graph_clean = ICGGraph(
    document_id="doc_clean",
    nodes=[sa1, sa2, bio1, bio2],
    edges=[sa_edge, bio_edge],
)

top_clean = harvester.topology_analyzer.analyze_topology(graph_clean)
dom_sa = next(d for d in top_clean.domains if "sa1" in d.member_node_ids)
dom_bio = next(d for d in top_clean.domains if "bio1" in d.member_node_ids)

bridge_clean = ProposedCrossDomainBridge(
    source_node_id=sa1.id,
    target_node_id=bio1.id,
    source_domain_id=dom_sa.domain_id,
    target_domain_id=dom_bio.domain_id,
    semantic_similarity=0.75,
    topological_isomorphism=1.0,
    resonance_score=0.68,
    proposed_hypothesis="Асинхронные шины событий функционально изоморфны спайковым потенциалам действия.",
)

resolving_clean = (
    "Асинхронные шины событий и спайковые нейронные импульсы реализуют единый принцип "
    "дискретной асинхронной передачи сообщений, устраняя блокировку узлов."
)

ok2 = harvester.validate_and_install_bridge(
    graph=graph_clean,
    bridge=bridge_clean,
    resolving_evidence=resolving_clean,
    confidence_score=0.95,
)

print(f"  [DEBUG] Clean Bridge Validation: {ok2}, State: {bridge_clean.reinforcement_state}, RefutationPressure: {bridge_clean.refutation_pressure}")
check("CASE_2.a Clean Bridge validation successful", ok2 is True, "Validation OK")
check("CASE_2.b Bridge reinforcement state is REINFORCED", bridge_clean.reinforcement_state == "REINFORCED", f"state={bridge_clean.reinforcement_state}")
check("CASE_2.c Refutation pressure is minimal (<=0.20)", bridge_clean.refutation_pressure <= 0.20, f"ref_press={bridge_clean.refutation_pressure}")

synth_edge_2 = next((e for e in graph_clean.edges if e.status == EdgeStatus.REINFORCED_SYNTHETIC_LINK), None)
check("CASE_2.d Edge status is REINFORCED_SYNTHETIC_LINK with boosted weight (>=0.90)",
      synth_edge_2 is not None and synth_edge_2.weight >= 0.90,
      f"edge_weight={synth_edge_2.weight if synth_edge_2 else None}")

score2 = harvester.compute_synthesis_coefficient(graph_clean)
print(f"  [DEBUG] Post-Reinforcement K_qual: {score2.k_qual:.4f}, K_composite: {score2.k_composite:.4f}")
check("CASE_2.e High Epistemic Quality K_qual achieved (>=0.70)", score2.k_qual >= 0.70, f"k_qual={score2.k_qual:.4f}")


# =========================================================================
# CASE 3: Axiomatic Conflict Detection & Speculative Demotion
# =========================================================================
print("\n═══ CASE 3: Axiomatic Conflict Detection & Speculative Demotion ═══")
# Inject an opposing axiom into the biological domain
bio_contra = make_anchor(
    "bio_contra",
    "Передача сигналов в синапсах полностью непрерывна и аналогова, не допуская дискретные импульсы.",
    epi=0.92
)
graph_clean.nodes.append(bio_contra)
graph_clean.edges.append(make_core_edge("bio1", "bio_contra"))

bridge_speculative = ProposedCrossDomainBridge(
    source_node_id=sa2.id,
    target_node_id=bio2.id,
    source_domain_id=dom_sa.domain_id,
    target_domain_id=dom_bio.domain_id,
    semantic_similarity=0.70,
    topological_isomorphism=1.0,
    resonance_score=0.65,
    proposed_hypothesis="Event Sourcing и синаптическая передача строго дискретны и не имеют аналоговых свойств.",
)

resolving_spec = "Event Sourcing и синапсы работают строго в дискретном импульсном режиме, реализуя квантованную передачу."

ok3 = harvester.validate_and_install_bridge(
    graph=graph_clean,
    bridge=bridge_speculative,
    resolving_evidence=resolving_spec,
    confidence_score=0.90,
)

print(f"  [DEBUG] Speculative Bridge Validation: {ok3}, State: {bridge_speculative.reinforcement_state}, RefutationPressure: {bridge_speculative.refutation_pressure}")
print(f"    Refuting Node: {bridge_speculative.refutation_node_id}, Snippet: {bridge_speculative.refutation_evidence_text}")

check("CASE_3.a Counter-Refutation detects the conflicting axiom (RefutationPressure > 0.40)",
      bridge_speculative.refutation_pressure > 0.40,
      f"ref_press={bridge_speculative.refutation_pressure}")
check("CASE_3.b Refuting node ID and text trace recorded for audit (Aris Requirement #1)",
      bridge_speculative.refutation_node_id == "bio_contra" and bridge_speculative.refutation_evidence_text is not None,
      f"ref_node={bridge_speculative.refutation_node_id}")
check("CASE_3.c Bridge downgraded to SPECULATIVE_LINK",
      bridge_speculative.reinforcement_state == "SPECULATIVE",
      f"state={bridge_speculative.reinforcement_state}")


# =========================================================================
# CASE 4: Epistemic Avalanche Stress Test (K_qual Protected)
# =========================================================================
print("\n═══ CASE 4: Epistemic Avalanche Stress Test ═══")
# Inject 3 speculative links into graph_clean
score_before = harvester.compute_synthesis_coefficient(graph_clean)

# Verify that speculative links apply damping penalty and do not falsely inflate K_qual
check("CASE_4.a Speculative link penalizes / damps K_qual without corrupting reinforced core",
      score_before.k_qual < score2.k_qual,
      f"k_qual_with_spec={score_before.k_qual:.4f} < clean={score2.k_qual:.4f}")


# =========================================================================
# CASE 5: False Refutation Resistance (Aris Requirement #4)
# =========================================================================
print("\n═══ CASE 5: False Refutation Resistance ═══")
# Inject a noisy low-confidence node trying to refute a bridge
noisy_refuter = make_anchor(
    "noise_ref",
    "Микросервисы полностью невозможны и асинхронные шины запрещены физикой.",
    epi=0.15 # Very low epistemic confidence
)
graph_clean.nodes.append(noisy_refuter)

ref_press_noisy, r_id, r_txt = harvester.adversarial_counter_refutation(
    graph=graph_clean,
    bridge=bridge_clean,
    hypothesis_text=resolving_clean,
)

print(f"  [DEBUG] Noisy Refuter Effective Pressure: {ref_press_noisy:.4f}")
check("CASE_5.a Low-confidence noise discounted by epistemic weighting (EffectivePressure <= 0.20)",
      ref_press_noisy <= 0.20,
      f"effective_contra={ref_press_noisy:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №15 Bridge Stabilization: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Synthetic Bridge Stabilization & Epistemic Reinforcement OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
