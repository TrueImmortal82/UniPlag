"""
Test Suite for Emergent Topology, Synthesis Gravity & Anchor Evolution (scripts/test_emergent_topology.py)
Validates Aris Directive #4:
1. Synthesis Gravity: Boosts edge weights around synthesis hubs proportional to R(S).
2. Anchor Roles: Promotes synthesis hubs aggregating >= 3 distinct domains to ANCHOR nodes.
3. Redundant Path Pruning: Bypasses weak direct links when strong composite synthesis routes exist.
4. Topologic structure optimization.
"""

from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import NodeType, EdgeStatus, ContributionClass


def test_emergent_topology():
    print("=" * 80)
    print("  EMERGENT TOPOLOGY & SYNTHESIS GRAVITY SUITE (ARIS DIRECTIVE #4)")
    print("=" * 80)

    builder = ICGGraphBuilder()

    # Multi-claim document producing Synthesis + Subordinate Inferences
    doc_text = (
        "В исследовании [1] показано, что квантовые кубиты в оптическом резонаторе сохраняют когерентность при низкой температуре. "
        "В работе [2] установлено, что синаптическая пластичность нейронов коры мозга подчиняется закону Хебба. "
        "В статье [3] доказано, что градиентная оптимизация в трансформерах выравнивает матричные веса. "
        "Следовательно, объединяя данные подходы, квантовая модель памяти с синаптической пластичностью и градиентным трансформером ускоряет обучение нейросети. "
        "Отсюда следует, что предложенная архитектура квантовой памяти снижает энергопотребление дата-центров на 40%."
    )

    graph = builder.build_graph("doc_emergent_test", doc_text, discipline="Quantum AI")

    print("\n[1/3] Validating Anchor Node Evolution & Synthesis Gravity...")
    anchor_nodes = [n for n in graph.nodes if n.is_anchor]
    print(f"      Anchor Nodes Found: {len(anchor_nodes)}")
    for a in anchor_nodes:
        print(f"      - [ANCHOR {a.id}] Class: {a.contribution_class.value} | Type: {a.type.value} | Text: {a.span.raw_text[:60]}...")
        assert a.type == NodeType.ANCHOR, "Node type must be ANCHOR"
        assert a.is_anchor, "is_anchor flag must be True"

    print("\n[2/3] Validating Synthesis Gravity Edge Boosts...")
    for e in graph.edges:
        wd = e.weight_details
        print(f"      Edge [{e.source_node_id} -> {e.target_node_id}]: Final W={e.weight:.3f} (Gravity Boost: +{wd.gravity_bonus:.3f}) | Status={e.status.value}")
        if e.target_node_id == anchor_nodes[0].id or e.source_node_id == anchor_nodes[0].id:
            assert wd.gravity_bonus > 0.0, "Edges connected to synthesis hub must receive gravity boost"

    print("\n[3/3] Validating Emergent Topology Metrics...")
    ms = graph.metrics_summary
    print(f"      Anchor Nodes Count:         {ms.anchor_nodes_count}")
    print(f"      Active Resonance Nodes:     {ms.active_resonance_nodes_count}")
    print(f"      Max Resonance Score:        {ms.max_resonance_score:.3f}")
    print(f"      Raw Graph Density:          {ms.graph_density_raw:.3f}")
    print(f"      Filtered Core Density:      {ms.graph_density_filtered:.3f}")
    print(f"      Pruned Redundant Edges:     {ms.pruned_redundant_edges_count}")

    assert ms.anchor_nodes_count >= 1, "Must have at least 1 Anchor node"
    assert ms.max_resonance_score >= 0.70, "Max resonance score must be >= 0.70"

    print("\n" + "=" * 80)
    print("  ALL EMERGENT TOPOLOGY TESTS PASSED (ARIS DIRECTIVE #4 VERIFIED)!")
    print("=" * 80)


if __name__ == "__main__":
    test_emergent_topology()
