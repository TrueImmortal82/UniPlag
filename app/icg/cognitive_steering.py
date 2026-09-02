"""
Cognitive Steering & Resource Allocation Engine (app/icg/cognitive_steering.py)
Aris Directive #12: Cognitive Steering & Attention Management

Implements:
  1. Priority Matrix: Allocates attention based on topological zone weight:
       - PARADOX_CORE: 1.00 (Maximum cognitive return, dialectical synthesis)
       - TURBULENCE_ZONE: 0.70 (Contradiction resolution & stabilization)
       - EMERGING_FRONTIER: 0.50 (Frontier expansion & crystallization)
       - COGNITIVE_WASTELAND: 0.40 (Void settlement / inquiry generation)
       - CRYSTALLIZED_KNOWLEDGE: 0.05 + dynamic background monitoring
  2. Anti-Obsession Damping: Damping multiplier prevents infinite loops in contested paradoxes.
  3. Action Selection Rules: Maps entropy/connectivity to explicit steering actions.
  4. Dynamic Compute Allocation: Proportional allocation prioritizing paradoxical crucible (~85-95%).
  5. Feedback Loop & Phase Transition: Executes synthesis and verifies phase transition to crystal.
"""

from __future__ import annotations

import math
from typing import List, Dict, Optional, Any

from app.icg.models import (
    ICGGraph, DomainZoneType, DomainStabilityState, CognitiveDomain,
    SteeringAction, SteeringTarget, SteeringReport, ProposedResolution,
)
from app.icg.topology import TopologyAnalyzer
from app.icg.synthesis_loop import SynthesisLoopEngine

# ─────────────────────────────────────────────────────────────────────────────
# Configuration (Aris Directive #12 — no magic numbers in code)
# ─────────────────────────────────────────────────────────────────────────────

ZONE_WEIGHTS: Dict[DomainZoneType, float] = {
    DomainZoneType.PARADOX_CORE: 1.00,
    DomainZoneType.TURBULENCE_ZONE: 0.70,
    DomainZoneType.EMERGING_FRONTIER: 0.50,
    DomainZoneType.COGNITIVE_WASTELAND: 0.40,
    DomainZoneType.CRYSTALLIZED_KNOWLEDGE: 0.05,
}

DAMPING_RATE: float = 0.25             # Damping factor per iteration: 1 / (1 + 0.25 * n)
CRYSTAL_BACKGROUND_FLOOR: float = 0.05  # Base background monitoring for archives


