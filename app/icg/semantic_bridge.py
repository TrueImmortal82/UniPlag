"""
Cross-Domain Semantic Bridge & Harvesting Engine (app/icg/semantic_bridge.py)
Aris Directive #14: Dynamic Knowledge Harvesting & Cross-Domain Synthesis

Implements:
  1. Latent Cross-Domain Bridge Discovery: Scans pairs across distinct cognitive domains.
  2. Structural Neighborhood Isomorphism: Checks local degree/topological symmetry in Resonance.
  3. Vectorized Synthesis Coefficient (K_synth): Quantifies both structural quantity and epistemic quality.
  4. Bridge Validation & Graph Consolidation: Upgrades verified cross-domain hypotheses into active bridges.
"""

from __future__ import annotations

import math
import time
from typing import List, Dict, Tuple, Optional, Set

from app.icg.models import (
    ICGGraph, ClaimNode, NodeType, EdgeEvidence, RelationType, EdgeStatus,
    EdgeWeightDetails, DomainZoneType, ProposedCrossDomainBridge,
    SynthesisVectorScore, CrossDomainDiscoveryReport, VoidStatus,
)
from app.icg.topology import TopologyAnalyzer
from app.icg.nli_verifier import NLIVerifier


class SemanticBridgeHarvester:
    """
    Scans the cognitive topology of ICG v0.4 to discover, rank, and validate
    latent structural isomorphisms and synthetic bridges across disparate knowledge domains.
    """

    def __init__(
        self,
        topology_analyzer: Optional[TopologyAnalyzer] = None,
        nli_verifier: Optional[NLIVerifier] = None,
    ):
        self.topology_analyzer = topology_analyzer or TopologyAnalyzer()
        self.nli_verifier = nli_verifier or NLIVerifier()

    def discover_cross_domain_bridges(
        self,
        graph: ICGGraph,
        min_resonance: float = 0.55,
        max_proposals: int = 10,
    ) -> List[ProposedCrossDomainBridge]:
        """
        Identify latent isomorphic connections between nodes belonging to distinct cognitive domains (Aris Directive #14).
        """
        top_report = self.topology_analyzer.analyze_topology(graph)
        if len(top_report.domains) < 2:
            return []

        # Map each node to its domain and zone
        node_to_domain: Dict[str, str] = {}
        node_to_zone: Dict[str, DomainZoneType] = {}
        for d in top_report.domains:
            for nid in d.member_node_ids:
                node_to_domain[nid] = d.domain_id
                node_to_zone[nid] = d.zone_type

        # Node degree mapping for topological isomorphism
        node_degree: Dict[str, int] = {}
        for n in graph.nodes:
            deg = sum(
                1 for e in graph.edges
                if (e.source_node_id == n.id or e.target_node_id == n.id)
                and e.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK)
            )
            node_degree[n.id] = deg

        # Filter candidate anchor nodes (exclude wasteland)
        eligible_nodes = [
            n for n in graph.nodes
            if n.id in node_to_domain
            and node_to_zone.get(n.id) != DomainZoneType.COGNITIVE_WASTELAND
            and n.type != NodeType.COGNITIVE_VOID
        ]

        proposals: List[ProposedCrossDomainBridge] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for i, u in enumerate(eligible_nodes):
            dom_u = node_to_domain[u.id]
            for j in range(i + 1, len(eligible_nodes)):
                v = eligible_nodes[j]
                dom_v = node_to_domain[v.id]

                # Strict requirement: Must cross domain boundaries
                if dom_u == dom_v:
                    continue

                pair_key = (min(u.id, v.id), max(u.id, v.id))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # 1. Semantic Similarity
                nli_res = self.nli_verifier.hybrid.verify_pair(u.span.raw_text, v.span.raw_text)
                sim = max(nli_res.entailment_score, 0.05)

                # Also try dense cosine similarity if available
                if self.nli_verifier.hybrid.dense_model is not None:
                    try:
                        from sentence_transformers.util import cos_sim
                        emb_u = self.nli_verifier.hybrid.dense_model.encode(u.span.raw_text, show_progress_bar=False)
                        emb_v = self.nli_verifier.hybrid.dense_model.encode(v.span.raw_text, show_progress_bar=False)
                        dense_val = float(cos_sim(emb_u, emb_v))
                        sim = max(sim, dense_val)
                    except Exception:
                        pass

                # 2. Neighborhood Topological Isomorphism (Aris Requirement #1)
                deg_u = node_degree.get(u.id, 0)
                deg_v = node_degree.get(v.id, 0)
                deg_diff = abs(deg_u - deg_v)
                deg_sum = max(1, deg_u + deg_v)
                topo_sim = round(1.0 - (deg_diff / deg_sum), 4)

                # 3. Latent Cross-Domain Resonance Formula (Aris Requirement #1)
                min_epi = min(u.epistemic_confidence, v.epistemic_confidence)
                resonance = sim * min_epi * (0.70 + 0.30 * topo_sim)
                resonance = round(resonance, 4)

                # Adaptive Threshold Check (Aris Directive #15)
                dom_u_obj = next((d for d in top_report.domains if d.domain_id == dom_u), None)
                dom_v_obj = next((d for d in top_report.domains if d.domain_id == dom_v), None)
                adaptive_thresh = (
                    self.compute_adaptive_threshold(dom_u_obj, dom_v_obj, graph, base_threshold=min_resonance)
                    if dom_u_obj and dom_v_obj else min_resonance
                )

                if resonance >= adaptive_thresh:
                    u_snippet = u.span.raw_text[:60]
                    v_snippet = v.span.raw_text[:60]
                    hypo = f"Функциональный изоморфизм между «{u_snippet}» и «{v_snippet}» обеспечивает междоменную передачу принципов управления."

                    bridge = ProposedCrossDomainBridge(
                        source_node_id=u.id,
                        target_node_id=v.id,
                        source_domain_id=dom_u,
                        target_domain_id=dom_v,
                        semantic_similarity=round(sim, 4),
                        topological_isomorphism=topo_sim,
                        resonance_score=resonance,
                        proposed_hypothesis=hypo,
                        is_validated=False,
                    )
                    proposals.append(bridge)

        # Sort proposals by resonance descending
        proposals.sort(key=lambda b: b.resonance_score, reverse=True)
        return proposals[:max_proposals]

    def compute_adaptive_threshold(
        self,
        domain_u: CognitiveDomain,
        domain_v: CognitiveDomain,
        graph: ICGGraph,
        base_threshold: float = 0.50,
    ) -> float:
        """
        Adaptive Resonance Threshold based on domain contradiction ratio and wasteland density (Aris Directive #15).
        """
        # Wasteland penalty: ratio of open voids and low-confidence nodes to total domain members
        waste_u = (
            domain_u.void_count + sum(
                1 for nid in domain_u.member_node_ids
                if any(n.id == nid and n.epistemic_confidence < 0.50 for n in graph.nodes)
            )
        ) / max(1, len(domain_u.member_node_ids))

        waste_v = (
            domain_v.void_count + sum(
                1 for nid in domain_v.member_node_ids
                if any(n.id == nid and n.epistemic_confidence < 0.50 for n in graph.nodes)
            )
        ) / max(1, len(domain_v.member_node_ids))

        contra_factor = (domain_u.contradiction_ratio + domain_v.contradiction_ratio) / 2.0
        waste_factor = (waste_u + waste_v) / 2.0

        adaptive_thresh = base_threshold + 0.15 * contra_factor + 0.15 * waste_factor
        return round(min(0.90, adaptive_thresh), 4)

    def adversarial_counter_refutation(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
        hypothesis_text: str,
    ) -> Tuple[float, Optional[str], Optional[str]]:
        """
        Sweeps 1-2 hop neighborhood nodes in source and target domains to find opposing axioms (Aris Directive #15).
        Returns: (max_effective_refutation, refuting_node_id, refuting_text)
        """
        candidate_node_ids = set()
        top_report = self.topology_analyzer.analyze_topology(graph)
        dom_src_id = next((d.domain_id for d in top_report.domains if bridge.source_node_id in d.member_node_ids), None)
        dom_tgt_id = next((d.domain_id for d in top_report.domains if bridge.target_node_id in d.member_node_ids), None)
        target_dom_ids = {d_id for d_id in (dom_src_id, dom_tgt_id, bridge.source_domain_id, bridge.target_domain_id) if d_id}

        for d in top_report.domains:
            if d.domain_id in target_dom_ids:
                candidate_node_ids.update(d.member_node_ids)

        max_contra = 0.0
        refuting_id = None
        refuting_text = None

        for nid in candidate_node_ids:
            if nid in (bridge.source_node_id, bridge.target_node_id):
                continue
            node = next((n for n in graph.nodes if n.id == nid), None)
            if not node or node.type == NodeType.COGNITIVE_VOID:
                continue

            nli_check = self.nli_verifier.hybrid.verify_pair(node.span.raw_text, hypothesis_text)
            # Effective refutation weighted by the neighbor's epistemic confidence (Aris requirement)
            effective_contra = nli_check.contradiction_score * node.epistemic_confidence

            if effective_contra > max_contra:
                max_contra = effective_contra
                refuting_id = node.id
                refuting_text = node.span.raw_text

        return round(max_contra, 4), refuting_id, refuting_text

    def validate_and_install_bridge(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
        resolving_evidence: str,
        confidence_score: float = 0.90,
    ) -> bool:
        """
        Validates cross-domain hypothesis via dual-pole verification, runs adversarial counter-refutation,
        and installs reinforced or speculative synthetic link (Aris Directive #15).
        """
        # Fetch nodes
        u = next((n for n in graph.nodes if n.id == bridge.source_node_id), None)
        v = next((n for n in graph.nodes if n.id == bridge.target_node_id), None)
        if not u or not v:
            return False

        # Verify evidence against both nodes
        nli_u = self.nli_verifier.hybrid.verify_pair(u.span.raw_text, resolving_evidence)
        nli_v = self.nli_verifier.hybrid.verify_pair(v.span.raw_text, resolving_evidence)

        if nli_u.contradiction_score > 0.40 or nli_v.contradiction_score > 0.40:
            return False

        if nli_u.entailment_score < 0.30 or nli_v.entailment_score < 0.30:
            return False

        # Step 2: Adversarial Counter-Refutation Check (Aris Directive #15)
        ref_pressure, ref_node_id, ref_evidence_text = self.adversarial_counter_refutation(
            graph=graph,
            bridge=bridge,
            hypothesis_text=resolving_evidence,
        )
        bridge.refutation_pressure = ref_pressure
        bridge.refutation_node_id = ref_node_id
        bridge.refutation_evidence_text = ref_evidence_text

        base_edge_weight = round(min(0.95, (bridge.resonance_score + confidence_score) / 2.0), 3)

        if ref_pressure <= 0.20:
            # Reinforced Bridge
            final_status = EdgeStatus.REINFORCED_SYNTHETIC_LINK
            final_weight = min(0.98, round(base_edge_weight * 1.25, 3))
            bridge.reinforcement_state = "REINFORCED"
        elif ref_pressure > 0.40:
            # Speculative Bridge (flagged with refutation trace)
            final_status = EdgeStatus.SPECULATIVE_LINK
            final_weight = round(base_edge_weight * 0.50, 3)
            bridge.reinforcement_state = "SPECULATIVE"
        else:
            final_status = EdgeStatus.SYNTHETIC_LINK
            final_weight = base_edge_weight
            bridge.reinforcement_state = "UNVERIFIED"

        edge = EdgeEvidence(
            edge_id=f"synth_{bridge.bridge_id}",
            source_node_id=bridge.source_node_id,
            target_node_id=bridge.target_node_id,
            relation_type=RelationType.SYNTHESIZES,
            weight=final_weight,
            status=final_status,
            weight_details=EdgeWeightDetails(
                final_weight=final_weight,
                status=final_status,
                resonance_amplifier=bridge.resonance_score,
            )
        )
        graph.edges.append(edge)
        bridge.is_validated = True
        return True

    def activate_exploration_zone(
        self,
        graph: ICGGraph,
        target_domain_ids: List[str],
        attenuation_rate: float = 0.25,
    ) -> None:
        """
        Activates Heuristic Exploration Zone on specified domains with configurable attenuation rate (Aris Directive #16).
        """
        top_report = self.topology_analyzer.analyze_topology(graph)
        for d in top_report.domains:
            if d.domain_id in target_domain_ids:
                d.zone_type = DomainZoneType.EXPLORATION_ZONE

    def discover_exploratory_tunnels(
        self,
        graph: ICGGraph,
        exploration_domain_ids: Optional[List[str]] = None,
        attenuation_rate: float = 0.25,
        min_tunnel_potential: float = 0.50,
        max_proposals: int = 10,
    ) -> List[ProposedCrossDomainBridge]:
        """
        Discovers latent structural connections across exploration zones using attenuated resonance and topological tunneling (Aris Directive #16).
        """
        top_report = self.topology_analyzer.analyze_topology(graph)
        if len(top_report.domains) < 2:
            return []

        expl_doms = set(exploration_domain_ids or [
            d.domain_id for d in top_report.domains if d.zone_type == DomainZoneType.EXPLORATION_ZONE
        ])

        # Map each node to its domain and zone
        node_to_domain: Dict[str, str] = {}
        for d in top_report.domains:
            for nid in d.member_node_ids:
                node_to_domain[nid] = d.domain_id

        # Node degree mapping
        node_degree: Dict[str, int] = {}
        for n in graph.nodes:
            deg = sum(
                1 for e in graph.edges
                if (e.source_node_id == n.id or e.target_node_id == n.id)
                and e.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK, EdgeStatus.REINFORCED_SYNTHETIC_LINK)
            )
            node_degree[n.id] = deg

        eligible_nodes = [
            n for n in graph.nodes
            if n.id in node_to_domain and n.type != NodeType.COGNITIVE_VOID
        ]

        proposals: List[ProposedCrossDomainBridge] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for i, u in enumerate(eligible_nodes):
            dom_u = node_to_domain[u.id]
            for j in range(i + 1, len(eligible_nodes)):
                v = eligible_nodes[j]
                dom_v = node_to_domain[v.id]

                if dom_u == dom_v:
                    continue

                pair_key = (min(u.id, v.id), max(u.id, v.id))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Semantic & dense similarity
                nli_res = self.nli_verifier.hybrid.verify_pair(u.span.raw_text, v.span.raw_text)
                sim = max(nli_res.entailment_score, 0.05)

                if self.nli_verifier.hybrid.dense_model is not None:
                    try:
                        from sentence_transformers.util import cos_sim
                        emb_u = self.nli_verifier.hybrid.dense_model.encode(u.span.raw_text, show_progress_bar=False)
                        emb_v = self.nli_verifier.hybrid.dense_model.encode(v.span.raw_text, show_progress_bar=False)
                        dense_val = float(cos_sim(emb_u, emb_v))
                        sim = max(sim, dense_val)
                    except Exception:
                        pass

                deg_u = node_degree.get(u.id, 0)
                deg_v = node_degree.get(v.id, 0)
                topo_sim = round(1.0 - (abs(deg_u - deg_v) / max(1, deg_u + deg_v)), 4)

                min_epi = min(u.epistemic_confidence, v.epistemic_confidence)
                resonance = round(sim * min_epi * (0.70 + 0.30 * topo_sim), 4)

                dom_u_obj = next((d for d in top_report.domains if d.domain_id == dom_u), None)
                dom_v_obj = next((d for d in top_report.domains if d.domain_id == dom_v), None)
                base_adaptive = (
                    self.compute_adaptive_threshold(dom_u_obj, dom_v_obj, graph, base_threshold=0.50)
                    if dom_u_obj and dom_v_obj else 0.50
                )

                # Attenuated threshold for exploration domains (Aris Requirement #1)
                is_expl_pair = (dom_u in expl_doms or dom_v in expl_doms)
                effective_thresh = (
                    round(base_adaptive * (1.0 - attenuation_rate), 4)
                    if is_expl_pair else base_adaptive
                )

                tunneling_potential = round(topo_sim * min_epi * (sim + 0.20), 4)

                if resonance >= effective_thresh and tunneling_potential >= min_tunnel_potential:
                    u_snippet = u.span.raw_text[:60]
                    v_snippet = v.span.raw_text[:60]
                    hypo = f"Эвристический туннель между «{u_snippet}» и «{v_snippet}» активирован для форсированной верификации."

                    bridge = ProposedCrossDomainBridge(
                        source_node_id=u.id,
                        target_node_id=v.id,
                        source_domain_id=dom_u,
                        target_domain_id=dom_v,
                        semantic_similarity=round(sim, 4),
                        topological_isomorphism=topo_sim,
                        resonance_score=resonance,
                        proposed_hypothesis=hypo,
                        is_validated=False,
                        is_exploratory=is_expl_pair,
                        tunneling_potential=tunneling_potential,
                    )
                    proposals.append(bridge)

        proposals.sort(key=lambda b: b.tunneling_potential, reverse=True)
        return proposals[:max_proposals]

    def install_exploratory_candidate(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
    ) -> EdgeEvidence:
        """
        Installs an exploratory bridge under the Containment Fuse (Aris Directive #16).
        """
        edge = EdgeEvidence(
            edge_id=f"expl_{bridge.bridge_id}",
            source_node_id=bridge.source_node_id,
            target_node_id=bridge.target_node_id,
            relation_type=RelationType.SYNTHESIZES,
            weight=0.30,
            status=EdgeStatus.EXPLORATORY_CANDIDATE,
            weight_details=EdgeWeightDetails(
                final_weight=0.30,
                status=EdgeStatus.EXPLORATORY_CANDIDATE,
                resonance_amplifier=bridge.resonance_score,
            )
        )
        graph.edges.append(edge)
        return edge

    def execute_semantic_tunneling_validation(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
        intermediary_lemmas: List[str],
        resolving_evidence: str,
        confidence_score: float = 0.90,
    ) -> bool:
        """
        Executes forced multi-hop validation and adversarial counter-refutation on an exploratory bridge (Aris Directive #16).
        """
        bridge.tunneling_hops = intermediary_lemmas

        u = next((n for n in graph.nodes if n.id == bridge.source_node_id), None)
        v = next((n for n in graph.nodes if n.id == bridge.target_node_id), None)
        if not u or not v:
            return False

        # Multi-premise validation: Source + Intermediate Lemmas + Resolving Evidence -> Target
        all_premises = [u.span.raw_text] + intermediary_lemmas
        nli_forward = self.nli_verifier.hybrid.verify_multi_premise(all_premises, resolving_evidence)
        nli_backward = self.nli_verifier.hybrid.verify_pair(v.span.raw_text, resolving_evidence)

        if nli_forward.contradiction_score > 0.40 or nli_backward.contradiction_score > 0.40:
            self._prune_exploratory_edge(graph, bridge.bridge_id)
            return False

        if nli_forward.entailment_score < 0.25 or nli_backward.entailment_score < 0.25:
            self._prune_exploratory_edge(graph, bridge.bridge_id)
            return False

        # Step 2: Adversarial Counter-Refutation (Directive #15)
        ref_pressure, ref_node_id, ref_evidence_text = self.adversarial_counter_refutation(
            graph=graph,
            bridge=bridge,
            hypothesis_text=resolving_evidence,
        )
        bridge.refutation_pressure = ref_pressure
        bridge.refutation_node_id = ref_node_id
        bridge.refutation_evidence_text = ref_evidence_text

        if ref_pressure <= 0.20:
            # Successfully Tunnelled & Reinforced
            self._prune_exploratory_edge(graph, bridge.bridge_id)
            final_weight = min(0.98, round(((bridge.resonance_score + confidence_score) / 2.0) * 1.25, 3))
            reinforced_edge = EdgeEvidence(
                edge_id=f"synth_{bridge.bridge_id}",
                source_node_id=bridge.source_node_id,
                target_node_id=bridge.target_node_id,
                relation_type=RelationType.SYNTHESIZES,
                weight=final_weight,
                status=EdgeStatus.REINFORCED_SYNTHETIC_LINK,
                weight_details=EdgeWeightDetails(
                    final_weight=final_weight,
                    status=EdgeStatus.REINFORCED_SYNTHETIC_LINK,
                    resonance_amplifier=bridge.resonance_score,
                )
            )
            graph.edges.append(reinforced_edge)
            bridge.reinforcement_state = "REINFORCED"
            bridge.is_validated = True
            return True
        else:
            # Refuted in adversarial sweep: Burn candidate
            self._prune_exploratory_edge(graph, bridge.bridge_id)
            bridge.reinforcement_state = "REFUTED_EXPLORATORY"
            return False

    def _prune_exploratory_edge(self, graph: ICGGraph, bridge_id: str) -> None:
        """Helper to remove temporary exploratory candidate edges."""
        graph.edges = [
            e for e in graph.edges
            if not (e.status == EdgeStatus.EXPLORATORY_CANDIDATE and e.edge_id.endswith(bridge_id))
        ]

    def prune_stale_exploratory_candidates(
        self,
        graph: ICGGraph,
        max_age_seconds: float = 3600.0,
    ) -> int:
        """
        Burns unvalidated exploratory candidate edges older than max_age_seconds (Aris Directive #16).
        """
        now = time.time()
        initial_count = len(graph.edges)
        graph.edges = [
            e for e in graph.edges
            if not (e.status == EdgeStatus.EXPLORATORY_CANDIDATE and (now - getattr(e, "created_at_epoch", now)) > max_age_seconds)
        ]
        return initial_count - len(graph.edges)

    def compute_synthesis_coefficient(self, graph: ICGGraph) -> SynthesisVectorScore:
        """
        Vectorized Synthesis Coefficient K_synth with Containment Fuse (Aris Directive #15 & #16).
        EXPLORATORY_CANDIDATE edges are strictly excluded from K_synth.
        """
        top_report = self.topology_analyzer.analyze_topology(graph)
        n_domains = max(1, len(top_report.domains))
        n_nodes = max(1, len(graph.nodes))

        # Node to domain map
        node_to_domain: Dict[str, str] = {}
        for d in top_report.domains:
            for nid in d.member_node_ids:
                node_to_domain[nid] = d.domain_id

        # Categorize cross-domain edges (CONTAINMENT FUSE: EXPLORATORY_CANDIDATE is completely omitted)
        cross_edges = [
            e for e in graph.edges
            if e.status in (EdgeStatus.SYNTHETIC_LINK, EdgeStatus.REINFORCED_SYNTHETIC_LINK, EdgeStatus.SPECULATIVE_LINK)
        ]
        reinforced_edges = [e for e in cross_edges if e.status == EdgeStatus.REINFORCED_SYNTHETIC_LINK]
        speculative_edges = [e for e in cross_edges if e.status == EdgeStatus.SPECULATIVE_LINK]

        active_bridges = len([e for e in cross_edges if e.status != EdgeStatus.SPECULATIVE_LINK])
        open_voids = sum(
            1 for n in graph.nodes
            if n.type == NodeType.COGNITIVE_VOID
            and n.synthesis_metadata and n.synthesis_metadata.cognitive_void
            and n.synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN
        )

        # 1. Quantitative Synthesis Metric: Structural cross-pollination
        void_penalty = 1.0 - (open_voids / n_nodes)
        non_waste_domains = [d for d in top_report.domains if d.zone_type != DomainZoneType.COGNITIVE_WASTELAND]
        domain_norm = max(1, len(non_waste_domains)) if non_waste_domains else n_domains
        k_quant = (active_bridges / domain_norm) * max(0.10, void_penalty)
        k_quant = round(min(1.0, k_quant), 4)

        # 2. Qualitative Synthesis Metric: Epistemic weight & stability with Speculative Penalty
        valid_eval_edges = reinforced_edges if reinforced_edges else [e for e in cross_edges if e.status == EdgeStatus.SYNTHETIC_LINK]
        avg_bridge_weight = (
            sum(e.weight for e in valid_eval_edges) / max(1, len(valid_eval_edges))
            if valid_eval_edges else 0.0
        )
        avg_domain_stability = (
            sum(d.stability_score for d in non_waste_domains) / max(1, len(non_waste_domains))
            if non_waste_domains else 0.50
        )
        
        # Speculative links penalize K_qual (Aris Requirement #3)
        speculative_penalty = 0.20 * len(speculative_edges)
        raw_k_qual = avg_bridge_weight * avg_domain_stability
        k_qual = max(0.01, round(raw_k_qual - speculative_penalty, 4)) if valid_eval_edges else 0.05

        # 3. Composite Metric
        k_composite = round(math.sqrt(k_quant * k_qual), 4)

        return SynthesisVectorScore(
            k_quant=k_quant,
            k_qual=k_qual,
            k_composite=k_composite,
            active_bridges_count=active_bridges,
            open_voids_count=open_voids,
            epistemic_stability=round(avg_domain_stability, 4),
        )


__all__ = ["SemanticBridgeHarvester"]
