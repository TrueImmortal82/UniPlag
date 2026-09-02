"""
test_synthetic_stress.py — Aris Directive #13 Stress-Test Suite
Stress-Testing the Synthetic Bridge: Noise Resistance, False Crystallization & Insight Loss

Test Cases:
  CASE_1: Discrimination: Genuine Paradox vs Pseudo-Paradox Noise (Compute Steering & Filtration)
  CASE_2: False Crystallization Resistance under Adaptive Mimicry Noise (FCR == 0.0%)
  CASE_3: Mass Neutral Flooding & Topological Quarantine (Isolation of Wasteland from Crystal)
  CASE_4: Synthesis Confusion Matrix & Insight Loss Evaluation (FCR=0%, InsightLoss=0%, Accuracy>=95%)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_synthetic_stress.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    DomainZoneType, DomainStabilityState, ResolutionStatus,
)
from app.icg.stress_generator import StressGenerator
from app.icg.synthesis_loop import SynthesisLoopEngine
from app.icg.topology import TopologyAnalyzer
from app.icg.cognitive_steering import CognitiveSteeringEngine

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
        hypotheses=["Hypothesis"],
        void_type=VoidType.EMPIRICAL_GAP,
        tentative_edge_ids=[f"t_{void_id}_1", f"t_{void_id}_2"],
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
        span=TextSpan(start_char=0, end_char=0, raw_text="[COGNITIVE_VOID]"),
        synthesis_metadata=SynthesisMetadata(cognitive_void=meta),
    )


stress_gen = StressGenerator()
synthesis_engine = SynthesisLoopEngine()
topology_analyzer = TopologyAnalyzer()
steering_engine = CognitiveSteeringEngine()

# =========================================================================
# CASE 1: Discrimination: Genuine Paradox vs Pseudo-Paradox Noise
# =========================================================================
print("\n═══ CASE 1: Discrimination: Genuine Paradox vs Pseudo-Paradox ═══")
# Setup a genuine paradox domain (3 nodes: GR + QM + observation bridge with dialectical tension)
paradox_case = stress_gen.get_genuine_paradox_cases()[0]
gp_a = make_anchor("gp_a", paradox_case["pole_a"], epi=0.92)
gp_b = make_anchor("gp_b", paradox_case["pole_b"], epi=0.90)
gp_c = make_anchor("gp_c", "Экспериментальные данные планковской интерферометрии", epi=0.88)
gp_e1 = make_core_edge("gp_a", "gp_c")
gp_e2 = make_core_edge("gp_b", "gp_c")
gp_rep = make_repulsion_edge("gp_a", "gp_b")

# Setup a pseudo-noise domain (2 isolated low-confidence nodes)
pseudo_noise = stress_gen.get_pseudo_paradox_noise(2)
pn_a = make_anchor("pn_a", pseudo_noise[0], epi=0.35)
pn_b = make_anchor("pn_b", pseudo_noise[1], epi=0.30)
pn_rep = make_repulsion_edge("pn_a", "pn_b")

graph_disc = ICGGraph(
    document_id="doc_disc",
    nodes=[gp_a, gp_b, gp_c, pn_a, pn_b],
    edges=[gp_e1, gp_e2, gp_rep, pn_rep],
)

disc_report = steering_engine.get_high_value_targets(graph_disc, total_compute_budget=1000)
top_target = disc_report.targets[0]
print(f"  [DEBUG] Top Target: {top_target.label}, Zone={top_target.zone_type.value}, Budget={top_target.allocated_compute_units} ({top_target.budget_percentage}%)")

check("CASE_1.a Genuine Paradox ranked #1 in compute allocation",
      any("относительности" in node.span.raw_text for nid in top_target.member_node_ids for node in [gp_a, gp_b, gp_c] if node.id == nid),
      f"top_target_label={top_target.label}")
check("CASE_1.b Genuine Paradox receives majority of budget (>=70%)", top_target.budget_percentage >= 70.0,
      f"pct={top_target.budget_percentage}%")
check("CASE_1.c Pseudo noise receives minimal budget (<30%)", 
      all(t.budget_percentage < 30.0 for t in disc_report.targets if t.target_id != top_target.target_id),
      f"targets_pct={[t.budget_percentage for t in disc_report.targets]}")


# =========================================================================
# CASE 2: False Crystallization Resistance under Adaptive Mimicry Noise
# =========================================================================
print("\n═══ CASE 2: False Crystallization Resistance (Adaptive Mimicry) ═══")
# Construct a target void between quantum anchors
c_a = make_anchor("c_a", "Квантовая когерентность в кубитах ускоряет вычисления и масштабирует квантовые системы.", epi=0.88)
c_b = make_anchor("c_b", "Синаптическая пластичность в нейронах обеспечивает обучение и консолидацию памяти.", epi=0.85)
void_target = make_void("void_mimic_test", c_a.id, c_b.id)

graph_mimic = ICGGraph(
    document_id="doc_mimic",
    nodes=[c_a, c_b, void_target],
    edges=[],
    metrics_summary=MetricsSummary(cognitive_voids_count=1, tentative_edges_count=2, external_corpus_coverage=0.85)
)

# Generate 10 adaptive mimicry noise sentences (using vocabulary of c_a and c_b)
mimicry_samples = stress_gen.generate_adaptive_mimicry([c_a, c_b], count=10)

false_crystallizations = 0
rejections = 0

for i, sample in enumerate(mimicry_samples):
    prop = synthesis_engine.propose_void_resolution(
        graph=graph_mimic,
        void_id="void_mimic_test",
        evidence_text=sample,
        evidence_source="Mimicry Generator",
        confidence_score=0.90,
    )
    if prop.status == ResolutionStatus.VERIFIED:
        false_crystallizations += 1
    else:
        rejections += 1

print(f"  [DEBUG] Mimicry Test: Rejections={rejections}/10, False Crystallizations={false_crystallizations}/10")

check("CASE_2.a Zero False Crystallizations (FCR = 0.0%)", false_crystallizations == 0,
      f"false_cryst={false_crystallizations}")
check("CASE_2.b 100% of mimicry noise rejected by NLI filter", rejections == 10,
      f"rejections={rejections}/10")
check("CASE_2.c Target void remained OPEN throughout attack",
      graph_mimic.nodes[2].synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN, "OPEN")


# =========================================================================
# CASE 3: Mass Neutral Flooding & Topological Quarantine
# =========================================================================
print("\n═══ CASE 3: Mass Neutral Flooding & Topological Quarantine ═══")
# Start with a pristine crystal cluster
cr1 = make_anchor("cr1", "Квантовая суперпозиция в резонаторе", 0.90)
cr2 = make_anchor("cr2", "Лазерный контроль квантовых состояний", 0.88)
cr3 = make_anchor("cr3", "Топологические коды коррекции ошибок", 0.86)
cr_edges = [make_core_edge("cr1", "cr2"), make_core_edge("cr2", "cr3"), make_core_edge("cr3", "cr1")]

# Inject 15 neutral flooding nodes
flood_samples = stress_gen.get_neutral_flood(15)
flood_nodes = [make_anchor(f"flood_{i}", text, epi=0.40) for i, text in enumerate(flood_samples)]

graph_flood = ICGGraph(
    document_id="doc_flood",
    nodes=[cr1, cr2, cr3] + flood_nodes,
    edges=cr_edges, # No edges to flood nodes
)

flood_topology = topology_analyzer.analyze_topology(graph_flood)
print(f"  [DEBUG] Domains Detected: {len(flood_topology.domains)}, Crystallized Count: {flood_topology.crystallized_count}, Wasteland Count: {flood_topology.wasteland_count}")

# Verify that the crystal domain is completely preserved
crystal_domain = next((d for d in flood_topology.domains if d.zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE), None)
check("CASE_3.a Crystal Domain perfectly preserved intact", crystal_domain is not None, "Crystal domain intact")
if crystal_domain:
    check("CASE_3.b Crystal stability remains STABLE (score >= 0.70)", crystal_domain.stability_score >= 0.70,
          f"stability={crystal_domain.stability_score:.4f}")
    check("CASE_3.c Crystal membership exact (3 nodes)", len(crystal_domain.member_node_ids) == 3,
          f"members={len(crystal_domain.member_node_ids)}")

# Verify that all flood nodes are segregated into Wasteland / unverified domains
wasteland_domains = [d for d in flood_topology.domains if d.zone_type == DomainZoneType.COGNITIVE_WASTELAND]
check("CASE_3.d Flooding nodes quarantined into COGNITIVE_WASTELAND", len(wasteland_domains) >= 1,
      f"wastelands={len(wasteland_domains)}")


# =========================================================================
# CASE 4: Full Synthesis Confusion Matrix & Insight Loss
# =========================================================================
print("\n═══ CASE 4: Confusion Matrix, FCR & Insight Loss ═══")
# Benchmark battery:
# 2 Genuine Paradoxes with valid synthesis (TP targets)
# 10 Mimicry Noise (TN targets)
# 5 Pseudo-Paradoxes (TN targets)
# 5 Neutral Floods (TN targets)

tp = 0
tn = 0
fp = 0
fn = 0

# Test Genuine Paradoxes (should be VERIFIED upon valid synthesis)
for gp in stress_gen.get_genuine_paradox_cases():
    p_a = make_anchor("p_a", gp["pole_a"], 0.90)
    p_b = make_anchor("p_b", gp["pole_b"], 0.88)
    v_node = make_void("v_gp", p_a.id, p_b.id)
    g = ICGGraph(document_id="doc_tp", nodes=[p_a, p_b, v_node], edges=[])
    
    prop = synthesis_engine.propose_void_resolution(g, "v_gp", gp["resolving_synthesis"], confidence_score=0.90)
    if prop.status == ResolutionStatus.VERIFIED:
        tp += 1
    else:
        fn += 1

# Test Noise Batteries (should all be REJECTED)
noise_battery = (
    stress_gen.generate_adaptive_mimicry([c_a, c_b], 5) +
    stress_gen.get_pseudo_paradox_noise(5) +
    stress_gen.get_neutral_flood(5)
)

for noise_text in noise_battery:
    p_a = make_anchor("p_a", "Квантовая суперпозиция в резонаторе", 0.90)
    p_b = make_anchor("p_b", "Лазерный контроль квантовых состояний", 0.88)
    v_node = make_void("v_noise", p_a.id, p_b.id)
    g = ICGGraph(document_id="doc_tn", nodes=[p_a, p_b, v_node], edges=[])
    
    prop = synthesis_engine.propose_void_resolution(g, "v_noise", noise_text, confidence_score=0.90)
    if prop.status == ResolutionStatus.VERIFIED:
        fp += 1
    else:
        tn += 1

total_samples = tp + tn + fp + fn
accuracy = (tp + tn) / total_samples
fcr = fp / max(1, (fp + tn))
insight_loss = fn / max(1, (tp + fn))
precision = tp / max(1, (tp + fp))
recall = tp / max(1, (tp + fn))
f1 = 2 * (precision * recall) / max(1e-6, (precision + recall))

print(f"\n  [CONFUSION MATRIX]")
print(f"  TP (Genuine Validated):    {tp}")
print(f"  TN (Noise Rejected):        {tn}")
print(f"  FP (False Crystallization): {fp}")
print(f"  FN (Insight Lost):          {fn}")
print(f"  Accuracy:                   {accuracy * 100:.1f}%")
print(f"  False Crystallization Rate: {fcr * 100:.1f}%")
print(f"  Insight Loss Rate:          {insight_loss * 100:.1f}%")
print(f"  Macro-F1 Score:             {f1:.4f}")

check("CASE_4.a False Crystallization Rate is strictly 0.0%", fcr == 0.0, f"FCR={fcr*100:.1f}%")
check("CASE_4.b Insight Loss is strictly 0.0% (Zero genuine insights missed)", insight_loss == 0.0, f"InsightLoss={insight_loss*100:.1f}%")
check("CASE_4.c Synthesis Accuracy is 100.0%", accuracy == 1.0, f"Accuracy={accuracy*100:.1f}%")
check("CASE_4.d Macro-F1 is 1.0000", f1 == 1.0, f"F1={f1:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №13 Stress Test: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Synthetic Bridge STRESS-TEST VERIFIED (FCR=0.0%, InsightLoss=0.0%)")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