class CognitiveSteeringEngine:
    """
    Steers computational attention across the cognitive topology of ICG v0.4.
    Directs deep synthesis loops into high-friction paradox cores while preserving archives.
    """

    def __init__(
        self,
        topology_analyzer: Optional[TopologyAnalyzer] = None,
        synthesis_engine: Optional[SynthesisLoopEngine] = None,
    ):
        self.topology_analyzer = topology_analyzer or TopologyAnalyzer()
        self.synthesis_engine = synthesis_engine or SynthesisLoopEngine()
        self.domain_iteration_counts: Dict[str, int] = {}

    def get_high_value_targets(
        self,
        graph: ICGGraph,
        total_compute_budget: int = 1000,
        limit: int = 10,
    ) -> SteeringReport:
        """
        Evaluate cognitive topology and generate a prioritized resource allocation plan.
        """
        top_report = self.topology_analyzer.analyze_topology(graph)
        if not top_report.domains:
            return SteeringReport(total_compute_budget=total_compute_budget)

        raw_targets: List[SteeringTarget] = []
        domain_entropy_map: Dict[str, float] = {
            sn.domain_id: sn.internal_entropy for sn in top_report.super_nodes
        }

        # Step 1: Calculate Target Value for each domain
        for domain in top_report.domains:
            zone = domain.zone_type
            base_zone_weight = ZONE_WEIGHTS.get(zone, 0.50)

            # Dynamic background monitoring for Crystallized Knowledge (Aris Requirement #2)
            if zone == DomainZoneType.CRYSTALLIZED_KNOWLEDGE:
                # Active boundary friction gives slight boost to monitoring weight
                zone_weight = base_zone_weight + min(0.10, 0.02 * len(domain.member_node_ids))
            else:
                zone_weight = base_zone_weight

            entropy = domain_entropy_map.get(domain.domain_id, 0.05)
            connectivity = max(1, len(domain.member_node_ids))
            contra_factor = 1.0 + domain.contradiction_ratio

            raw_value = zone_weight * (1.0 + entropy) * math.log(2.0 + connectivity) * contra_factor

            # Anti-Obsession Damping (Aris Requirement #1)
            iter_count = self.domain_iteration_counts.get(domain.domain_id, 0)
            damped_value = raw_value / (1.0 + DAMPING_RATE * iter_count)
            damped_value = round(max(0.01, damped_value), 4)

            # Explicit Action Selection (Aris Requirement #3)
            action = self._select_recommended_action(domain)

            target = SteeringTarget(
                target_id=domain.domain_id,
                label=domain.label,
                zone_type=zone,
                value_score=damped_value,
                recommended_action=action,
                iteration_count=iter_count,
                member_node_ids=domain.member_node_ids,
            )
            raw_targets.append(target)

        # Step 2: Proportional Resource Allocation
        total_value = sum(t.value_score for t in raw_targets) or 1.0
        for t in raw_targets:
            pct = round(100.0 * (t.value_score / total_value), 2)
            t.budget_percentage = pct
            t.allocated_compute_units = int(round(total_compute_budget * (pct / 100.0)))

        # Sort by value_score descending
        raw_targets.sort(key=lambda t: t.value_score, reverse=True)
        ranked_targets = raw_targets[:limit]

        # Calculate macro allocation metrics
        paradox_alloc = sum(
            t.budget_percentage for t in ranked_targets if t.zone_type == DomainZoneType.PARADOX_CORE
        )
        archive_alloc = sum(
            t.budget_percentage for t in ranked_targets if t.zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE
        )

        top_id = ranked_targets[0].target_id if ranked_targets else None

        return SteeringReport(
            targets=ranked_targets,
            total_compute_budget=total_compute_budget,
            top_priority_target_id=top_id,
            paradox_allocation_percentage=round(paradox_alloc, 2),
            archive_allocation_percentage=round(archive_alloc, 2),
            feedback_recomputed=False,
        )

    def _select_recommended_action(self, domain: CognitiveDomain) -> SteeringAction:
        """
        Action selection rules mapping topological features to cognitive operations (Aris Directive #12).
        """
        if domain.zone_type == DomainZoneType.PARADOX_CORE:
            return SteeringAction.SYNTHESIS_CRUCIBLE
        if domain.zone_type == DomainZoneType.TURBULENCE_ZONE:
            return SteeringAction.CONTRADICTION_RESOLUTION
        if domain.zone_type == DomainZoneType.COGNITIVE_WASTELAND or domain.void_count >= 1:
            return SteeringAction.VOID_SETTLEMENT
        if domain.zone_type == DomainZoneType.EMERGING_FRONTIER:
            return SteeringAction.FRONTIER_EXPANSION
        return SteeringAction.ARCHIVE_MONITORING

    def execute_steered_synthesis(
        self,
        graph: ICGGraph,
        target_domain_id: str,
        void_id: Optional[str] = None,
        resolving_evidence: Optional[str] = None,
        confidence_score: float = 0.90,
    ) -> Dict[str, Any]:
        """
        Execute directed synthesis on a target domain and verify the resulting phase transition (Feedback Loop).
        """
        # Increment iteration count for damping tracking
        self.domain_iteration_counts[target_domain_id] = (
            self.domain_iteration_counts.get(target_domain_id, 0) + 1
        )

        proposal_res = None
        if void_id and resolving_evidence:
            proposal_res = self.synthesis_engine.propose_void_resolution(
                graph=graph,
                void_id=void_id,
                evidence_text=resolving_evidence,
                confidence_score=confidence_score,
            )

        # Feedback Loop: Recompute topology to verify phase transition
        post_top = self.topology_analyzer.analyze_topology(graph)
        
        # Check if the domain was crystallized
        is_crystallized = any(
            d.zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE for d in post_top.domains
        )

        return {
            "target_domain_id": target_domain_id,
            "iteration": self.domain_iteration_counts[target_domain_id],
            "proposal_status": proposal_res.status.value if proposal_res else "N/A",
            "post_crystallized_count": post_top.crystallized_count,
            "post_turbulence_count": post_top.turbulence_count,
            "post_paradox_core_count": post_top.paradox_core_count,
            "is_crystallized": is_crystallized,
            "message": f"Steered synthesis completed on {target_domain_id}. Crystallized domains: {post_top.crystallized_count}",
        }


__all__ = [
    "CognitiveSteeringEngine",
    "ZONE_WEIGHTS",
    "DAMPING_RATE",
    "CRYSTAL_BACKGROUND_FLOOR",
]
