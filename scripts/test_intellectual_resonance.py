"""
Test Suite for Intellectual Resonance Trigger & Collapse to Synthesis (scripts/test_intellectual_resonance.py)
Validates Aris Directive #3:
- Cross-domain intersection of >= 3 domains.
- Resonance score computation with diversity factor.
- Automatic collapse to SYNTHESIS when R(v) >= 0.70.
- Formatted resonance logging.
"""

from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import ContributionClass, EdgeStatus


def test_intellectual_resonance():
    print("=" * 80)
    print("  INTELLECTUAL RESONANCE & COLLAPSE TO SYNTHESIS SUITE (ARIS DIRECTIVE #3)")
    print("=" * 80)

    builder = ICGGraphBuilder()

    # Multi-domain text spanning 3 distinct domains:
    # 1. Quantum Physics: "кубиты и оптический резонатор"
    # 2. Neuroscience: "синаптическая пластичность коры головного мозга"
    # 3. Deep Learning: "градиентная оптимизация и трансформеры"
    # Conclusion: Multi-disciplinary synthesis combining all 3 domains
    multi_domain_doc = (
        "В исследовании [1] показано, что квантовые кубиты в оптическом резонаторе сохраняют когерентность при низкой температуре. "
        "В работе [2] установлено, что синаптическая пластичность нейронов коры мозга подчиняется закону Хебба. "
        "В статье [3] доказано, что градиентная оптимизация в трансформерах выравнивает матричные веса. "
        "Следовательно, объединяя данные подходы, квантовая модель памяти с синаптической пластичностью и градиентным трансформером ускоряет обучение нейросети."
    )

    graph = builder.build_graph("doc_resonance_cross_domain", multi_domain_doc, discipline="Interdisciplinary AI")

    print("\n[1/2] Inspecting Domain Classification on Extracted Claims...")
    for n in graph.nodes:
        print(f"      [{n.id}] Domain: {n.discipline_domain:<22} | Class: {n.contribution_class.value:<14} | Text: {n.span.raw_text[:60]}...")

    target_node = graph.nodes[-1]
    res_meta = target_node.synthesis_metadata.resonance if target_node.synthesis_metadata else None

    print("\n[2/2] Validating Intellectual Resonance Trigger & Collapse...")
    assert res_meta is not None, "ResonanceMetadata must be present on cross-domain synthesis node"
    print(f"      Resonance Score R(v):         {res_meta.resonance_score:.3f}")
    print(f"      Is Resonance Active:          {res_meta.is_resonance_active}")
    print(f"      Collapsed to Synthesis:       {res_meta.collapsed_to_synthesis}")
    print(f"      Contributing Domains:         {res_meta.contributing_domains}")
    print(f"      Resonance Log Output:         {res_meta.resonance_log}")
    print(f"      Final Node ContributionClass: {target_node.contribution_class.value}")
    print(f"\n      Graph Active Resonance Count: {graph.metrics_summary.active_resonance_nodes_count}")
    print(f"      Graph Max Resonance Score:    {graph.metrics_summary.max_resonance_score:.3f}")

    assert res_meta.is_resonance_active, "Resonance should be ACTIVE for >= 3 domains"
    assert res_meta.resonance_score >= 0.70, "Resonance score must be >= 0.70 for 3 distinct domain intersection"
    assert res_meta.collapsed_to_synthesis, "Should collapse to SYNTHESIS"
    assert target_node.contribution_class in [ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS]

    print("\n" + "=" * 80)
    print("  ALL INTELLECTUAL RESONANCE TESTS PASSED (ARIS DIRECTIVE #3 VERIFIED)!")
    print("=" * 80)


if __name__ == "__main__":
    test_intellectual_resonance()
