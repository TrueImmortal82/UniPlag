"""
test_cross_domain_harvesting.py — Aris Directive #14 Test Suite
Dynamic Knowledge Harvesting, Cross-Domain Synthesis & Synthesis Coefficient

Test Cases:
  CASE_1: Batch Ingestion & Immune Staging Layer (Quarantine of noise, promotion of clean claims)
  CASE_2: Cross-Domain Semantic Bridge Discovery (Event Sourcing <-> Action Potential Propagation)
  CASE_3: Bridge Validation & Synthetic Link Installation (Upgrades hypothesis to active edge)
  CASE_4: Vectorized Synthesis Coefficient K_synth (Quantity vs Quality metrics)

Usage:
  cd "e:/AI detector/uniplag"
  .venv/Scripts/python.exe scripts/test_cross_domain_harvesting.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.icg.models import (
    NodeType, EdgeStatus, RelationType, VoidType, VoidStatus,
    ContributionClass, ClaimNode, EdgeEvidence, TextSpan,
    SynthesisMetadata, CognitiveVoidMetadata, InquiryResult,
    ICGGraph, MetricsSummary, EdgeWeightDetails,
    DomainZoneType, DomainStabilityState,
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
ingestion = IngestionPipeline()

# =========================================================================
# CASE 1: Batch Ingestion & Immune Staging Layer
# =========================================================================
print("\n═══ CASE 1: Batch Ingestion & Immune Staging Layer ═══")
graph_empty = ICGGraph(document_id="doc_ingest", nodes=[], edges=[])

raw_batch = [
    # Domain A: Software Architecture / Event Sourcing (Clean)
    {"id": "sa1", "text": "Асинхронные шины событий и брокеры сообщений обеспечивают слабую связность микросервисов.", "epistemic_confidence": 0.90},
    {"id": "sa2", "text": "Паттерн Event Sourcing сохраняет полную хронологию мутаций состояния системы.", "epistemic_confidence": 0.88},
    {"id": "sa3", "text": "Распределенная репликация логов предотвращает потерю данных при сбоях узлов.", "epistemic_confidence": 0.86},

    # Domain B: Biological Neural Networks (Clean)
    {"id": "bio1", "text": "Распространение спайковых потенциалов действия передает дискретные импульсы возбуждения по аксонам.", "epistemic_confidence": 0.90},
    {"id": "bio2", "text": "Синаптическая пластичность Хебба адаптирует силу синаптической связи на основе частоты импульсов.", "epistemic_confidence": 0.88},
    {"id": "bio3", "text": "Пластичность нейронных ансамблей обеспечивает консолидацию долговременной памяти.", "epistemic_confidence": 0.86},

    # Injected Noise: Mimicry & Evasive Fluff
    {"id": "noise1", "text": "Исследование рассматривает гипотетический синтез через микросервисы и нейроны, формируя абстрактный контекст.", "epistemic_confidence": 0.80},
    {"id": "noise2", "text": "Исследование иллюстрирует вероятностную взаимосвязь с явлением шины событий и памяти.", "epistemic_confidence": 0.75},
]

ingest_res = ingestion.ingest_batch_claims(graph_empty, raw_batch)
print(f"  [DEBUG] Ingestion Summary: Submitted={ingest_res.total_submitted}, Promoted={ingest_res.promoted_to_active}, Quarantined={ingest_res.quarantined_to_wasteland}")

check("CASE_1.a Total submitted count tracked", ingest_res.total_submitted == 8, f"total={ingest_res.total_submitted}")
check("CASE_1.b Clean claims promoted to active graph (6/6)", ingest_res.promoted_to_active == 6, f"promoted={ingest_res.promoted_to_active}")
check("CASE_1.c Evasive noise quarantined to wasteland (2/2)", ingest_res.quarantined_to_wasteland == 2, f"quarantined={ingest_res.quarantined_to_wasteland}")
check("CASE_1.d Active graph contains exactly 8 nodes (6 active + 2 quarantined)", len(graph_empty.nodes) == 8, f"nodes={len(graph_empty.nodes)}")


# =========================================================================
# CASE 2: Cross-Domain Semantic Bridge Discovery
# =========================================================================
print("\n═══ CASE 2: Cross-Domain Semantic Bridge Discovery ═══")
# Establish intra-domain core edges
graph_empty.edges.extend([
    make_core_edge("sa1", "sa2"),
    make_core_edge("sa2", "sa3"),
    make_core_edge("sa3", "sa1"),
    make_core_edge("bio1", "bio2"),
    make_core_edge("bio2", "bio3"),
    make_core_edge("bio3", "bio1"),
])

# Scan for cross-domain bridges
proposed_bridges = harvester.discover_cross_domain_bridges(graph_empty, min_resonance=0.30, max_proposals=5)
print(f"  [DEBUG] Discovered Bridges: {len(proposed_bridges)}")
for b in proposed_bridges:
    print(f"    Bridge {b.source_node_id} <-> {b.target_node_id}: Sim={b.semantic_similarity:.3f}, TopoSim={b.topological_isomorphism:.3f}, Resonance={b.resonance_score:.4f}")

check("CASE_2.a Latent cross-domain bridges discovered", len(proposed_bridges) >= 1, f"count={len(proposed_bridges)}")

# Verify the structural isomorphism between Event Sourcing / Asynch Bus and Action Potentials / Synaptic Plasticity
top_bridge = proposed_bridges[0] if proposed_bridges else None
check("CASE_2.b Top bridge connects Domain A and Domain B", 
      top_bridge is not None and top_bridge.source_domain_id != top_bridge.target_domain_id,
      f"src_dom={top_bridge.source_domain_id if top_bridge else None} != tgt_dom={top_bridge.target_domain_id if top_bridge else None}")
check("CASE_2.c Topological isomorphism factor computed",
      top_bridge is not None and top_bridge.topological_isomorphism >= 0.80,
      f"topo_sim={top_bridge.topological_isomorphism if top_bridge else None}")


# =========================================================================
# CASE 3: Bridge Validation & Synthetic Link Installation
# =========================================================================
print("\n═══ CASE 3: Bridge Validation & Synthetic Link Installation ═══")
if top_bridge:
    resolving_evidence = (
        "Асинхронные шины событий в распределенных системах функционально соответствуют "
        "распространению спайковых потенциалов действия в нейронных сетях, обеспечивая "
        "дискретную импульсную передачу данных без жесткой временной блокировки узлов."
    )

    validation_ok = harvester.validate_and_install_bridge(
        graph=graph_empty,
        bridge=top_bridge,
        resolving_evidence=resolving_evidence,
        confidence_score=0.92,
    )
    print(f"  [DEBUG] Bridge Validation Result: {validation_ok}")

    check("CASE_3.a Bridge successfully validated via dual-pole NLI", validation_ok is True, "Validation successful")
    check("CASE_3.b Bridge status marked is_validated = True", top_bridge.is_validated is True, "is_validated=True")
    
    synth_edge = next((e for e in graph_empty.edges if e.status in (EdgeStatus.SYNTHETIC_LINK, EdgeStatus.REINFORCED_SYNTHETIC_LINK)), None)
    check("CASE_3.c Synthetic link installed in active graph edges", synth_edge is not None, f"edge_id={synth_edge.edge_id if synth_edge else None}")
    if synth_edge:
        check("CASE_3.d Synthetic link carries high weight (>=0.70)", synth_edge.weight >= 0.70, f"weight={synth_edge.weight}")


# =========================================================================
# CASE 4: Vectorized Synthesis Coefficient K_synth
# =========================================================================
print("\n═══ CASE 4: Vectorized Synthesis Coefficient K_synth ═══")
vector_score = harvester.compute_synthesis_coefficient(graph_empty)
print(f"  [DEBUG] Synthesis Coefficient: K_quant={vector_score.k_quant:.4f}, K_qual={vector_score.k_qual:.4f}, K_composite={vector_score.k_composite:.4f}")
print(f"    Active Bridges: {vector_score.active_bridges_count}, Open Voids: {vector_score.open_voids_count}, Stability: {vector_score.epistemic_stability:.4f}")

check("CASE_4.a Quantitative metric K_quant computed", vector_score.k_quant > 0.0, f"k_quant={vector_score.k_quant:.4f}")
check("CASE_4.b Qualitative metric K_qual computed", vector_score.k_qual > 0.0, f"k_qual={vector_score.k_qual:.4f}")
check("CASE_4.c Composite metric K_composite >= 0.30", vector_score.k_composite >= 0.30, f"k_comp={vector_score.k_composite:.4f}")
check("CASE_4.d Active bridges count registered (>=1)", vector_score.active_bridges_count >= 1, f"bridges={vector_score.active_bridges_count}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'═'*60}")
print(f"  Директива №14 Cross-Domain Synthesis: {passed}/{total} PASS ({100*passed//total}%)")
print(f"{'═'*60}")

if passed == total:
    print("  🎉 ALL CASES PASS — Dynamic Knowledge Harvesting & Cross-Domain Synthesis OPERATIONAL")
else:
    print(f"  ⚠️  {total - passed} test(s) failed — review above")

sys.exit(0 if passed == total else 1)
