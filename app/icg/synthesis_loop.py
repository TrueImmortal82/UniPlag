"""
Epistemic Synthesis Loop & Verification Engine (app/icg/synthesis_loop.py)
Aris Directive #10: Synthesis of Hypotheses & Verification Loop

Implements the complete lifecycle:
  Inquiry → ProposedResolution → Dual-Pole NLI Verification → Graph Evolution / Conflict Handling

Key Architectural Components (per Aris):
  1. The Blind Spot Defense: Active entailment threshold (anti-neutrality / anti-silence).
  2. Structured Conflict Diagnostics: ConflictDetail object with pole, reason, score, snippets.
  3. Actionable Conflict Resolution Strategies: REVISE_POLES, TRIANGULATE_THIRD_POLE, ARBITRATE_EXTERNAL_SOURCE.
  4. Local Radius Heatmap Update: recompute_neighbor_tensions(max_hop_radius=2).
  5. Immutable Search & Learning History: proposals_history in CognitiveVoidMetadata.
"""

from __future__ import annotations

import time
import re
from typing import Optional, Dict, Any, List

from app.icg.models import (
    ICGGraph, NodeType, VoidStatus, VoidType,
    ResolutionStatus, ConflictResolutionStrategy,
    ConflictDetail, ProposedResolution,
)
from app.icg.nli_verifier import NLIVerifier
from app.icg.graph_builder import ICGGraphBuilder

# ─────────────────────────────────────────────────────────────────────────────
# Verification Thresholds (Aris Directive #10 / #13 — no magic numbers in code)
# ─────────────────────────────────────────────────────────────────────────────

T_CONTRADICTION_THRESHOLD: float = 0.50     # Contradiction above this triggers CONFLICT
T_MIN_PRIMARY_ENTAILMENT: float = 0.35      # Primary pole entailment requirement
T_MIN_BRIDGING_ENTAILMENT: float = 0.18     # Minimum dual-pole bridging entailment requirement
T_MIN_SUMMED_ENTAILMENT: float = 0.50       # Summed dual-pole entailment requirement
T_MIN_CONFIDENCE_SCORE: float = 0.70        # Minimum external confidence required for resolution


