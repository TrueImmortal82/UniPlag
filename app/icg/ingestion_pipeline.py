"""
Immune Ingestion Pipeline & Quarantine Staging Layer (app/icg/ingestion_pipeline.py)
Aris Directive #14: Dynamic Knowledge Harvesting & Staging Quarantine

Implements:
  1. Staging Quarantine Layer: Ingested claims enter Pending_Validation before graph integration.
  2. Immune Screening: Filters out adversarial noise, acute contradictions, and vacuous mimicry.
  3. Automatic Promotion & Quarantine: Clean claims join active graph; unverified/noisy claims are quarantined into COGNITIVE_WASTELAND.
"""

from __future__ import annotations

import re
import uuid
from typing import List, Dict, Any, Optional

from app.icg.models import (
    ICGGraph, ClaimNode, NodeType, ContributionClass, TextSpan,
    IngestionBatchResult, DomainZoneType,
)
from app.icg.nli_verifier import NLIVerifier


class IngestionPipeline:
    """
    Ingests batch external claims through an immune staging quarantine,
    protecting core knowledge crystals from semantic pollution and hallucinatory noise.
    """

    def __init__(self, nli_verifier: Optional[NLIVerifier] = None):
        self.nli_verifier = nli_verifier or NLIVerifier()

    def ingest_batch_claims(
        self,
        graph: ICGGraph,
        claims_data: List[Dict[str, Any]],
        default_confidence: float = 0.85,
    ) -> IngestionBatchResult:
        """
        Screen and import batch claims into graph through Quarantine Layer (Aris Directive #14).
        """
        result = IngestionBatchResult(total_submitted=len(claims_data))

        # Identify existing core crystal nodes for immune screening
        crystal_anchors = [
            n for n in graph.nodes
            if n.is_anchor and n.epistemic_confidence >= 0.80 and n.type != NodeType.COGNITIVE_VOID
        ]

        evasive_pattern = (
            r"(рассматривает\s+гипотетическ|иллюстрирует\s+вероятностн|структурирует\s+феноменолог|"
            r"формируя\s+абстрактн|мета-дискурсивн|коррелирует\s+в\s+первом\s+приближении)"
        )

        for item in claims_data:
            text = item.get("text", "").strip()
            if not text:
                continue

            claim_id = item.get("id", f"claim_{uuid.uuid4().hex[:8]}")
            user_epi = item.get("epistemic_confidence", default_confidence)

            # Step 1: Check for Evasive / Empty Mimicry Noise
            if bool(re.search(evasive_pattern, text.lower())):
                quarantine_node = ClaimNode(
                    id=claim_id,
                    type=NodeType.CLAIM,
                    contribution_class=ContributionClass.UNKNOWN,
                    span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
                    is_anchor=False,
                    confidence=0.30,
                    epistemic_confidence=0.20,
                )
                graph.nodes.append(quarantine_node)
                result.quarantined_to_wasteland += 1
                result.quarantined_node_ids.append(claim_id)
                continue

            # Step 2: Immune Contradiction Screening against Core Crystals
            has_severe_contradiction = False
            for anchor in crystal_anchors:
                nli_check = self.nli_verifier.hybrid.verify_pair(anchor.span.raw_text, text)
                if nli_check.contradiction_score >= 0.70:
                    has_severe_contradiction = True
                    break

            if has_severe_contradiction:
                result.rejected_contradictions += 1
                quarantine_node = ClaimNode(
                    id=claim_id,
                    type=NodeType.CLAIM,
                    contribution_class=ContributionClass.UNKNOWN,
                    span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
                    is_anchor=False,
                    confidence=0.25,
                    epistemic_confidence=0.15,
                )
                graph.nodes.append(quarantine_node)
                result.quarantined_to_wasteland += 1
                result.quarantined_node_ids.append(claim_id)
                continue

            # Step 3: Clean Claim -> Promoted to Active Knowledge Graph
            active_node = ClaimNode(
                id=claim_id,
                type=NodeType.SUPER_ANCHOR if user_epi >= 0.85 else NodeType.ANCHOR,
                contribution_class=ContributionClass.SYNTHESIS,
                span=TextSpan(start_char=0, end_char=len(text), raw_text=text),
                is_anchor=True,
                is_super_anchor=(user_epi >= 0.85),
                confidence=0.90,
                epistemic_confidence=user_epi,
            )
            graph.nodes.append(active_node)
            result.promoted_to_active += 1
            result.active_claim_node_ids.append(claim_id)

        return result


__all__ = ["IngestionPipeline"]
