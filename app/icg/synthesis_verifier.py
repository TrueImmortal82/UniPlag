"""
Synthesis & Causal Contribution Verifier v0.4 (app/icg/synthesis_verifier.py)
Implements continuous Joint Dependency Scoring (JDS), anti-flooding irrelevant premise filtering,
Incomplete Evidence Trap detection (Protocol B), and ECC-weighted epistemic confidence.
"""

from typing import List, Dict, Tuple, Optional, Set
import re
import math
from app.icg.models import (
    ClaimNode, ContributionClass, AblationResult, SynthesisMetadata, ExternalAttribution
)
from app.icg.nli_verifier import NLIVerifier, NLIVerificationResult
from app.icg.external_search import ExternalSearchEngine


class SynthesisVerifier:
    def __init__(self, nli_verifier: Optional[NLIVerifier] = None, external_search: Optional[ExternalSearchEngine] = None):
        self.nli = nli_verifier or NLIVerifier()
        if external_search is None:
            external_search = ExternalSearchEngine(
                embed_model=getattr(self.nli.hybrid, 'dense_model', None)
            )
        self.external_search = external_search
        self.nli.external_search = self.external_search

    def evaluate_claim_derivation(
        self,
        target_claim: ClaimNode,
        candidate_premises: List[ClaimNode],
        use_llm: bool = False,
        entailment_threshold: float = 0.04
    ) -> Tuple[ContributionClass, float, Optional[SynthesisMetadata]]:
        conclusion_text = target_claim.span.raw_text
        has_synthesis_modality = bool(
            target_claim.proposition and 
            target_claim.proposition.modality == "synthesis_claim"
        )

        if not candidate_premises:
            if target_claim.proposition and target_claim.proposition.modality == "hypothesis":
                ext_res = self.external_search.verify_global_novelty(target_claim.span.raw_text)
                meta = SynthesisMetadata(
                    parent_premise_ids=[],
                    source_novelty_score=ext_res.global_novelty_score,
                    external_attribution=ext_res
                )
                return ContributionClass.ORIGINAL_CONTRIBUTION, 0.85, meta
            return ContributionClass.UNSUPPORTED, 0.10, None

        # Protocol B: Incomplete Evidence Trap (A -> C without B)
        # If the claim explicitly purports multi-source synthesis but has only 1 premise:
        if len(candidate_premises) == 1 and has_synthesis_modality:
            ext_res = self.external_search.verify_global_novelty(conclusion_text)
            meta = SynthesisMetadata(
                parent_premise_ids=[candidate_premises[0].id],
                is_missing_required_premise=True,
                external_attribution=ext_res
            )
            return ContributionClass.UNKNOWN, 0.20, meta

        premise_texts = {p.id: p.span.raw_text for p in candidate_premises}
        all_texts = list(premise_texts.values())

        # 1. Multi-Premise Joint Verification
        full_res = self.nli.verify_step(all_texts, conclusion_text, use_llm=use_llm)
        
        # Check for explicit contradiction (Layer 2 value conflict detector)
        # BUT: skip contradiction check if target is inference and all premises are inference/reproduction
        # This prevents false contradictions in logical inference chains
        target_is_inference = target_claim.proposition and target_claim.proposition.modality == "inference"
        premises_are_chain = all(
            p.proposition and p.proposition.modality in ("inference", "assertion")
            for p in candidate_premises
        )
        if full_res.is_contradiction(threshold=0.40):
            if target_is_inference and premises_are_chain:
                pass  # Don't flag contradiction in inference chains
            else:
                return ContributionClass.CONTRADICTORY, round(full_res.contradiction_score, 3), None

        # Check for non-sequitur / unsupported / fallacy
        if not full_res.is_valid_entailment(threshold=entailment_threshold) or not full_res.counterfactual_passed:
            if full_res.fallacy_reason and ("fallacy" in full_res.fallacy_reason.lower() or "non-sequitur" in full_res.fallacy_reason.lower() or "pseudo" in full_res.fallacy_reason.lower()):
                return ContributionClass.UNSUPPORTED, 0.05, None
            if full_res.entailment_score >= 0.02 and full_res.counterfactual_passed:
                return ContributionClass.UNKNOWN, round(full_res.entailment_score, 3), None
            return ContributionClass.UNSUPPORTED, full_res.entailment_score, None

        # 2. Hypothesis check grounded in premises
        if target_claim.proposition and target_claim.proposition.modality == "hypothesis":
            ext_res = self.external_search.verify_global_novelty(conclusion_text)
            meta = SynthesisMetadata(
                parent_premise_ids=[p.id for p in candidate_premises],
                source_novelty_score=0.90,
                external_attribution=ext_res
            )
            return ContributionClass.ORIGINAL_CONTRIBUTION, 0.88, meta

        # 3. Single-Premise Tests (P_i -> C)
        single_scores: Dict[str, float] = {}
        single_explainers: List[str] = []
        
        for p in candidate_premises:
            s_res = self.nli.verify_step([p.span.raw_text], conclusion_text, use_llm=use_llm)
            single_scores[p.id] = s_res.entailment_score
            if s_res.is_valid_entailment(threshold=0.75):
                single_explainers.append(p.id)

        # 4. Continuous Counterfactual Ablation & Anti-Flooding Test
        ablated_scores: Dict[str, float] = {}
        necessity_scores: Dict[str, float] = {}
        critical_premises: List[str] = []
        irrelevant_premises: List[str] = []
        
        if len(candidate_premises) >= 2:
            for p in candidate_premises:
                subset_texts = [text for pid, text in premise_texts.items() if pid != p.id]
                abl_res = self.nli.verify_step(subset_texts, conclusion_text, use_llm=use_llm)
                ablated_scores[p.id] = abl_res.entailment_score
                
                delta = max(0.0, full_res.entailment_score - abl_res.entailment_score)
                necessity_scores[p.id] = round(delta, 3)
                
                if delta >= 0.04 or (abl_res.entailment_score < 0.40 and full_res.entailment_score >= 0.25):
                    critical_premises.append(p.id)
                elif delta < 0.01:
                    irrelevant_premises.append(p.id)

        # 5. Continuous Joint Dependency Score (JDS) Calculation
        max_single_e = max(single_scores.values()) if single_scores else 0.0
        mean_necessity = (sum(necessity_scores.values()) / len(necessity_scores)) if necessity_scores else 0.0
        raw_jds = mean_necessity * 2.5 * (1.0 - max(0.0, max_single_e - 0.20))
        continuous_jds = round(max(0.0, min(1.0, raw_jds)), 3)

        # 6. Novelty & External Corpus Verification with ECC
        source_novelty, has_novel_relation = self._calculate_novelty(candidate_premises, target_claim)
        ext_attrib = self.external_search.verify_global_novelty(conclusion_text)

        sources_in_premises = set()
        for p in candidate_premises:
            sources_in_premises.update(p.sources_cited)

        # Joint Multi-Source Synthesis Qualification:
        is_joint_synthesis = (
            len(candidate_premises) >= 2 and
            (has_novel_relation or has_synthesis_modality or len(sources_in_premises) >= 2) and
            (has_synthesis_modality or (has_novel_relation and len(sources_in_premises) >= 2) or continuous_jds >= 0.20) and
            full_res.entailment_score >= 0.15
        ) or (
            # Aris Directive: "fast corridor" for CONFIRMED cross-domain novelty.
            # A novel fused relation should not depend on how much each single premise
            # explains alone (JDS penalizes strong single premises). Guarded by high
            # joint entailment so novelty without logical grounding stays hallucination.
            len(candidate_premises) >= 2
            and has_novel_relation
            and len(sources_in_premises) >= 2
            and full_res.entailment_score >= 0.30
        )

        ablation_summary = (
            f"Joint dependency: {'PASSED' if is_joint_synthesis else 'FAILED'} "
            f"(JDS: {continuous_jds:.3f}, Critical: {critical_premises}, Single explainers: {single_explainers}, "
            f"External known: {ext_attrib.found_in_external_corpus}, ECC: {ext_attrib.external_corpus_coverage})"
        )

        ablation_result = AblationResult(
            full_entailment=full_res.entailment_score,
            single_premise_scores=single_scores,
            ablated_premise_scores=ablated_scores,
            joint_dependency_score=continuous_jds,
            causal_necessity_scores=necessity_scores,
            critical_premises=critical_premises if critical_premises else [p.id for p in candidate_premises],
            irrelevant_premises=irrelevant_premises,
            ablation_summary=ablation_summary
        )

        synthesis_meta = SynthesisMetadata(
            parent_premise_ids=[p.id for p in candidate_premises if p.id not in irrelevant_premises],
            novel_relational_contribution=has_novel_relation,
            source_novelty_score=source_novelty,
            ablation=ablation_result,
            external_attribution=ext_attrib
        )

        # Final 8-Class Assignment
        if is_joint_synthesis:
            if ext_attrib.found_in_external_corpus:
                conf = min(0.98, full_res.entailment_score * 1.1)
                return ContributionClass.SYNTHESIS, round(conf, 3), synthesis_meta
            else:
                conf = min(0.98, full_res.entailment_score * 1.1 + ext_attrib.global_novelty_score * 0.1)
                return ContributionClass.SOURCE_NOVEL_SYNTHESIS, round(conf, 3), synthesis_meta

        elif single_explainers or len(candidate_premises) == 1:
            explainer_id = single_explainers[0] if single_explainers else candidate_premises[0].id
            explainer_text = premise_texts[explainer_id]
            
            p_stems = self.nli.hybrid._extract_content_stems(explainer_text)
            c_stems = self.nli.hybrid._extract_content_stems(conclusion_text)
            
            matched_c = sum(1 for cs in c_stems if any(self.nli.hybrid._stems_match(ps, cs) for ps in p_stems))
            stem_overlap = matched_c / max(1, len(c_stems))
            has_conditions = bool(target_claim.proposition and target_claim.proposition.conditions)
            
            if (stem_overlap >= 0.70 or single_scores.get(explainer_id, 0) >= 0.75) and not has_conditions:
                if target_claim.proposition and target_claim.proposition.modality == "inference":
                    return ContributionClass.INFERENCE, round(full_res.entailment_score, 3), synthesis_meta
                return ContributionClass.REPRODUCTION, 0.92, synthesis_meta
            else:
                return ContributionClass.INFERENCE, round(full_res.entailment_score, 3), synthesis_meta

        elif full_res.entailment_score >= 0.10:
            return ContributionClass.INFERENCE, round(full_res.entailment_score, 3), synthesis_meta

        else:
            return ContributionClass.UNKNOWN, 0.25, synthesis_meta

    def _calculate_novelty(
        self,
        premises: List[ClaimNode],
        conclusion: ClaimNode
    ) -> Tuple[float, bool]:
        conc_text = conclusion.span.raw_text
        premise_texts = [p.span.raw_text for p in premises]
        
        c_stems = self.nli.hybrid._extract_content_stems(conc_text)
        p_stems_list = [self.nli.hybrid._extract_content_stems(p_text) for p_text in premise_texts]
        
        if not p_stems_list or not c_stems:
            return 0.0, False

        overlap_counts = []
        for p_stems in p_stems_list:
            cnt = sum(1 for cs in c_stems if any(self.nli.hybrid._stems_match(ps, cs) for ps in p_stems))
            overlap_counts.append(cnt)

        multi_overlap = sum(1 for ov in overlap_counts if ov >= 2)

        # Aris Directive: true cross-domain SYNTHESIS draws ~one fundamental concept
        # from each disparate source and fuses them into a new meaning. Requiring
        # multi_overlap>=2 (much shared with EACH premise) misses this. So besides the
        # original path (kept), also mark as novel when:
        #   - 2+ premises, EACH contributes >=1 stem to the conclusion,
        #   - premises are cross-domain (low mutual overlap p1_p2),
        #   - and (guarded by caller) the joint entailment is high (no hallucination).
        if len(premises) >= 2 and multi_overlap >= 2:
            p1_p2_overlap = sum(1 for s1 in p_stems_list[0] if any(self.nli.hybrid._stems_match(s2, s1) for s2 in p_stems_list[1]))
            if p1_p2_overlap <= 2:
                return 0.88, True

        p1_p2_cross_overlap = sum(
            1 for s1 in p_stems_list[0] if any(self.nli.hybrid._stems_match(s2, s1) for s2 in p_stems_list[1])
        ) if len(p_stems_list) >= 2 else 0
        each_contributes = bool(
            len(p_stems_list) >= 2
        ) and all(ov >= 1 for ov in overlap_counts) and (len([ov for ov in overlap_counts if ov >= 1]) >= 2)
        if each_contributes and p1_p2_cross_overlap <= 2:
            return 0.88, True

        max_ov = max(overlap_counts) if overlap_counts else 0
        novelty = min(1.0, max(0.1, 1.0 - (max_ov / max(1, len(c_stems)))))
        return round(novelty, 3), False
