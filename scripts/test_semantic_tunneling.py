"""
test_semantic_tunneling.py — Aris Directive #16 Test Suite
Dynamic Heuristic Exploration, Semantic Tunneling & Containment Safety Fuse

Test Cases:
  CASE_1: Standard Regime Rejection (Radical cross-domain candidate below baseline threshold)
  CASE_2: Exploration Zone Attenuation (Captures candidate as EXPLORATORY_CANDIDATE)
  CASE_3: Containment Safety Fuse (Zero impact on K_qual and K_quant during candidate stage)
  CASE_4: Semantic Tunneling Multi-Hop Validation (Multi-premise chain with intermediate lemmas)
  CASE_5: Full Epistemic Promotion & Crystallization (REINFORCED_SYNTHETIC_LINK, K_qual >= 0.85)
  CASE_6: False Breakthrough Containment & Burning (Adversarially refuted exploratory candidate pruned with zero K_qual pollution)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_semantic_tunneling.py
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
# Setup Base Domains: Quantum Mechanics <-> Macroeconomics
# =========================================================================
# Domain A: Quantum Mechanics
qm1 = make_anchor("qm1", "Квантовая запутанность обеспечивает мгновенную нелокальную корреляцию состояний частиц.", epi=0.92)
qm2 = make_anchor("qm2", "Теорема Белла математически доказывает отсутствие локального скрытого реализма.", epi=0.90)
qm_edge = make_core_edge("qm1", "qm2")

# Domain B: Market Macroeconomics
econ1 = make_anchor("econ1", "Каскадная корреляция рыночных активов создает системный риск финансовой сети.", epi=0.90)
econ2 = make_anchor("econ2", "Теория арбитражного ценообразования связывает нелокальные риски портфелей.", epi=0.88)
econ_edge = make_core_edge("econ1", "econ2")

graph_expl = ICGGraph(
    document_id="doc_tunneling",
    nodes=[qm1, qm2, econ1, econ2],
    edges=[qm_edge, econ_edge],
)

top_expl = harvester.topology_analyzer.analyze_topology(graph_expl)
dom_qm = next(d for d in top_expl.domains if "qm1" in d.member_node_ids)
dom_econ = next(d for d in top_expl.domains if "econ1" in d.member_node_ids)


# =========================================================================
# CASE 1: Standard Regime Rejection
# =========================================================================
print("\n═══ CASE 1: Standard Regime Rejection ═══")
# In standard regime (strict threshold 0.65), radical cross-domain bridge is rejected
standard_proposals = harvester.discover_cross_domain_bridges(graph_expl, min_resonance=0.65)
print(f"  [DEBUG] Standard Proposals Count: {len(standard_proposals)}")
check("CASE_1.a Standard regime rejects radical bridge (<0.65 resonance)", len(standard_proposals) == 0, f"proposals={len(standard_proposals)}")


# =========================================================================
# CASE 2: Exploration Zone Attenuation & Candidate Discovery
# =========================================================================
print("\n═══ CASE 2: Exploration Zone Attenuation & Candidate Discovery ═══")
# Activate exploration zone with 25% threshold attenuation
harvester.activate_exploration_zone(graph_expl, [dom_qm.domain_id, dom_econ.domain_id], attenuation_rate=0.25)

expl_proposals = harvester.discover_exploratory_tunnels(
    graph=graph_expl,
    exploration_domain_ids=[dom_qm.domain_id, dom_econ.domain_id],
    attenuation_rate=0.25,
    min_tunnel_potential=0.45,
)

print(f"  [DEBUG] Exploratory Proposals Count: {len(expl_proposals)}")
for p in expl_proposals:
    print(f"    Candidate: {p.source_node_id} <-> {p.target_node_id}, Res={p.resonance_score:.4f}, TunnelPot={p.tunneling_potential:.4f}, IsExpl={p.is_exploratory}")

check("CASE_2.a Exploration Zone discovers latent candidate bridge", len(expl_proposals) >= 1, f"count={len(expl_proposals)}")
top_candidate = expl_proposals[0] if expl_proposals else None
check("CASE_2.b Candidate flagged is_exploratory = True", top_candidate is not None and top_candidate.is_exploratory is True, "is_exploratory=True")


# =========================================================================
# CASE 3: Containment Safety Fuse Verification
# =========================================================================
print("\n═══ CASE 3: Containment Safety Fuse Verification ═══")
score_pre_install = harvester.compute_synthesis_coefficient(graph_expl)

# Install candidate into graph under Containment Fuse
if top_candidate:
    candidate_edge = harvester.install_exploratory_candidate(graph_expl, top_candidate)
    check("CASE_3.a Edge installed with status EXPLORATORY_CANDIDATE",
          candidate_edge.status == EdgeStatus.EXPLORATORY_CANDIDATE,
          f"status={candidate_edge.status}")

score_post_install = harvester.compute_synthesis_coefficient(graph_expl)
print(f"  [DEBUG] Pre-Install K_qual: {score_pre_install.k_qual:.4f}, Post-Install K_qual: {score_post_install.k_qual:.4f}")
check("CASE_3.b Containment Fuse: 0% pollution of K_qual while candidate is unverified",
      score_post_install.k_qual == score_pre_install.k_qual,
      f"post={score_post_install.k_qual} == pre={score_pre_install.k_qual}")
check("CASE_3.c Containment Fuse: 0% unearned inflation of active bridges count",
      score_post_install.active_bridges_count == score_pre_install.active_bridges_count,
      f"active_bridges={score_post_install.active_bridges_count}")


# =========================================================================
# CASE 4 & 5: Semantic Tunneling Multi-Hop Validation & Crystallization
# =========================================================================
print("\n═══ CASE 4 & 5: Semantic Tunneling Multi-Hop Validation & Crystallization ═══")
if top_candidate:
    intermediate_lemmas = [
        "Нелокальные корреляции в сложных графах описываются единым матричным формализмом спектральной плотности связей.",
        "Корреляционные матрицы активов математически изоморфны матрицам плотности квантовых ансамблей."
    ]

    resolving_evidence = (
        "Квантовая запутанность и каскадная корреляция рыночных активов изоморфны на уровне "
        "спектральной теории графов, отражая нелокальное распространение взаимной информации."
    )

    tunneling_ok = harvester.execute_semantic_tunneling_validation(
        graph=graph_expl,
        bridge=top_candidate,
        intermediary_lemmas=intermediate_lemmas,
        resolving_evidence=resolving_evidence,
        confidence_score=0.92,
    )

    print(f"  [DEBUG] Semantic Tunneling Result: {tunneling_ok}, State: {top_candidate.reinforcement_state}")
    check("CASE_4.a Multi-Hop Tunneling validation successfully completed", tunneling_ok is True, "Tunneling OK")
    check("CASE_4.b Bridge upgraded to REINFORCED", top_candidate.reinforcement_state == "REINFORCED", f"state={top_candidate.reinforcement_state}")
    check("CASE_4.c Intermediate lemma trajectory recorded in tunneling_hops",
          len(top_candidate.tunneling_hops) == 2,
          f"hops={len(top_candidate.tunneling_hops)}")

    score_crystallized = harvester.compute_synthesis_coefficient(graph_expl)
    print(f"  [DEBUG] Crystallized K_qual: {score_crystallized.k_qual:.4f}, K_composite: {score_crystallized.k_composite:.4f}")
    check("CASE_5.a Post-Tunneling High Epistemic Quality K_qual achieved (>=0.85)",
          score_crystallized.k_qual >= 0.85,
          f"k_qual={score_crystallized.k_qual:.4f}")


# =========================================================================
# CASE 6: False Breakthrough Containment & Burning (Aris Requirement #4)
# =========================================================================
print("\n═══ CASE 6: False Breakthrough Containment & Burning ═══")
# Inject a fake radical candidate with high TopoSim but contradictory physics
fake_candidate = ProposedCrossDomainBridge(
    source_node_id=qm2.id,
    target_node_id=econ2.id,
    source_domain_id=dom_qm.domain_id,
    target_domain_id=dom_econ.domain_id,
    semantic_similarity=0.45,
    topological_isomorphism=1.0,
    resonance_score=0.40,
    proposed_hypothesis="Теорема Белла доказывает локальный детерминизм рыночных котировок.",
    is_exploratory=True,
    tunneling_potential=0.60,
)

# Install fake candidate under containment
harvester.install_exploratory_candidate(graph_expl, fake_candidate)

# Attempt validation with contradictory assertion
fake_resolving = "Теорема Белла утверждает строгий локальный детерминизм и отвергает квантовую нелокальность."
fake_tunnel_ok = harvester.execute_semantic_tunneling_validation(
    graph=graph_expl,
    bridge=fake_candidate,
    intermediary_lemmas=["Псевдонаучная аналогия о детерминизме."],
    resolving_evidence=fake_resolving,
    confidence_score=0.90,
)

print(f"  [DEBUG] Fake Breakthrough Validation: {fake_tunnel_ok}, State: {fake_candidate.reinforcement_state}")
check("CASE_6.a Fake Breakthrough rejected by adversarial counter-refutation", fake_tunnel_ok is False, "Refuted OK")
check("CASE_6.b Fake candidate edge burned and pruned from graph edges",
      not any(e.status == EdgeStatus.EXPLORATORY_CANDIDATE and e.edge_id.endswith(fake_candidate.bridge_id) for e in graph_expl.edges),
      "Edge burned from graph")

score_post_fake = harvester.compute_synthesis_coefficient(graph_expl)
check("CASE_6.c Core K_qual preserved 100% intact after fake breakthrough attack",
      score_post_fake.k_qual == score_crystallized.k_qual,
      f"post_fake={score_post_fake.k_qual:.4f} == clean={score_crystallized.k_qual:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №16 Semantic Tunneling: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Dynamic Heuristic Exploration & Semantic Tunneling OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
