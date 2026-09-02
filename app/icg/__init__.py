"""
Intellectual Contribution Graph (ICG) Package
"""

from app.icg.models import (
    ICGGraph, ClaimNode, EdgeEvidence, TextSpan,
    Proposition, ContributionClass, NodeType, RelationType, MetricsSummary
)
from app.icg.discourse import extract_claim_nodes_from_text, split_sentences_with_spans
from app.icg.nli_verifier import NLIVerifier, NLIVerificationResult
from app.icg.graph_builder import ICGGraphBuilder

__all__ = [
    "ICGGraph",
    "ClaimNode",
    "EdgeEvidence",
    "TextSpan",
    "Proposition",
    "ContributionClass",
    "NodeType",
    "RelationType",
    "MetricsSummary",
    "extract_claim_nodes_from_text",
    "split_sentences_with_spans",
    "NLIVerifier",
    "NLIVerificationResult",
    "ICGGraphBuilder",
]
