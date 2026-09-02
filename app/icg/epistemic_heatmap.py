"""
Epistemic Heatmap & Priority Queue (app/icg/epistemic_heatmap.py)
Aris Directive #9: Cognitive Tension Ranking

Implements:
  calculate_void_tension(void_id, graph) → float
  get_top_priority_voids(graph, limit=10) → List[TensionRecord]
  recompute_neighbor_tensions(resolved_void_id, graph) → None

Void Tension Formula:
  T(v) = w_anchor * avg_epistemic_of_poles
        + w_connectivity * log1p(connected_high_confidence_nodes)
        + w_tentative * tentative_edge_count
        + w_centrality * centrality_score

Where:
  w_anchor = 0.40       — significance of surrounding known anchors
  w_connectivity = 0.30 — graph reachability boost (log-scaled)
  w_tentative = 0.20    — number of TENTATIVE edges depending on this void
  w_centrality = 0.10   — degree centrality of the two anchor poles

Constants are configurable (no magic numbers in code).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from app.icg.models import ICGGraph

from app.icg.models import (
    NodeType, EdgeStatus, VoidStatus, VoidType,
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration (Aris Directive #9 — no magic numbers)
# ─────────────────────────────────────────────────────────────────────────────

W_ANCHOR: float = 0.40          # Weight: average epistemic confidence of poles
W_CONNECTIVITY: float = 0.30    # Weight: log-scaled count of high-confidence neighbors
W_TENTATIVE: float = 0.20       # Weight: number of TENTATIVE edges linked to this void
W_CENTRALITY: float = 0.10      # Weight: degree centrality of pole nodes

HIGH_CONFIDENCE_THRESHOLD: float = 0.60   # Nodes above this are "known" neighbors
MAX_CENTRALITY_NORM: int = 20             # Normalize degree centrality against this


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(order=True)
class TensionRecord:
    """
    A ranked cognitive void with its tension score and contributing factors.
    Comparable: higher tension = higher priority.
    """
    tension: float = field(compare=True)
    void_id: str = field(compare=False)
    void_type: str = field(compare=False)
    pole_a_id: str = field(compare=False)
    pole_b_id: str = field(compare=False)
    avg_pole_epistemic: float = field(compare=False)
    connectivity_score: float = field(compare=False)
    tentative_count: int = field(compare=False)
    centrality_score: float = field(compare=False)
    inquiry_question: str = field(compare=False, default="")

    def to_dict(self) -> dict:
        return {
            "void_id": self.void_id,
            "void_type": self.void_type,
            "tension": round(self.tension, 4),
            "pole_a_id": self.pole_a_id,
            "pole_b_id": self.pole_b_id,
            "avg_pole_epistemic": round(self.avg_pole_epistemic, 4),
            "connectivity_score": round(self.connectivity_score, 4),
            "tentative_count": self.tentative_count,
            "centrality_score": round(self.centrality_score, 4),
            "inquiry_question": self.inquiry_question[:100] + "..." if len(self.inquiry_question) > 100 else self.inquiry_question,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Core tension calculator
# ─────────────────────────────────────────────────────────────────────────────

def calculate_void_tension(void_id: str, graph: "ICGGraph") -> Optional[TensionRecord]:
    """
    Calculate the Void Tension for a single COGNITIVE_VOID node.

    T(v) = W_ANCHOR * avg_epistemic_of_poles
         + W_CONNECTIVITY * log1p(high_confidence_reachable_count)
         + W_TENTATIVE * (tentative_count / max(1, total_tentative))
         + W_CENTRALITY * centrality_score

    Returns None if the node is not a COGNITIVE_VOID or is already RESOLVED.
    """
    void_node = next((n for n in graph.nodes if n.id == void_id), None)
    if void_node is None:
        return None
    if void_node.type != NodeType.COGNITIVE_VOID:
        return None

    void_meta = (void_node.synthesis_metadata.cognitive_void
                 if void_node.synthesis_metadata else None)
    if void_meta is None:
        return None
    # Skip already-resolved voids
    if void_meta.void_status == VoidStatus.RESOLVED:
        return None

    pole_a_id = void_meta.pole_a_anchor_id
    pole_b_id = void_meta.pole_b_anchor_id

    # ── Factor 1: Average epistemic confidence of the two anchor poles ────────
    node_map: Dict[str, object] = {n.id: n for n in graph.nodes}
    pole_a = node_map.get(pole_a_id)
    pole_b = node_map.get(pole_b_id)
    epi_a = pole_a.epistemic_confidence if pole_a else 0.0
    epi_b = pole_b.epistemic_confidence if pole_b else 0.0
    avg_epistemic = (epi_a + epi_b) / 2.0

    # ── Factor 2: High-confidence nodes reachable from either pole ───────────
    #   (measures how much "known" information surrounds this void)
    reachable_high_conf: Set[str] = set()
    for edge in graph.edges:
        if edge.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK):
            src = node_map.get(edge.source_node_id)
            tgt = node_map.get(edge.target_node_id)
            for pole_id in (pole_a_id, pole_b_id):
                if edge.source_node_id == pole_id and tgt:
                    if tgt.epistemic_confidence >= HIGH_CONFIDENCE_THRESHOLD:
                        reachable_high_conf.add(tgt.id)
                if edge.target_node_id == pole_id and src:
                    if src.epistemic_confidence >= HIGH_CONFIDENCE_THRESHOLD:
                        reachable_high_conf.add(src.id)
    connectivity_score = math.log1p(len(reachable_high_conf))

    # ── Factor 3: TENTATIVE edges linked to this void ─────────────────────────
    total_tentative = sum(1 for e in graph.edges if e.status == EdgeStatus.TENTATIVE)
    void_tentative = sum(
        1 for e in graph.edges
        if e.status == EdgeStatus.TENTATIVE and
        (e.source_node_id == void_id or e.target_node_id == void_id)
    )
    # Normalize against total tentative in graph
    tentative_norm = void_tentative / max(1, total_tentative)

    # ── Factor 4: Degree centrality of pole nodes ─────────────────────────────
    def degree(node_id: str) -> int:
        return sum(
            1 for e in graph.edges
            if e.source_node_id == node_id or e.target_node_id == node_id
        )
    centrality_a = degree(pole_a_id)
    centrality_b = degree(pole_b_id)
    centrality_score = min(1.0, (centrality_a + centrality_b) / (2.0 * MAX_CENTRALITY_NORM))

    # ── Composite Tension ──────────────────────────────────────────────────────
    tension = (
        W_ANCHOR * avg_epistemic
        + W_CONNECTIVITY * min(1.0, connectivity_score)   # log1p capped at 1.0
        + W_TENTATIVE * tentative_norm
        + W_CENTRALITY * centrality_score
    )
    tension = round(min(1.0, tension), 6)

    inquiry_q = ""
    if void_meta.inquiry:
        inquiry_q = void_meta.inquiry.inquiry_question

    return TensionRecord(
        tension=tension,
        void_id=void_id,
        void_type=void_meta.void_type.value,
        pole_a_id=pole_a_id,
        pole_b_id=pole_b_id,
        avg_pole_epistemic=round(avg_epistemic, 4),
        connectivity_score=round(connectivity_score, 4),
        tentative_count=void_tentative,
        centrality_score=round(centrality_score, 4),
        inquiry_question=inquiry_q,
    )


def get_top_priority_voids(graph: "ICGGraph", limit: int = 10) -> List[TensionRecord]:
    """
    Compute Tension for all OPEN COGNITIVE_VOID nodes in the graph and return
    them sorted by descending Tension (highest priority = most bottlenecked).

    Args:
        graph: ICGGraph to analyse
        limit: Maximum number of records to return (default 10)

    Returns:
        List[TensionRecord] sorted by tension descending
    """
    records: List[TensionRecord] = []
    for node in graph.nodes:
        if node.type == NodeType.COGNITIVE_VOID:
            record = calculate_void_tension(node.id, graph)
            if record is not None:  # None = already resolved
                records.append(record)

    # Sort by tension descending (TensionRecord is @dataclass(order=True))
    records.sort(reverse=True)
    return records[:limit]


def recompute_neighbor_tensions(
    resolved_void_id: str,
    graph: "ICGGraph",
    max_hop_radius: int = 2
) -> Dict[str, float]:
    """
    After closing a void (Directive #8/10), recompute Tension for remaining
    OPEN voids within a local radius of `max_hop_radius` hops from the resolved void's poles.

    Uses BFS over CORE_ACTIVE_LINK and SYNTHETIC_LINK edges up to max_hop_radius
    to collect affected anchor poles, preventing global cascade overhead (Aris Directive #10).

    Returns:
        Dict[void_id -> new_tension] for all affected local voids
    """
    # Find the resolved void's poles
    resolved_node = next((n for n in graph.nodes if n.id == resolved_void_id), None)
    if resolved_node is None:
        return {}

    resolved_meta = (resolved_node.synthesis_metadata.cognitive_void
                     if resolved_node.synthesis_metadata else None)
    if resolved_meta is None:
        return {}

    initial_poles = {resolved_meta.pole_a_anchor_id, resolved_meta.pole_b_anchor_id}
    
    # BFS up to max_hop_radius to collect local neighborhood of poles
    affected_poles: Set[str] = set(initial_poles)
    frontier: Set[str] = set(initial_poles)
    
    for _ in range(max_hop_radius - 1):
        next_frontier: Set[str] = set()
        for edge in graph.edges:
            if edge.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK):
                if edge.source_node_id in frontier and edge.target_node_id not in affected_poles:
                    next_frontier.add(edge.target_node_id)
                if edge.target_node_id in frontier and edge.source_node_id not in affected_poles:
                    next_frontier.add(edge.source_node_id)
        if not next_frontier:
            break
        affected_poles.update(next_frontier)
        frontier = next_frontier

    # Find all other OPEN voids that share at least one pole with the affected neighborhood
    affected_tensions: Dict[str, float] = {}
    for node in graph.nodes:
        if node.type != NodeType.COGNITIVE_VOID or node.id == resolved_void_id:
            continue
        meta = (node.synthesis_metadata.cognitive_void
                if node.synthesis_metadata else None)
        if meta is None or meta.void_status == VoidStatus.RESOLVED:
            continue
        if meta.pole_a_anchor_id in affected_poles or meta.pole_b_anchor_id in affected_poles:
            record = calculate_void_tension(node.id, graph)
            if record is not None:
                affected_tensions[node.id] = record.tension

    return affected_tensions


__all__ = [
    "calculate_void_tension",
    "get_top_priority_voids",
    "recompute_neighbor_tensions",
    "TensionRecord",
    "W_ANCHOR", "W_CONNECTIVITY", "W_TENTATIVE", "W_CENTRALITY",
    "HIGH_CONFIDENCE_THRESHOLD",
]
