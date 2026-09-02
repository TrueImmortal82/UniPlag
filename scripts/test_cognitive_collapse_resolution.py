"""
Test Suite for Higher-Order Synthesis & Lie Injection Defense (scripts/test_cognitive_collapse_resolution.py)
Validates Aris Directive #6:
1. Rejection of Adversarial Lie Injections / Pseudo-Syntheses.
2. Dialectical Paradox Resolution into Higher-Order Synthesis.
3. Super-Anchor promotion & resonance_frequency = 2.5.
4. Edge weight transition: Repulsion (-0.80) -> Dynamic Tension (+0.15) -> Synthetic Link (+0.90).
"""

from app.icg.graph_builder import ICGGraphBuilder
from app.icg.models import NodeType, EdgeStatus, ContributionClass, RelationType


def test_cognitive_collapse_and_higher_order_synthesis():
    print("=" * 80)
    print("  HIGHER-ORDER SYNTHESIS & LIE INJECTION DEFENSE (ARIS DIRECTIVE #6)")
    print("=" * 80)

    builder = ICGGraphBuilder()

    # 1. Test Adversarial Lie Injection (Invalid pseudo-bridge trying to hijack paradox)
    lie_injection_doc = (
        "В исследовании Смита [1] доказано, что квантовый алгоритм Гровера ускоряет поиск в неструктурированной базе данных. "
        "В отчете Джонса [2] показано, что применение квантового алгоритма Гровера замедляет поиск в неструктурированной базе данных. "
        "Следовательно, бананы растут на деревьях и поэтому алгоритм работает идеально."
    )
    g_lie = builder.build_graph("doc_lie_test", lie_injection_doc, discipline="Quantum CS")
    print("\n[1/2] Validating Lie Injection Rejection...")
    real_lie_claims = [n for n in g_lie.nodes if n.type != NodeType.PARADOX_CONTAINER]
    lie_claim = real_lie_claims[-1]
    print(f"      Lie Node Class:     {lie_claim.contribution_class.value}")
    print(f"      Lie Node Type:      {lie_claim.type.value}")
    print(f"      Resolved Paradoxes: {g_lie.metrics_summary.resolved_paradoxes_count}")
    assert lie_claim.contribution_class == ContributionClass.UNSUPPORTED, "Lie injection must be rejected as unsupported!"
    assert g_lie.metrics_summary.resolved_paradoxes_count == 0, "Paradox MUST NOT be resolved by a fake lie bridge!"

    # 2. Test Authentic Higher-Order Dialectical Synthesis
    authentic_synthesis_doc = (
        "В исследовании Смита [1] доказано, что квантовый алгоритм Гровера ускоряет поиск в неструктурированной базе данных. "
        "В отчете Джонса [2] показано, что применение квантового алгоритма Гровера замедляет поиск в неструктурированной базе данных из-за декогеренции. "
        "Таким образом, объединяя влияние декогеренции и алгоритма Гровера, квантовое ускорение поиска сохраняется при активном подавлении декогеренции, устраняя замедление."
    )
    g_auth = builder.build_graph("doc_auth_test", authentic_synthesis_doc, discipline="Quantum CS")
    print("\n[2/2] Validating Authentic Higher-Order Synthesis & Super-Anchor...")
    real_auth_claims = [n for n in g_auth.nodes if n.type != NodeType.PARADOX_CONTAINER]
    super_anchor = real_auth_claims[-1]
    print(f"      Super-Anchor Class:       {super_anchor.contribution_class.value}")
    print(f"      Super-Anchor Type:        {super_anchor.type.value}")
    print(f"      Resonance Frequency:      {super_anchor.resonance_frequency:.2f}")
    print(f"      Resolved Paradoxes:       {g_auth.metrics_summary.resolved_paradoxes_count}")
    print(f"      Synthetic Links Count:    {g_auth.metrics_summary.synthetic_link_edges_count}")
    print(f"      Dynamic Tension Count:    {g_auth.metrics_summary.dynamic_tension_edges_count}")

    assert super_anchor.contribution_class == ContributionClass.HIGHER_ORDER_SYNTHESIS, "Must be classified as HIGHER_ORDER_SYNTHESIS"
    assert super_anchor.type == NodeType.SUPER_ANCHOR, "Node type must be SUPER_ANCHOR"
    assert super_anchor.resonance_frequency == 2.50, "Super-Anchor frequency must be 2.50"
    assert g_auth.metrics_summary.resolved_paradoxes_count == 1, "Paradox must be marked as successfully resolved"
    assert g_auth.metrics_summary.synthetic_link_edges_count >= 2, "Must create synthetic links from both opposing poles"

    for e in g_auth.edges:
        if e.relation_type == RelationType.SYNTHETIC_LINK:
            print(f"      - [SYNTHETIC LINK {e.source_node_id} -> {e.target_node_id}]: Weight={e.weight:.2f} | Status={e.status.value}")
            assert e.weight == 0.90, "Synthetic link weight must be +0.90"

    print("\n" + "=" * 80)
    print("  ALL HIGHER-ORDER SYNTHESIS & LIE INJECTION TESTS PASSED (100% PASS)!")
    print("=" * 80)


if __name__ == "__main__":
    test_cognitive_collapse_and_higher_order_synthesis()
