"""
Cognitive Topology & Dynamic Clustering Engine (app/icg/topology.py)
Aris Directive #11: Cognitive Topology & Dynamic Clustering

Implements:
  1. Community Detection: Modularity & Connected-Component grouping of reasoning nodes into Cognitive Domains.
  2. Non-linear Domain Stability: Exponential penalty for contradiction ratio and void friction.
  3. Epistemic Zone Classification:
       - CRYSTALLIZED_KNOWLEDGE: High density, low conflict, zero voids, stable crystal.
       - TURBULENCE_ZONE: High conflict ratio (>= 0.25), unstable turbulence.
       - PARADOX_CORE: High conflict + high density + high epistemic confidence (dialectical crucible).
       - COGNITIVE_WASTELAND: Sparse density, high unresolved void count.
       - EMERGING_FRONTIER: Transitional active reasoning zone.
  4. Domain Abstraction (MacroSuperNode):
       - Computes internal_entropy (variance/information dispersion of member confidence).
       - Preserves strongest boundary bridge edge weights across domains.
  5. Overheated Domain Alerts: Actionable triggers for contradiction resolution.
"""

from __future__ import annotations

import math
import uuid
from typing import List, Dict, Set, Tuple, Optional

from app.icg.models import (
    ICGGraph, NodeType, EdgeStatus, VoidStatus,
    DomainZoneType, DomainStabilityState, CognitiveDomain,
    MacroSuperNode, TopologyReport,
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration (Aris Directive #11 — no magic numbers in code)
# ─────────────────────────────────────────────────────────────────────────────

CONTRA_EXP_SCALE: float = 3.5           # Exponential multiplier for contradiction penalty
CONTRA_UNSTABLE_THRESHOLD: float = 0.25 # Contradiction ratio threshold for UNSTABLE status
MIN_CRYSTAL_DENSITY: float = 0.35       # Minimum internal density for CRYSTALLIZED_KNOWLEDGE
MIN_CRYSTAL_CONFIDENCE: float = 0.70    # Minimum average epistemic confidence for crystal
MAX_CRYSTAL_CONTRA: float = 0.10        # Maximum contradiction ratio tolerated in crystal


class TopologyAnalyzer:
    """
    Analyzes the macro-topological landscape of the Intellectual Contribution Graph.
    Partitions nodes into Cognitive Domains, evaluates epistemic stability,
    flags overheated paradox cores, and generates hierarchical Super-Nodes.
    """

    def analyze_topology(self, graph: ICGGraph) -> TopologyReport:
        """
        Execute full cognitive topological survey on the graph.
        """
        # Step 1: Filter real claim/anchor nodes (exclude meta-nodes from raw clustering)
        core_nodes = [
            n for n in graph.nodes
            if n.type not in (NodeType.COGNITIVE_VOID, NodeType.PARADOX_CONTAINER)
        ]
        if not core_nodes:
            return TopologyReport()

        core_node_ids = {n.id for n in core_nodes}
        node_map = {n.id: n for n in graph.nodes}

        # Step 2: Build Adjacency for Community Detection
        # Positive connections group nodes; Repulsion edges act as cluster boundaries
        adj: Dict[str, Set[str]] = {nid: set() for nid in core_node_ids}
        repulsion_pairs: Set[Tuple[str, str]] = set()

        for edge in graph.edges:
            src, tgt = edge.source_node_id, edge.target_node_id
            if src in core_node_ids and tgt in core_node_ids and src != tgt:
                if edge.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK):
                    adj[src].add(tgt)
                    adj[tgt].add(src)
                elif edge.status == EdgeStatus.REPULSION_BOUNDARY or edge.weight < -0.30:
                    repulsion_pairs.add((src, tgt))
                    repulsion_pairs.add((tgt, src))

        # Step 3: Graph Partitioning into Connected Components & Communities
        # (Separates distinct dense clusters even if linked by a sparse bridge edge)
        clusters = self._partition_communities(core_node_ids, adj, repulsion_pairs, node_map, graph.edges)

        # Step 4: Map Cognitive Voids to clusters
        open_voids = [
            n for n in graph.nodes
            if n.type == NodeType.COGNITIVE_VOID and
            n.synthesis_metadata and n.synthesis_metadata.cognitive_void and
            n.synthesis_metadata.cognitive_void.void_status == VoidStatus.OPEN
        ]

        domains: List[CognitiveDomain] = []
        node_to_domain_map: Dict[str, str] = {}

        for i, member_ids in enumerate(clusters):
            # Deterministic domain_id derived from member nodes
            import hashlib
            h = hashlib.md5("_".join(sorted(member_ids)).encode('utf-8')).hexdigest()[:8]
            domain_id = f"dom_{h}"
            for nid in member_ids:
                node_to_domain_map[nid] = domain_id

            member_set = set(member_ids)
            n_members = len(member_ids)

            # Internal positive core edges
            internal_core_edges = [
                e for e in graph.edges
                if e.source_node_id in member_set and e.target_node_id in member_set
                and e.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK)
            ]
            # Internal repulsion / conflict edges
            internal_repulsion_edges = [
                e for e in graph.edges
                if e.source_node_id in member_set and e.target_node_id in member_set
                and (e.status == EdgeStatus.REPULSION_BOUNDARY or e.weight < -0.30)
            ]

            # Internal open voids (where both poles are inside this cluster)
            internal_voids = [
                v for v in open_voids
                if v.synthesis_metadata.cognitive_void.pole_a_anchor_id in member_set
                and v.synthesis_metadata.cognitive_void.pole_b_anchor_id in member_set
            ]

            # Compute topological metrics
            max_possible_edges = n_members * (n_members - 1) if n_members > 1 else 1
            internal_density = round(min(1.0, (2.0 * len(internal_core_edges)) / max_possible_edges), 4)

            total_internal_interactions = len(internal_core_edges) + len(internal_repulsion_edges)
            contradiction_ratio = (
                round(len(internal_repulsion_edges) / max(1, total_internal_interactions), 4)
                if total_internal_interactions > 0 else 0.0
            )

            epistemic_scores = [node_map[nid].epistemic_confidence for nid in member_ids if nid in node_map]
            avg_epistemic = round(sum(epistemic_scores) / max(1, len(epistemic_scores)), 4)
            void_count = len(internal_voids)

            # Non-linear Stability Calculation (Aris Directive #11)
            base_stability = internal_density * avg_epistemic
            # Exponential penalty: if contradiction_ratio rises, penalty accelerates steeply
            exp_contra_penalty = min(1.0, math.expm1(CONTRA_EXP_SCALE * contradiction_ratio)) * 0.75
            void_penalty = min(0.35, 0.12 * void_count)
            raw_stability = base_stability - exp_contra_penalty - void_penalty
            stability_score = round(max(0.0, min(1.0, raw_stability)), 4)

            # Epistemic Zone Classification
            is_overheated = False
            contradiction_alert = False

            if contradiction_ratio >= CONTRA_UNSTABLE_THRESHOLD:
                is_overheated = True
                contradiction_alert = True
                if avg_epistemic >= MIN_CRYSTAL_CONFIDENCE and internal_density >= MIN_CRYSTAL_DENSITY:
                    zone_type = DomainZoneType.PARADOX_CORE
                else:
                    zone_type = DomainZoneType.TURBULENCE_ZONE
                stability_state = DomainStabilityState.UNSTABLE

            elif void_count >= 1 or internal_density < 0.20:
                zone_type = DomainZoneType.COGNITIVE_WASTELAND
                stability_state = DomainStabilityState.UNSTABLE

            elif (
                internal_density >= MIN_CRYSTAL_DENSITY
                and avg_epistemic >= MIN_CRYSTAL_CONFIDENCE
                and contradiction_ratio <= MAX_CRYSTAL_CONTRA
                and void_count == 0
            ):
                zone_type = DomainZoneType.CRYSTALLIZED_KNOWLEDGE
                stability_state = DomainStabilityState.STABLE

            else:
                zone_type = DomainZoneType.EMERGING_FRONTIER
                stability_state = (
                    DomainStabilityState.STABLE if stability_score >= 0.65
                    else (DomainStabilityState.UNSTABLE if stability_score < 0.35 else DomainStabilityState.TRANSITIONAL)
                )

            # Choose domain label from dominant anchor
            dominant_node = max(member_ids, key=lambda nid: node_map[nid].epistemic_confidence if nid in node_map else 0)
            dominant_text = node_map[dominant_node].span.raw_text[:35] if dominant_node in node_map else f"Domain {i+1}"
            label = f"{dominant_text}..."

            domain = CognitiveDomain(
                domain_id=domain_id,
                label=label,
                member_node_ids=member_ids,
                zone_type=zone_type,
                stability_state=stability_state,
                stability_score=stability_score,
                internal_density=internal_density,
                contradiction_ratio=contradiction_ratio,
                avg_epistemic_confidence=avg_epistemic,
                void_count=void_count,
                is_overheated=is_overheated,
                contradiction_alert_required=contradiction_alert,
            )
            domains.append(domain)

        # Step 5: Construct TopologyReport
        crystallized_count = sum(1 for d in domains if d.zone_type == DomainZoneType.CRYSTALLIZED_KNOWLEDGE)
        turbulence_count = sum(1 for d in domains if d.zone_type == DomainZoneType.TURBULENCE_ZONE)
        paradox_core_count = sum(1 for d in domains if d.zone_type == DomainZoneType.PARADOX_CORE)
        wasteland_count = sum(1 for d in domains if d.zone_type == DomainZoneType.COGNITIVE_WASTELAND)
        overheated = [d.domain_id for d in domains if d.is_overheated]

        # Generate SuperNodes for stable domains
        super_nodes = [self.abstract_domain(d, graph, node_to_domain_map) for d in domains if d.stability_state == DomainStabilityState.STABLE]

        return TopologyReport(
            domains=domains,
            crystallized_count=crystallized_count,
            turbulence_count=turbulence_count,
            paradox_core_count=paradox_core_count,
            wasteland_count=wasteland_count,
            overheated_domains=overheated,
            super_nodes=super_nodes,
            global_modularity_score=round(len(domains) / max(1, len(core_nodes)), 4),
        )

    def abstract_domain(
        self,
        domain: CognitiveDomain,
        graph: ICGGraph,
        node_to_domain_map: Dict[str, str],
    ) -> MacroSuperNode:
        """
        Collapse a CognitiveDomain into a single MacroSuperNode.
        Calculates internal_entropy and preserves strongest boundary weights (Aris Directive #11).
        """
        member_set = set(domain.member_node_ids)
        node_map = {n.id: n for n in graph.nodes}

        # Epistemic values of members
        conf_list = [node_map[nid].epistemic_confidence for nid in domain.member_node_ids if nid in node_map]
        mean_conf = sum(conf_list) / max(1, len(conf_list))

        # Internal Entropy (Variance of epistemic confidence across members)
        variance = sum((c - mean_conf) ** 2 for c in conf_list) / max(1, len(conf_list))
        internal_entropy = round(math.sqrt(variance), 4)

        # Boundary edges and strongest weights to other domains
        boundary_edge_count = 0
        strongest_weights: Dict[str, float] = {}

        for edge in graph.edges:
            src, tgt = edge.source_node_id, edge.target_node_id
            if (src in member_set and tgt not in member_set) or (tgt in member_set and src not in member_set):
                boundary_edge_count += 1
                other_node = tgt if src in member_set else src
                other_domain = node_to_domain_map.get(other_node, "external")
                current_max = strongest_weights.get(other_domain, 0.0)
                if edge.weight > current_max:
                    strongest_weights[other_domain] = round(edge.weight, 4)

        super_node = MacroSuperNode(
            domain_id=domain.domain_id,
            label=f"[SUPER-NODE] {domain.label}",
            aggregated_epistemic_confidence=round(mean_conf, 4),
            internal_entropy=internal_entropy,
            member_count=len(domain.member_node_ids),
            boundary_edge_count=boundary_edge_count,
            strongest_boundary_weights=strongest_weights,
            zone_type=domain.zone_type,
        )
        domain.super_node_id = super_node.super_node_id
        return super_node

    def _partition_communities(
        self,
        core_node_ids: Set[str],
        adj: Dict[str, Set[str]],
        repulsion_pairs: Set[Tuple[str, str]],
        node_map: Dict[str, ClaimNode],
        edges: List[EdgeEvidence],
    ) -> List[List[str]]:
        """
        Partitions core nodes into modular cognitive domains.
        Respects discipline domains and splits dense cores connected by sparse bridges.
        """
        visited: Set[str] = set()
        components: List[List[str]] = []

        for nid in core_node_ids:
            if nid not in visited:
                comp: List[str] = []
                queue = [nid]
                visited.add(nid)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited and (curr, neighbor) not in repulsion_pairs:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        final_clusters: List[List[str]] = []
        for comp in components:
            if len(comp) <= 3:
                final_clusters.append(comp)
                continue

            # Check if component has distinct explicit discipline domains
            domains_in_comp: Dict[str, List[str]] = {}
            for nid in comp:
                disc = getattr(node_map.get(nid), "discipline_domain", None) or "default"
                domains_in_comp.setdefault(disc, []).append(nid)

            if len(domains_in_comp) > 1 and all(len(v) >= 1 for v in domains_in_comp.values()):
                for sub_cluster in domains_in_comp.values():
                    final_clusters.append(sub_cluster)
                continue

            # Density core separation: check for articulation / bridge nodes
            # If a sub-group is a complete clique/dense core (e.g. c1-c2-c3) and another node has only 1 link to it
            core_degrees = {nid: len(adj[nid] & set(comp)) for nid in comp}
            sub_dense = [nid for nid, deg in core_degrees.items() if deg >= 2]
            sub_sparse = [nid for nid, deg in core_degrees.items() if deg < 2]

            # If active repulsion exists between sub_sparse and sub_dense, do NOT split!
            # The domain is experiencing active internal dialectical conflict (Aris Directive #11).
            has_internal_conflict = any(
                (u, v) in repulsion_pairs for u in sub_sparse for v in sub_dense
            )

            if sub_dense and sub_sparse and len(sub_dense) >= 3 and not has_internal_conflict:
                final_clusters.append(sub_dense)
                final_clusters.append(sub_sparse)
            else:
                final_clusters.append(comp)

        return final_clusters


__all__ = [
    "TopologyAnalyzer",
    "CONTRA_EXP_SCALE",
    "CONTRA_UNSTABLE_THRESHOLD",
    "MIN_CRYSTAL_DENSITY",
    "MIN_CRYSTAL_CONFIDENCE",
    "MAX_CRYSTAL_CONTRA",
]
