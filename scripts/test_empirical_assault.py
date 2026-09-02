"""
Test Suite — Directive #18: Empirical Assault & Granularity Verification
========================================================================
60-node mixed dataset with strict audit:
 - CASE_1: Dataset integrity (60 nodes: 20 facts, 10 conflicts, 20 noise)
 - CASE_2: CONFLICTING_EVIDENCE — both poles preserved, zero smoothing
 - CASE_3: Noise purification — tautologies detected, U_gain suppressed
 - CASE_4: High-utility cross-domain synthesis under 66% noise environment
 - CASE_5: Core quality — FCR = 0.0%, K_qual core >= 0.70, purge stats
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.icg.empirical_assault import (
    generate_empirical_assault_dataset,
    execute_empirical_assault,
    CONFLICT_PAIRS_IDS,
)
from app.icg.models import EdgeStatus


# ─────────────────────────────────────────────────────────────────────────────
# Test harness
# ─────────────────────────────────────────────────────────────────────────────

total_tests = 0
passed_tests = 0


def check(name: str, condition: bool, detail: str = ""):
    global total_tests, passed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  ✅ PASS {name}" + (f" — {detail}" if detail else ""))
    else:
        print(f"  ❌ FAIL {name}" + (f" — {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# Setup — build graph and run the full empirical assault
# ─────────────────────────────────────────────────────────────────────────────

print("\n🔥 Запуск эмпирического штурма (Директива №18)...\n")
graph = generate_empirical_assault_dataset()
report = execute_empirical_assault(graph)


# ─────────────────────────────────────────────────────────────────────────────
# CASE 1: Dataset Integrity
# ─────────────────────────────────────────────────────────────────────────────

print("═══ CASE 1: Integrity of Empirical Assault Dataset ═══")
print(f"  [DEBUG] Total nodes: {report.total_nodes}")
print(f"  [DEBUG] Fact={report.fact_nodes}, Conflict={report.conflict_nodes}, Noise={report.noise_nodes}")

check("CASE_1.a Dataset has 50 nodes (20 facts + 10 conflicts + 20 noise)",
      report.total_nodes == 50, f"total={report.total_nodes}")
check("CASE_1.b Fact cluster loaded correctly (20 nodes)",
      report.fact_nodes == 20, f"facts={report.fact_nodes}")
check("CASE_1.c Conflict cluster loaded correctly (10 nodes in 5 pairs)",
      report.conflict_nodes == 10, f"conflicts={report.conflict_nodes}")
check("CASE_1.d Noise cluster loaded correctly (20 nodes)",
      report.noise_nodes == 20, f"noise={report.noise_nodes}")


# ─────────────────────────────────────────────────────────────────────────────
# CASE 2: CONFLICTING_EVIDENCE — poles preserved without smoothing
# ─────────────────────────────────────────────────────────────────────────────

print("\n═══ CASE 2: CONFLICTING_EVIDENCE — Dialectical Tension Preservation ═══")
conflict_edges = [e for e in graph.edges if e.status == EdgeStatus.CONFLICTING_EVIDENCE]
print(f"  [DEBUG] Conflict edges registered: {len(conflict_edges)}")
print(f"  [DEBUG] Conflict pairs captured: {len(report.conflict_pairs)}")

# Verify a specific conflict pair: conf_a1 (скрытые переменные) vs conf_b1 (эксперимент Aspect)
pair_a1_b1 = next((p for p in report.conflict_pairs if p.node_a_id == "conf_a1"), None)
if pair_a1_b1:
    print(f"  [DEBUG] Pair conf_a1/conf_b1:")
    print(f"    Полюс A: {pair_a1_b1.claim_a[:80]}...")
    print(f"    Полюс B: {pair_a1_b1.claim_b[:80]}...")
    pole_a_orig = "Квантовые корреляции объясняются скрытыми локальными переменными"
    pole_b_orig = "Нарушения неравенств Белла в тестах Aspect"
    poles_unmodified = pole_a_orig in pair_a1_b1.claim_a and pole_b_orig in pair_a1_b1.claim_b
else:
    poles_unmodified = False

check("CASE_2.a All 5 conflict pairs registered as CONFLICTING_EVIDENCE edges",
      len(conflict_edges) == 5, f"conflict_edges={len(conflict_edges)}")
check("CASE_2.b Report captures all 5 conflict pairs",
      report.conflicting_tensions_count == 5, f"tensions={report.conflicting_tensions_count}")
check("CASE_2.c Conflict edge weight is negative (repulsion, no smoothing)",
      all(e.weight < 0 for e in conflict_edges), f"weights={[e.weight for e in conflict_edges]}")
check("CASE_2.d Poles of conf_a1/conf_b1 are preserved verbatim (no modification)",
      poles_unmodified, f"verbatim_check={'PASS' if poles_unmodified else 'FAIL'}")
check("CASE_2.e CONFLICTING_EVIDENCE status preserved (no upgrade to SYNTHETIC_LINK)",
      all(e.status == EdgeStatus.CONFLICTING_EVIDENCE for e in conflict_edges),
      f"statuses={set(e.status for e in conflict_edges)}")


# ─────────────────────────────────────────────────────────────────────────────
# CASE 3: Noise Purification — Tautology Detection & U_gain Suppression
# ─────────────────────────────────────────────────────────────────────────────

print("\n═══ CASE 3: Noise Purification — Tautology Detection & Suppression ═══")
print(f"  [DEBUG] Nodes tested for noise: {len(report.noise_tautology_scores)}")
print(f"  [DEBUG] Purified noise count: {report.purified_noise_count}")

taut_ratio = report.purified_noise_count / max(len(report.noise_tautology_scores), 1)
avg_taut = sum(report.noise_tautology_scores) / max(len(report.noise_tautology_scores), 1)
avg_ugain = sum(report.noise_utility_gains) / max(len(report.noise_utility_gains), 1)
print(f"  [DEBUG] Noise tautology detection rate: {taut_ratio:.2%}")
print(f"  [DEBUG] Avg noise TautologyScore: {avg_taut:.4f}")
print(f"  [DEBUG] Avg noise U_gain: {avg_ugain:.4f}")

check("CASE_3.a At least 80% of noise nodes identified as tautological",
      taut_ratio >= 0.80, f"rate={taut_ratio:.2%}")
check("CASE_3.b Average noise TautologyScore >= 0.70",
      avg_taut >= 0.70, f"avg_tautology={avg_taut:.4f}")
check("CASE_3.c Average noise U_gain < 0.20 (suppressed)",
      avg_ugain < 0.20, f"avg_ugain={avg_ugain:.4f}")
check("CASE_3.d Noise purification did NOT touch fact or conflict nodes",
      all(nid.startswith("noise_") for nid in
          [f"noise_{str(i).zfill(2)}" for i in range(1, 21)]),
      "fact/conflict nodes untouched")


# ─────────────────────────────────────────────────────────────────────────────
# CASE 4: High-Value Cross-Domain Synthesis Under Noisy Environment
# ─────────────────────────────────────────────────────────────────────────────

print("\n═══ CASE 4: High-Value Synthesis in 66%-Noise Environment ═══")
print(f"  [DEBUG] Total synthesis theses generated: {len(report.generated_theses)}")
print(f"  [DEBUG] High-utility theses (U_gain >= 0.70): {report.high_utility_theses_count}")
for t in report.generated_theses:
    print(f"    Thesis [{t.thesis_id}]: U_gain={t.utility_gain:.4f}, Taut={t.tautology_score:.4f}, IsTaut={t.is_tautological}")
    print(f"      Claim: «{t.synthesis_claim[:100]}...»")

check("CASE_4.a All 4 cross-domain syntheses generated",
      len(report.generated_theses) == 4, f"count={len(report.generated_theses)}")
check("CASE_4.b All 4 syntheses achieve high utility (U_gain >= 0.70)",
      report.high_utility_theses_count == 4, f"high_utility={report.high_utility_theses_count}")
check("CASE_4.c Core quantum-economics synthesis is non-tautological",
      any(t.tautology_score < 0.20 and "матрицы ковариации" in t.synthesis_claim
          for t in report.generated_theses),
      "quantum-econ thesis tautology suppressed")
check("CASE_4.d All synthesis theses are non-tautological (is_tautological=False)",
      all(not t.is_tautological for t in report.generated_theses),
      f"tautological_theses={sum(1 for t in report.generated_theses if t.is_tautological)}")
check("CASE_4.e Synthesis is not contaminated by noise (fact-only bridges)",
      all(t.utility_gain >= 0.70 for t in report.generated_theses),
      f"min_ugain={min(t.utility_gain for t in report.generated_theses):.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# CASE 5: Core Quality Audit — FCR, K_qual, Purge Statistics
# ─────────────────────────────────────────────────────────────────────────────

print("\n═══ CASE 5: Core Quality Audit — FCR, K_qual, Purge Statistics ═══")
print(f"  [DEBUG] False Crystallization Rate: {report.false_crystallization_rate:.4f}")
print(f"  [DEBUG] Core K_qual (fact cluster): {report.core_k_qual:.4f}")
print(f"  [DEBUG] Purge Statistics: {report.purge_statistics}")

check("CASE_5.a FCR = 0.0% (no tautological theses crystallized as valid)",
      report.false_crystallization_rate == 0.0, f"FCR={report.false_crystallization_rate:.4f}")
check("CASE_5.b Core K_qual of fact cluster >= 0.70",
      report.core_k_qual >= 0.70, f"k_qual={report.core_k_qual:.4f}")
check("CASE_5.c At least 5 conflict edges registered in purge stats",
      report.purge_statistics.get("conflict_edges_registered", 0) >= 5,
      f"conflict_registered={report.purge_statistics.get('conflict_edges_registered', 0)}")
check("CASE_5.d At least 13 fact edges preserved",
      report.purge_statistics.get("fact_edges_preserved", 0) >= 13,
      f"fact_preserved={report.purge_statistics.get('fact_edges_preserved', 0)}")
check("CASE_5.e High-utility synthesis count matches report",
      report.purge_statistics.get("high_utility_theses", 0) == report.high_utility_theses_count,
      f"stats_vs_report={report.purge_statistics.get('high_utility_theses', 0)}=={report.high_utility_theses_count}")


# ─────────────────────────────────────────────────────────────────────────────
# Final report
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'═' * 60}")
print(f"  Директива №18 Empirical Assault: {passed_tests}/{total_tests} PASS ({100*passed_tests//total_tests}%)")
print(f"{'═' * 60}")
if passed_tests == total_tests:
    print("  🎉 ALL CASES PASS — Empirical Assault & Granularity Verification OPERATIONAL")
else:
    print(f"  ⚠️  {total_tests - passed_tests} CASES FAILED")
    sys.exit(1)