class SynthesisLoopEngine:
    """
    Orchestrates the Synthesis Loop for Cognitive Voids.
    Evaluates external evidence proposals against both anchor poles using dual-pole NLI,
    enforcing anti-hallucination, anti-noise, and conflict defense.
    """

    def __init__(
        self,
        nli_verifier: Optional[NLIVerifier] = None,
        graph_builder: Optional[ICGGraphBuilder] = None,
    ):
        self.nli = nli_verifier or NLIVerifier()
        self.graph_builder = graph_builder or ICGGraphBuilder()

    def propose_void_resolution(
        self,
        graph: ICGGraph,
        void_id: str,
        evidence_text: str,
        evidence_source: str = "",
        confidence_score: float = 0.85,
    ) -> ProposedResolution:
        """
        Submit and verify a proposed resolution for a Cognitive Void.

        Lifecycle:
          1. Locate OPEN void in graph
          2. Dual-pole NLI evaluation (Pole A vs Evidence, Pole B vs Evidence)
          3. Check Contradiction → status CONFLICT + structured ConflictDetail + Strategy
          4. Check Blind Spot Defense (Entailment Gate) → status REJECTED_UNSUPPORTED
          5. Check Confidence Gate (< 0.70) → status REJECTED_UNSUPPORTED
          6. Success → status VERIFIED + call graph_builder.resolve_cognitive_void() + history update

        Returns:
            ProposedResolution containing verification status and complete audit trail.
        """
        # Step 1: Locate void node
        void_node = next((n for n in graph.nodes if n.id == void_id), None)
        if void_node is None:
            return ProposedResolution(
                void_id=void_id,
                evidence_text=evidence_text,
                evidence_source=evidence_source,
                confidence_score=confidence_score,
                status=ResolutionStatus.REJECTED_UNSUPPORTED,
                created_at_epoch=time.time(),
            )

        void_meta = (void_node.synthesis_metadata.cognitive_void
                     if void_node.synthesis_metadata else None)
        if void_meta is None or void_meta.void_status == VoidStatus.RESOLVED:
            return ProposedResolution(
                void_id=void_id,
                evidence_text=evidence_text,
                evidence_source=evidence_source,
                confidence_score=confidence_score,
                status=ResolutionStatus.REJECTED_UNSUPPORTED,
                created_at_epoch=time.time(),
            )

        pole_a_id = void_meta.pole_a_anchor_id
        pole_b_id = void_meta.pole_b_anchor_id

        node_map = {n.id: n for n in graph.nodes}
        pole_a_node = node_map.get(pole_a_id)
        pole_b_node = node_map.get(pole_b_id)

        pole_a_text = pole_a_node.span.raw_text if pole_a_node else ""
        pole_b_text = pole_b_node.span.raw_text if pole_b_node else ""

        # Step 2: Dual-Pole NLI Verification
        res_a = self.nli.hybrid.verify_pair(pole_a_text, evidence_text)
        res_b = self.nli.hybrid.verify_pair(pole_b_text, evidence_text)

        entail_a = round(res_a.entailment_score, 4)
        contra_a = round(res_a.contradiction_score, 4)
        entail_b = round(res_b.entailment_score, 4)
        contra_b = round(res_b.contradiction_score, 4)

        proposal = ProposedResolution(
            void_id=void_id,
            evidence_text=evidence_text,
            evidence_source=evidence_source,
            confidence_score=confidence_score,
            status=ResolutionStatus.PROPOSED,
            pole_a_entailment=entail_a,
            pole_a_contradiction=contra_a,
            pole_b_entailment=entail_b,
            pole_b_contradiction=contra_b,
            created_at_epoch=time.time(),
        )

        # Step 3: Conflict Detection (Aris Requirement #2 & #4)
        if contra_a >= T_CONTRADICTION_THRESHOLD or contra_b >= T_CONTRADICTION_THRESHOLD:
            pole_label = "A" if contra_a >= contra_b else "B"
            conflicting_pole_id = pole_a_id if pole_label == "A" else pole_b_id
            conflicting_pole_text = pole_a_text if pole_label == "A" else pole_b_text
            contra_score = max(contra_a, contra_b)
            entail_score = entail_a if pole_label == "A" else entail_b

            # Select strategy based on conflict topology
            if contra_a >= T_CONTRADICTION_THRESHOLD and contra_b >= T_CONTRADICTION_THRESHOLD:
                strategy = ConflictResolutionStrategy.REVISE_POLES
            elif min(entail_a, entail_b) > 0.20:
                strategy = ConflictResolutionStrategy.TRIANGULATE_THIRD_POLE
            else:
                strategy = ConflictResolutionStrategy.ARBITRATE_EXTERNAL_SOURCE

            proposal.status = ResolutionStatus.CONFLICT
            proposal.conflict_strategy = strategy
            proposal.conflict_details = ConflictDetail(
                pole_id=conflicting_pole_id,
                pole_label=pole_label,
                contradiction_score=contra_score,
                entailment_score=entail_score,
                snippet_pole=conflicting_pole_text[:120],
                snippet_evidence=evidence_text[:120],
                reason=f"Evidence directly contradicts Pole {pole_label} (Contradiction={contra_score:.2f})",
            )

            # Update void classification to reflect dialectical friction
            void_meta.void_type = VoidType.CONTRADICTORY_SILENCE
            void_meta.proposals_history.append(proposal)
            return proposal

        # Step 4: The Blind Spot & Mimicry Defense (Aris Requirement #1 / #13)
        primary_entailment = max(entail_a, entail_b)
        bridging_entailment = min(entail_a, entail_b)
        summed_entailment = entail_a + entail_b

        # Causal / relational predicate requirement for genuine synthesis
        synthesis_predicate_pattern = (
            r"\b(объединя\w*|балансир\w*|интегрир\w*|компенсир\w*|связыва\w*|регулир\w*|"
            r"синхронизир\w*|поддержива\w*|нейтрализ\w*|согласу\w*|достига\w*|обеспечива\w*|"
            r"сочета\w*|гармонизир\w*|трансформиру\w*|разреша\w*|сдержива\w*|устраня\w*|"
            r"bridge\w*|reconcil\w*|integrat\w*|balanc\w*|coupl\w*|regulat\w*|align\w*|"
            r"combin\w*|resolv\w*|harmoniz\w*|mitigat\w*|stabiliz\w*)\b"
        )
        has_causal_predicate = bool(re.search(synthesis_predicate_pattern, evidence_text.lower()))

        # Check for evasive pseudo-synthesis templates (Aris Directive #13)
        evasive_pattern = (
            r"(рассматривает\s+гипотетическ|иллюстрирует\s+вероятностн|структурирует\s+феноменолог|"
            r"формируя\s+абстрактн|мета-дискурсивн|коррелирует\s+в\s+первом\s+приближении)"
        )
        is_evasive = bool(re.search(evasive_pattern, evidence_text.lower()))

        if (
            primary_entailment < T_MIN_PRIMARY_ENTAILMENT
            or bridging_entailment < T_MIN_BRIDGING_ENTAILMENT
            or summed_entailment < T_MIN_SUMMED_ENTAILMENT
            or not has_causal_predicate
            or is_evasive
        ):
            proposal.status = ResolutionStatus.REJECTED_UNSUPPORTED
            void_meta.proposals_history.append(proposal)
            return proposal

        # Step 5: Confidence Gate
        if confidence_score < T_MIN_CONFIDENCE_SCORE:
            proposal.status = ResolutionStatus.REJECTED_UNSUPPORTED
            void_meta.proposals_history.append(proposal)
            return proposal

        # Step 6: Verification Passed → Graph Evolution
        proposal.status = ResolutionStatus.VERIFIED
        resolve_res = self.graph_builder.resolve_cognitive_void(
            graph=graph,
            void_id=void_id,
            evidence_text=evidence_text,
            confidence_score=confidence_score,
        )

        proposal.created_edge_id = resolve_res.get("new_edge_id")
        void_meta.proposals_history.append(proposal)
        return proposal


__all__ = [
    "SynthesisLoopEngine",
    "T_CONTRADICTION_THRESHOLD",
    "T_MIN_PRIMARY_ENTAILMENT",
    "T_MIN_SUMMED_ENTAILMENT",
    "T_MIN_CONFIDENCE_SCORE",
]
