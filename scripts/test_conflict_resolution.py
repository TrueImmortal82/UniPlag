"""
Test Suite for Cognitive Immunity, Paradox Containers & Negative Gravity Repulsion (scripts/test_conflict_resolution.py)
Validates Aris Directive #5:
1. Negative Gravity Repulsion on contradiction edges (W = -0.80, status = REPULSION_BOUNDARY).
2. Paradox_Container meta-node creation over opposing dialectical poles.
3. Isolation bubble & Quarantine enforcement (is_contested=True, cannot be ANCHOR without Support/Conflict > 3.0).
4. Full regression pass.
"""

from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import NodeType, EdgeStatus, ContributionClass, RelationType


def test_conflict_resolution_paradox():
    print("=" * 80)
    print("  COGNITIVE IMMUNITY & PARADOX RESOLUTION SUITE (ARIS DIRECTIVE #5)")
    print("=" * 80)

    builder = ICGGraphBuilder()

    # Paradox scenario: Source 1 vs Source 2 asserting opposite claims on Grover's Algorithm
    paradox_doc = (
        "В исследовании Смита [1] доказано, что квантовый алгоритм Гровера ускоряет поиск в неструктурированной базе данных. "
        "Следовательно, применение квантового алгоритма Гровера замедляет поиск в неструктурированной базе данных."
    )

    graph = builder.build_graph("doc_paradox_test", paradox_doc, discipline="Quantum CS")

    print("\n[1/3] Validating Negative Gravity Repulsion Edges...")
    repulsion_edges = [e for e in graph.edges if e.status == EdgeStatus.REPULSION_BOUNDARY]
    print(f"      Repulsion Edges Found: {len(repulsion_edges)}")
    for re in repulsion_edges:
        print(f"      - Edge [{re.source_node_id} -> {re.target_node_id}]: Weight={re.weight:.2f} | Status={re.status.value} | Relation={re.relation_type.value}")
        assert re.weight == -0.80, "Contradiction edge must have negative gravity W = -0.80"
        assert re.status == EdgeStatus.REPULSION_BOUNDARY, "Edge status must be REPULSION_BOUNDARY"
        assert re.relation_type == RelationType.NEGATIVE_GRAVITY_REPULSION

    print("\n[2/3] Validating Paradox Containers & Quarantine Bubbles...")
    paradox_nodes = [n for n in graph.nodes if n.type == NodeType.PARADOX_CONTAINER]
    print(f"      Paradox Container Nodes: {len(paradox_nodes)}")
    for pn in paradox_nodes:
        meta = pn.synthesis_metadata.paradox_container if pn.synthesis_metadata else None
        print(f"      - [PARADOX CONTAINER {pn.id}] Pole A: {meta.pole_a_node_ids} vs Pole B: {meta.pole_b_node_ids}")
        print(f"        Explanation: {meta.conflict_explanation}")
        assert meta is not None, "ParadoxContainerMetadata must be present"
        assert meta.repulsion_force == -0.80, "Repulsion force must be -0.80"

    contested_nodes = [n for n in graph.nodes if n.is_contested]
    print(f"      Contested Quarantined Nodes: {len(contested_nodes)}")
    for cn in contested_nodes:
        print(f"      - [{cn.id}] is_quarantined={cn.is_quarantined}, is_anchor={cn.is_anchor}, Support/Conflict={cn.support_to_conflict_ratio}")
        assert cn.is_quarantined, "Contested node must be in Quarantine bubble"
        assert not cn.is_anchor, "Contested node is strictly forbidden from becoming ANCHOR"

    print("\n[3/3] Validating Cognitive Immunity Metrics Summary...")
    ms = graph.metrics_summary
    print(f"      Paradox Containers Count: {ms.paradox_containers_count}")
    print(f"      Quarantined Nodes Count:  {ms.quarantined_nodes_count}")
    print(f"      Repulsion Edges Count:    {ms.repulsion_edges_count}")

    assert ms.paradox_containers_count >= 1, "Must have at least 1 Paradox Container"
    assert ms.repulsion_edges_count >= 1, "Must have at least 1 Negative Gravity Repulsion edge"

    print("\n" + "=" * 80)
    print("  ALL COGNITIVE IMMUNITY & PARADOX TESTS PASSED (ARIS DIRECTIVE #5 VERIFIED)!")
    print("=" * 80)


if __name__ == "__main__":
    test_conflict_resolution_paradox()
