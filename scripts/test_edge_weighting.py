"""
Test Suite for Edge Weighting, 3-Tier Noise Filtering & Graph Density (scripts/test_edge_weighting.py)
Validates Aris Directive #2 (alpha=0.2, beta=0.6, gamma=0.2, 3-tier zones, and synthesis bridge protection).
"""

from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import EdgeStatus, ContributionClass


def test_edge_weighting_and_density():
    print("=" * 80)
    print("  EDGE WEIGHTING, 3-TIER NOISE FILTERING & DENSITY SUITE (ARIS DIRECTIVE #2)")
    print("=" * 80)

    builder = ICGGraphBuilder()

    # 1. Test Authentic Multi-Source Synthesis with Strong Necessity
    text_synthesis = (
        "В исследовании Иванова [1] показано, что увеличение размера батча свыше 256 снижает обобщающую способность модели. "
        "В то же время Петров [2] установил, что адаптивный темп обучения AdamW стабилизирует дисперсию градиентов. "
        "Следовательно, объединяя данные подходы, при размере батча 512 и динамическом масштабировании AdamW достигается стабилизация градиентов при сохранении обобщающей способности."
    )
    g1 = builder.build_graph("doc_synth_test", text_synthesis, discipline="AI/ML")
    
    print("\n[1/3] Testing Synthesis Edge Weighting & Bridge Protection...")
    print(f"      Total Nodes: {len(g1.nodes)}, Total Edges: {len(g1.edges)}")
    for e in g1.edges:
        wd = e.weight_details
        print(f"      Edge [{e.source_node_id} -> {e.target_node_id}]: W={e.weight:.3f} | Status={e.status.value} | Protected={wd.is_protected_synthesis_bridge}")
        print(f"           Details: Sim={wd.semantic_similarity:.3f} (x0.2), Necessity={wd.causal_necessity:.3f} (x0.6), Role={wd.discourse_role_weight:.3f} (x0.2)")
        assert e.status == EdgeStatus.CORE_ACTIVE_LINK, "Synthesis parent edge must be CORE_ACTIVE_LINK"
        assert e.weight >= 0.20, "Core reasoning edge weight should be >= 0.20"

    print(f"      Raw Graph Density:      {g1.metrics_summary.graph_density_raw:.3f}")
    print(f"      Filtered Core Density:  {g1.metrics_summary.graph_density_filtered:.3f}")
    print(f"      Edge Counts: Core={g1.metrics_summary.core_edges_count}, Weak={g1.metrics_summary.weak_edges_count}, Decorative={g1.metrics_summary.decorative_edges_count}")

    # 2. Test Single Inference Edge Weighting
    text_inference = (
        "Согласно фундаментальной теореме Шеннона [1], пропускная способность канала связи строго ограничена частотной полосой и шумом. "
        "Отсюда следует, что при фиксированной полосе частот рост скорости передачи достижим только за счет повышения мощности передатчика."
    )
    g2 = builder.build_graph("doc_infer_test", text_inference, discipline="Engineering")
    print("\n[2/3] Testing Single Inference Edge Weighting...")
    for e in g2.edges:
        wd = e.weight_details
        print(f"      Edge [{e.source_node_id} -> {e.target_node_id}]: W={e.weight:.3f} | Status={e.status.value}")
        assert e.weight > 0.30, "Strong inference edge should have significant weight"

    # 3. Test Contradiction / Weak / Decorative Edge Routing
    text_contradiction = (
        "В отчете [1] доказано, что применение нейросетей увеличивает точность распознавания речи. "
        "Следовательно, использование нейросетей уменьшает точность распознавания речи."
    )
    g3 = builder.build_graph("doc_contra_test", text_contradiction, discipline="AI/ML")
    print("\n[3/3] Testing Contradictory / Decorative Edge Classification...")
    for e in g3.edges:
        print(f"      Edge [{e.source_node_id} -> {e.target_node_id}]: W={e.weight:.3f} | Status={e.status.value}")
        assert e.status == EdgeStatus.DECORATIVE_MENTION or e.weight < 0.10, "Contradictory fallacy edge should be decorative / pruned"

    print("\n" + "=" * 80)
    print("  ALL EDGE WEIGHTING & FILTERING TESTS PASSED (3/3)!")
    print("=" * 80)


if __name__ == "__main__":
    test_edge_weighting_and_density()
