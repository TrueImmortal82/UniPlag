"""
Intellectual Contribution Graph Builder v0.4 (app/icg/graph_builder.py)
Constructs the reasoning DAG, evaluates multi-source synthesis with continuous JDS,
calculates continuous edge weights under Aris Directive #2 (alpha=0.2, beta=0.6, gamma=0.2),
applies 3-tier noise filtering with synthesis bridge protection (Aris Directive #2),
executes Intellectual Resonance Trigger & Collapse to Synthesis (Aris Directive #3),
applies Emergent Topology & Synthesis Gravity (Aris Directive #4),
enforces Cognitive Immunity, Negative Gravity Repulsion, and Paradox Containers (Aris Directive #5),
resolves dialectical paradoxes into Higher-Order Synthesis & Super-Anchors (Aris Directive #6),
and maps Cognitive Voids with Active Inquiry generation (Aris Directive #7).
"""

from typing import List, Dict, Tuple, Optional, Set, Any
import re
import uuid
import math

from app.icg.models import (
    ICGGraph, ClaimNode, EdgeEvidence, ContributionClass, NodeType,
    RelationType, MetricsSummary, TextSpan, Proposition, LayerSignals,
    EdgeStatus, EdgeWeightDetails, ResonanceMetadata, SynthesisMetadata,
    EmergentTopologyMetadata, ParadoxContainerMetadata,
    VoidType, VoidStatus, CognitiveVoidMetadata, InquiryResult,
)
from app.icg.discourse import extract_claim_nodes_from_text
from app.icg.nli_verifier import NLIVerifier
from app.icg.synthesis_verifier import SynthesisVerifier
from app.icg.external_search import ExternalSearchEngine
from app.icg.inquiry_generator import (
    InquiryGenerator,
    _extract_stems,
    _coverage,
    T_VOID,
    W_TENTATIVE_DEFAULT,
    MIN_ANCHOR_STEMS,
    REPULSION_CONTRADICTION_THRESHOLD,
)
from app.icg.epistemic_heatmap import recompute_neighbor_tensions


class ICGGraphBuilder:
    """
    Constructs the Intellectual Contribution Graph from a document text.
    Decomposes into EDUs, classifies contribution, evaluates continuous causal dependency,
    scores continuous edge weights, executes resonance triggers, applies synthesis gravity,
    evolves anchor nodes, manages paradox containers, resolves Higher-Order Synthesis, and computes metrics.
    """
    DOMAIN_LEXICON = {
        "Quantum Physics": ["квант", "фотон", "кубит", "когерентн", "резонатор", "лазер", "декогеренц", "диссипац", "quantum", "photon", "qubit", "coherence", "superposition", "decoherence"],
        "Deep Learning": ["нейросет", "градиент", "трансформер", "внимани", "батч", "adamw", "обучен", "loss", "neural", "transformer", "attention", "gradient", "embedding"],
        "Neuroscience": ["синапс", "нейрон", "мозг", "кора", "аксон", "дендрит", "памят", "нейробиолог", "brain", "neuron", "synapse", "cortex", "plasticity", "cognitive"],
        "Genetics & Medicine": ["ген", "crispr", "рнк", "днк", "cas9", "онколог", "опухол", "резистентност", "ингибитор", "мутац", "gene", "rna", "dna", "cleavage", "mutation", "therapy"],
        "Economics": ["инфляц", "ввп", "валют", "ставка", "рынок", "капитал", "gdp", "inflation", "market", "currency", "volatility", "monetary"],
        "Robotics & Engineering": ["робот", "привод", "пьезо", "шасси", "датчик", "канал", "шеннон", "robot", "actuator", "sensor", "throughput", "piezoelectric"]
    }

    def __init__(self, external_search: Optional[ExternalSearchEngine] = None, entailment_threshold: float = 0.04):
        self.nli = NLIVerifier()
        self.external_search = external_search or ExternalSearchEngine(
            embed_model=getattr(self.nli.hybrid, 'dense_model', None)
        )
        self.synthesis_verifier = SynthesisVerifier(
            nli_verifier=self.nli,
            external_search=self.external_search
        )
        self.entailment_threshold = entailment_threshold
        self.inquiry_generator = InquiryGenerator()  # Aris Directive #7

    def _is_tautology(self, text: str) -> bool:
        low = text.lower()
        vague_patterns = [
            r"всё?\s+связано\s+со\s+всем",
            r"всё?\s+взаимосвязано",
            r"наука\s+и\s+\w+\s+оба\s+(сложны|важны|интересны)",
            r"\w+\s+абстрактн\w*\s+и\s+непостижим",
            r"очень\s+сложный\s+орган",
            r"мы\s+ещё?\s+не\s+до\s+конца\s+понимаем",
            r"\w+\s+важн\w*\s+для\s+\w+,\s+так\s+же\s+как",
            r"все\s+утверждают",
            r"никто\s+не\s+знает",
            r"это\s+просто",
            r"на самом деле",
            r"стоит\s+только",
            r"важно\s+понимать",
            r"необходимо\s+отметить",
            r"следует\s+учесть",
            r"в\s+целом",
            r"как\s+правило",
            r"как\s+известно",
            r"всем\s+известно",
            r"как\s+говорится",
            r"семантическ",
            r"когнитивн",
            r"фрактальн",
            r"хаусдорф",
            r"тавтологическ",
            r"экзистенциальн",
            r"дистилляц",
            r"парадоксальн",
            r"hochma",
        ]
        taut_count = sum(1 for p in vague_patterns if re.search(p, low))
        if taut_count >= 2:
            return True
        words = low.split()
        unique = set(w.strip(".,;:!?—–-") for w in words if len(w) > 3)
        if len(words) > 5 and len(unique) / max(len(words), 1) < 0.35:
            return True
        return False

    def _is_vague_noise(self, text: str) -> bool:
        low = text.lower()
        noise_indicators = [
            r"всё?\s+взаимосвязано",
            r"всё?\s+связано\s+со\s+всем",
            r"абстрактн\w*\s+и\s+непостижим",
            r"очень\s+сложный",
            r"мы\s+ещё?\s+не\s+понимаем",
            r"\w+\s+важн\w*\s+для\s+\w+,\s+так\s+же\s+как",
            r"семантическ\w*\s+согласован",
            r"когнитивн\w*\s+резонанс",
            r"фрактальн\w*\s+размерност",
            r"хаусдорф",
            r"тавтологическ\w*\s+замыкан",
            r"экзистенциальн\w*\s+дистилляц",
            r"парадоксальн\w*\s+по\s+своей",
            r"hochma",
            r"эпистемическ\w*\s+целостн",
            r"аффективн\w*\s+коэффициент",
        ]
        return any(re.search(p, low) for p in noise_indicators)

    def _detect_domain(self, text: str) -> str:
        text_lower = text.lower()
        for domain, keywords in self.DOMAIN_LEXICON.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        return "General Science"

    def build_graph(
        self,
        document_id: str,
        text: str,
        sources_catalog: Optional[Dict[str, str]] = None,
        discipline: Optional[str] = None,
        use_llm: bool = False
    ) -> ICGGraph:
        raw_nodes = extract_claim_nodes_from_text(document_id, text)
        ecc = self.external_search.calculate_ecc(discipline)
        
        if not raw_nodes:
            return ICGGraph(
                document_id=document_id,
                nodes=[],
                edges=[],
                metrics_summary=MetricsSummary(external_corpus_coverage=ecc)
            )

        processed_nodes: List[ClaimNode] = []
        edges: List[EdgeEvidence] = []
        node_map: Dict[str, ClaimNode] = {}
        self.nli.reset_chain()

        for i, node in enumerate(raw_nodes):
            node.discipline_domain = self._detect_domain(node.span.raw_text)
            has_citations = len(node.sources_cited) > 0
            has_inference_connective = bool(
                node.proposition and (
                    node.proposition.modality in ["inference", "synthesis_claim"]
                )
            )
            is_hypothesis = bool(
                node.proposition and node.proposition.modality == "hypothesis"
            )

            # A. Grounded citation / Literature survey statement
            if (has_citations or node.proposition.modality == "fact_with_citation") and not has_inference_connective:
                node.contribution_class = ContributionClass.REPRODUCTION
                node.confidence = 0.95
                node.epistemic_confidence = round(0.95 * math.sqrt(ecc), 3)
                processed_nodes.append(node)
                node_map[node.id] = node
                continue

            # B. Author Hypothesis
            if is_hypothesis:
                node.contribution_class = ContributionClass.ORIGINAL_CONTRIBUTION
                node.confidence = 0.88
                node.epistemic_confidence = round(0.88 * math.sqrt(ecc), 3)
                processed_nodes.append(node)
                node_map[node.id] = node
                continue

            # C. Standalone raw assertion without reasoning connectives or citations
            if not has_inference_connective:
                is_tautology = self._is_tautology(node.span.raw_text)
                is_vague_noise = self._is_vague_noise(node.span.raw_text)
                
                if has_citations or node.proposition.modality == "fact_with_citation":
                    node.contribution_class = ContributionClass.REPRODUCTION
                    node.confidence = 0.95
                elif is_tautology or is_vague_noise:
                    node.contribution_class = ContributionClass.UNSUPPORTED
                    node.confidence = 0.10
                else:
                    # Aris Directive (Fact-Judge): a STANDALONE strong factual claim
                    # (absolutist marketing tone) with no external confirmation must be
                    # UNSUPPORTED, not a confident REPRODUCTION. Runs only in the Slow path.
                    _fact_res = self.nli.fact_judge(node.span.raw_text, None) if use_llm else None
                    if _fact_res is not None:
                        node.contribution_class = ContributionClass.UNSUPPORTED
                        node.confidence = 0.10
                    else:
                        node.contribution_class = ContributionClass.REPRODUCTION
                        node.confidence = 0.70
                node.epistemic_confidence = round(node.confidence * math.sqrt(ecc), 3)
                processed_nodes.append(node)
                node_map[node.id] = node
                continue

            # D. Reasoning Node with preceding premises
            # Aris Directive #20: anti-hallucination — even an inference-connective
            # statement that is vague/tautological noise must be rejected, otherwise
            # contentless claims dressed up as "Отсюда вытекает..." pass via the NLI.
            if self._is_tautology(node.span.raw_text) or self._is_vague_noise(node.span.raw_text):
                node.contribution_class = ContributionClass.UNSUPPORTED
                node.confidence = 0.10
                node.epistemic_confidence = round(0.10 * math.sqrt(ecc), 3)
                processed_nodes.append(node)
                node_map[node.id] = node
                continue

            candidate_premises = processed_nodes[:i]
            if not candidate_premises:
                node.contribution_class = ContributionClass.UNSUPPORTED
                node.confidence = 0.10
                node.epistemic_confidence = 0.05
                processed_nodes.append(node)
                node_map[node.id] = node
                continue

            # Execute 4-Step Continuous Causal Verification
            c_class, conf, synth_meta = self.synthesis_verifier.evaluate_claim_derivation(
                target_claim=node,
                candidate_premises=candidate_premises,
                use_llm=use_llm,
                entailment_threshold=self.entailment_threshold
            )

            node.contribution_class = c_class
            node.confidence = conf
            node.epistemic_confidence = round(conf * math.sqrt(ecc), 3)
            node.synthesis_metadata = synth_meta
            processed_nodes.append(node)
            node_map[node.id] = node

            self.nli.push_chain(node.span.raw_text)

            # Build and score edges with Aris Edge Weighting & Negative Gravity Repulsion
            if synth_meta and synth_meta.parent_premise_ids:
                is_synthesis_target = c_class in [
                    ContributionClass.SYNTHESIS,
                    ContributionClass.SOURCE_NOVEL_SYNTHESIS,
                    ContributionClass.HIGHER_ORDER_SYNTHESIS
                ]
                
                for parent_id in synth_meta.parent_premise_ids:
                    parent_node = node_map.get(parent_id)
                    parent_text = parent_node.span.raw_text if parent_node else ""
                    
                    rel_type = RelationType.INFERS
                    if is_synthesis_target:
                        rel_type = RelationType.SYNTHESIZES
                    elif c_class == ContributionClass.REPRODUCTION:
                        rel_type = RelationType.REPRODUCES
                    elif c_class == ContributionClass.ORIGINAL_CONTRIBUTION:
                        rel_type = RelationType.EXTENDS
                    elif c_class == ContributionClass.CONTRADICTORY:
                        rel_type = RelationType.NEGATIVE_GRAVITY_REPULSION
                    elif c_class == ContributionClass.UNKNOWN:
                        rel_type = RelationType.INSUFFICIENT_EVIDENCE

                    weight_details = self._score_edge_weight(
                        source_text=parent_text,
                        target_text=node.span.raw_text,
                        synth_meta=synth_meta,
                        parent_id=parent_id,
                        is_synthesis=is_synthesis_target,
                        base_conf=conf
                    )

                    edge = EdgeEvidence(
                        source_node_id=parent_id,
                        target_node_id=node.id,
                        relation_type=rel_type,
                        entailment_score=conf,
                        counterfactual_passed=bool(synth_meta.ablation and synth_meta.ablation.joint_dependency_score > 0.1),
                        evidence_excerpt=node.span.raw_text[:100],
                        weight=weight_details.final_weight,
                        status=weight_details.status,
                        weight_details=weight_details
                    )
                    edges.append(edge)

            elif c_class == ContributionClass.CONTRADICTORY:
                if candidate_premises:
                    contra_edge = EdgeEvidence(
                        source_node_id=candidate_premises[-1].id,
                        target_node_id=node.id,
                        relation_type=RelationType.NEGATIVE_GRAVITY_REPULSION,
                        contradiction_score=0.92,
                        counterfactual_passed=False,
                        evidence_excerpt=node.span.raw_text[:100],
                        weight=-0.80,
                        status=EdgeStatus.REPULSION_BOUNDARY,
                        weight_details=EdgeWeightDetails(
                            repulsion_force=-0.80,
                            final_weight=-0.80,
                            status=EdgeStatus.REPULSION_BOUNDARY
                        )
                    )
                    edges.append(contra_edge)

        # ---------------------------------------------------------------------
        # Aris Directive #3: Intellectual Resonance Trigger & Collapse to Synthesis
        # ---------------------------------------------------------------------
        self._evaluate_intellectual_resonance(processed_nodes, edges, node_map)

        # ---------------------------------------------------------------------
        # Aris Directive #4: Emergent Topology & Synthesis Gravity
        # ---------------------------------------------------------------------
        pruned_count = self._apply_emergent_topology(processed_nodes, edges, node_map)

        # ---------------------------------------------------------------------
        # Aris Directive #5: Cognitive Immunity, Evidence Escalation & Paradox Containers
        # ---------------------------------------------------------------------
        paradox_count, quarantined_count, repulsion_count = self._enforce_cognitive_immunity(
            processed_nodes, edges, node_map
        )

        # ---------------------------------------------------------------------
        # Aris Directive #6: Higher-Order Synthesis, Dynamic Tension & Super-Anchors
        # ---------------------------------------------------------------------
        resolved_count, tension_count, synth_link_count = self._resolve_higher_order_synthesis(
            processed_nodes, edges, node_map
        )

        # ---------------------------------------------------------------------
        # Aris Directive #7: Cognitive Void Mapping & Active Inquiry
        # ---------------------------------------------------------------------
        void_count, tentative_count, void_inquiries = self._detect_cognitive_voids(
            processed_nodes, edges, node_map
        )

        metrics = self._calculate_metrics(
            processed_nodes, edges, ecc, pruned_count,
            paradox_count, quarantined_count, repulsion_count,
            resolved_count, tension_count, synth_link_count,
            void_count, tentative_count, void_inquiries
        )

        return ICGGraph(
            document_id=document_id,
            nodes=processed_nodes,
            edges=edges,
            metrics_summary=metrics
        )

    def _score_edge_weight(
        self,
        source_text: str,
        target_text: str,
        synth_meta: Any,
        parent_id: str,
        is_synthesis: bool,
        base_conf: float
    ) -> EdgeWeightDetails:
        sim_semantic = 0.0
        if getattr(self.nli.hybrid, 'dense_model', None) is not None:
            try:
                from sentence_transformers.util import cos_sim
                e1 = self.nli.hybrid.dense_model.encode(source_text, show_progress_bar=False)
                e2 = self.nli.hybrid.dense_model.encode(target_text, show_progress_bar=False)
                sim_semantic = max(0.0, float(cos_sim(e1, e2)))
            except Exception:
                sim_semantic = 0.50
        else:
            s_stems = self.nli.hybrid._extract_content_stems(source_text)
            t_stems = self.nli.hybrid._extract_content_stems(target_text)
            overlap = sum(1 for ts in t_stems if any(self.nli.hybrid._stems_match(ss, ts) for ss in s_stems))
            sim_semantic = min(1.0, overlap / max(1, len(t_stems)))

        necessity = 0.0
        if synth_meta and synth_meta.ablation and synth_meta.ablation.causal_necessity_scores:
            necessity = synth_meta.ablation.causal_necessity_scores.get(parent_id, 0.0)
            necessity = min(1.0, necessity * 2.0)
        else:
            necessity = base_conf

        role_weight = 1.0 if is_synthesis else 0.80
        raw_score = 0.20 * sim_semantic + 0.60 * necessity + 0.20 * role_weight
        final_weight = round(min(1.0, max(0.0, raw_score)), 3)

        is_protected = is_synthesis or (synth_meta and len(synth_meta.parent_premise_ids) >= 2)
        
        if is_protected:
            if final_weight >= 0.05:
                status = EdgeStatus.CORE_ACTIVE_LINK
            else:
                status = EdgeStatus.WEAK_LINK
        else:
            if final_weight > 0.20:
                status = EdgeStatus.CORE_ACTIVE_LINK
            elif final_weight >= 0.10:
                status = EdgeStatus.WEAK_LINK
            else:
                status = EdgeStatus.DECORATIVE_MENTION

        return EdgeWeightDetails(
            semantic_similarity=round(sim_semantic, 3),
            causal_necessity=round(necessity, 3),
            discourse_role_weight=role_weight,
            raw_score=round(raw_score, 3),
            final_weight=final_weight,
            status=status,
            is_protected_synthesis_bridge=is_protected
        )

    def _evaluate_intellectual_resonance(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        node_map: Dict[str, ClaimNode]
    ) -> None:
        for node in nodes:
            incoming_edges = [
                e for e in edges
                if e.target_node_id == node.id and e.weight >= 0.15
            ]
            if len(incoming_edges) < 2:
                continue

            domain_max_weights: Dict[str, float] = {}
            for e in incoming_edges:
                parent = node_map.get(e.source_node_id)
                dom = parent.discipline_domain if parent and parent.discipline_domain else "General Science"
                domain_max_weights[dom] = max(domain_max_weights.get(dom, 0.0), e.weight)

            unique_domains = list(domain_max_weights.keys())
            
            if len(unique_domains) >= 3 or (len(unique_domains) >= 2 and sum(domain_max_weights.values()) >= 0.60):
                base_sum = sum(domain_max_weights.values())
                diversity_multiplier = 1.0 + (0.25 * (len(unique_domains) - 1))
                resonance_score = round(min(1.0, base_sum * diversity_multiplier), 3)

                is_active = len(unique_domains) >= 3 or resonance_score >= 0.65
                is_collapsed = resonance_score >= 0.70

                domains_str = " + ".join(unique_domains)
                res_log = f"[RESONANCE DETECTED] Node {node.id}: {domains_str} -> Potential Synthesis (R={resonance_score:.3f})"

                res_meta = ResonanceMetadata(
                    resonance_score=resonance_score,
                    is_resonance_active=is_active,
                    collapsed_to_synthesis=is_collapsed,
                    contributing_domains=unique_domains,
                    resonance_log=res_log
                )

                if node.synthesis_metadata is None:
                    node.synthesis_metadata = SynthesisMetadata(
                        parent_premise_ids=[e.source_node_id for e in incoming_edges],
                        resonance=res_meta
                    )
                else:
                    node.synthesis_metadata.resonance = res_meta

                if is_collapsed and node.contribution_class not in [ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS, ContributionClass.HIGHER_ORDER_SYNTHESIS]:
                    node.contribution_class = ContributionClass.SYNTHESIS
                    node.confidence = max(node.confidence, resonance_score)

    def _apply_emergent_topology(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        node_map: Dict[str, ClaimNode]
    ) -> int:
        synthesis_nodes = [
            n for n in nodes
            if n.contribution_class in [ContributionClass.SYNTHESIS, ContributionClass.SOURCE_NOVEL_SYNTHESIS, ContributionClass.HIGHER_ORDER_SYNTHESIS]
        ]

        for s_node in synthesis_nodes:
            res_score = 0.50
            domains_count = 2
            if s_node.synthesis_metadata and s_node.synthesis_metadata.resonance:
                res_score = s_node.synthesis_metadata.resonance.resonance_score
                domains_count = len(s_node.synthesis_metadata.resonance.contributing_domains)

            parent_ids = s_node.synthesis_metadata.parent_premise_ids if s_node.synthesis_metadata else []
            is_anchor = domains_count >= 3 or len(parent_ids) >= 4 or res_score >= 0.85
            if is_anchor and not s_node.is_contested:
                s_node.type = NodeType.ANCHOR
                s_node.is_anchor = True

            gravity_boost = round(0.25 * res_score, 3)

            for e in edges:
                if (e.target_node_id == s_node.id or e.source_node_id == s_node.id) and e.weight > 0:
                    new_w = round(min(1.0, e.weight + gravity_boost), 3)
                    e.weight = new_w
                    if e.weight_details:
                        e.weight_details.gravity_bonus = gravity_boost
                        e.weight_details.final_weight = new_w
                        if new_w >= 0.20:
                            e.weight_details.status = EdgeStatus.CORE_ACTIVE_LINK
                            e.status = EdgeStatus.CORE_ACTIVE_LINK

            if s_node.synthesis_metadata:
                s_node.synthesis_metadata.emergent_topology = EmergentTopologyMetadata(
                    is_anchor_hub=is_anchor,
                    gravity_boost=gravity_boost
                )

        pruned_edges_count = 0
        edge_lookup: Dict[Tuple[str, str], EdgeEvidence] = {
            (e.source_node_id, e.target_node_id): e for e in edges
        }

        for s_node in synthesis_nodes:
            s_id = s_node.id
            incoming_parents = [e.source_node_id for e in edges if e.target_node_id == s_id and e.weight >= 0.20]
            outgoing_targets = [e.target_node_id for e in edges if e.source_node_id == s_id and e.weight >= 0.20]

            for u_id in incoming_parents:
                w_u_s = edge_lookup[(u_id, s_id)].weight
                for v_id in outgoing_targets:
                    w_s_v = edge_lookup[(s_id, v_id)].weight
                    composite_weight = w_u_s * w_s_v

                    direct_edge = edge_lookup.get((u_id, v_id))
                    if direct_edge and direct_edge.weight < composite_weight and direct_edge.weight <= 0.35:
                        direct_edge.status = EdgeStatus.DECORATIVE_MENTION
                        if direct_edge.weight_details:
                            direct_edge.weight_details.status = EdgeStatus.DECORATIVE_MENTION
                            direct_edge.weight_details.is_bypassed_redundant = True
                        pruned_edges_count += 1
                        if s_node.synthesis_metadata and s_node.synthesis_metadata.emergent_topology:
                            s_node.synthesis_metadata.emergent_topology.bypassed_redundant_edges.append(direct_edge.edge_id)

        return pruned_edges_count

    def _enforce_cognitive_immunity(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        node_map: Dict[str, ClaimNode]
    ) -> Tuple[int, int, int]:
        paradox_count = 0
        quarantined_count = 0
        repulsion_count = 0

        # 1. Pairwise cross-premise dialectical conflict scan
        regular_claims = [n for n in nodes if n.type != NodeType.PARADOX_CONTAINER]
        for i in range(len(regular_claims)):
            for j in range(i + 1, len(regular_claims)):
                n_a = regular_claims[i]
                n_b = regular_claims[j]
                
                pair_res = self.nli.hybrid.verify_pair(n_a.span.raw_text, n_b.span.raw_text)
                if pair_res.contradiction_score >= 0.70:
                    existing = any(
                        (e.source_node_id == n_a.id and e.target_node_id == n_b.id) or
                        (e.source_node_id == n_b.id and e.target_node_id == n_a.id)
                        for e in edges
                    )
                    if not existing:
                        rep_edge = EdgeEvidence(
                            source_node_id=n_a.id,
                            target_node_id=n_b.id,
                            relation_type=RelationType.NEGATIVE_GRAVITY_REPULSION,
                            contradiction_score=pair_res.contradiction_score,
                            counterfactual_passed=False,
                            evidence_excerpt=n_b.span.raw_text[:100],
                            weight=-0.80,
                            status=EdgeStatus.REPULSION_BOUNDARY,
                            weight_details=EdgeWeightDetails(
                                repulsion_force=-0.80,
                                final_weight=-0.80,
                                status=EdgeStatus.REPULSION_BOUNDARY
                            )
                        )
                        edges.append(rep_edge)

        # 2. Mark Repulsion Boundaries
        for e in edges:
            if e.weight < 0 or e.status == EdgeStatus.REPULSION_BOUNDARY or e.relation_type in [RelationType.CONTRADICTS, RelationType.FALLACY_CONTRADICTION, RelationType.NEGATIVE_GRAVITY_REPULSION]:
                e.weight = -0.80
                e.status = EdgeStatus.REPULSION_BOUNDARY
                e.relation_type = RelationType.NEGATIVE_GRAVITY_REPULSION
                repulsion_count += 1

                target_node = node_map.get(e.target_node_id)
                if target_node:
                    target_node.is_contested = True
                    target_node.is_quarantined = True
                    target_node.is_anchor = False
                    target_node.type = NodeType.CLAIM
                    target_node.contested_reasons.append(f"Direct contradiction with node {e.source_node_id}")

        # 3. Evidence Escalation Scan
        for n in nodes:
            incoming = [e for e in edges if e.target_node_id == n.id]
            support_edges = [e for e in incoming if e.weight > 0.20]
            conflict_edges = [e for e in incoming if e.weight < 0]

            support_count = len(support_edges)
            conflict_count = len(conflict_edges)

            if conflict_count > 0:
                ratio = support_count / max(1, conflict_count)
                n.support_to_conflict_ratio = round(ratio, 2)

                if ratio <= 3.0:
                    n.is_quarantined = True
                    n.is_contested = True
                    n.is_anchor = False
                    n.type = NodeType.CLAIM
                    quarantined_count += 1
                else:
                    n.is_quarantined = False

        # 4. Instantiate Paradox Containers
        for e in edges:
            if e.status == EdgeStatus.REPULSION_BOUNDARY:
                s_node = node_map.get(e.source_node_id)
                t_node = node_map.get(e.target_node_id)
                if s_node and t_node:
                    paradox_id = f"paradox_{uuid.uuid4().hex[:6]}"
                    p_text = f"PARADOX CONTAINER: Dispute between [{s_node.span.raw_text[:40]}...] and [{t_node.span.raw_text[:40]}...]"
                    
                    p_meta = ParadoxContainerMetadata(
                        pole_a_node_ids=[s_node.id],
                        pole_b_node_ids=[t_node.id],
                        conflict_explanation=f"Source {s_node.id} asserts '{s_node.span.raw_text[:50]}' which dialectically opposes target {t_node.id} '{t_node.span.raw_text[:50]}'",
                        repulsion_force=-0.80
                    )
                    
                    paradox_node = ClaimNode(
                        id=paradox_id,
                        type=NodeType.PARADOX_CONTAINER,
                        contribution_class=ContributionClass.CONTRADICTORY,
                        span=TextSpan(start_char=0, end_char=len(p_text), raw_text=p_text),
                        synthesis_metadata=SynthesisMetadata(paradox_container=p_meta),
                        confidence=0.95
                    )
                    nodes.append(paradox_node)
                    node_map[paradox_id] = paradox_node
                    paradox_count += 1

        return paradox_count, quarantined_count, repulsion_count

    def _resolve_higher_order_synthesis(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        node_map: Dict[str, ClaimNode]
    ) -> Tuple[int, int, int]:
        resolved_count = 0
        tension_count = 0
        synthetic_link_count = 0

        paradox_containers = [n for n in nodes if n.type == NodeType.PARADOX_CONTAINER]
        if not paradox_containers:
            return 0, 0, 0

        regular_nodes = [n for n in nodes if n.type != NodeType.PARADOX_CONTAINER]

        for p_node in paradox_containers:
            p_meta = p_node.synthesis_metadata.paradox_container if p_node.synthesis_metadata else None
            if not p_meta or p_meta.is_resolved_to_higher_order:
                continue

            pole_a_ids = p_meta.pole_a_node_ids
            pole_b_ids = p_meta.pole_b_node_ids

            pole_a_nodes = [node_map[nid] for nid in pole_a_ids if nid in node_map]
            pole_b_nodes = [node_map[nid] for nid in pole_b_ids if nid in node_map]

            # Collect unique differentiating stems for Pole A and Pole B
            pole_a_stems = set().union(*[self.nli.hybrid._extract_content_stems(pa.span.raw_text) for pa in pole_a_nodes])
            pole_b_stems = set().union(*[self.nli.hybrid._extract_content_stems(pb.span.raw_text) for pb in pole_b_nodes])
            
            diff_a = pole_a_stems - pole_b_stems
            diff_b = pole_b_stems - pole_a_stems

            for candidate in regular_nodes:
                if candidate.id in pole_a_ids or candidate.id in pole_b_ids:
                    continue
                c_text = candidate.span.raw_text
                c_stems = self.nli.hybrid._extract_content_stems(c_text)
                
                has_pole_a_diff = any(any(self.nli.hybrid._stems_match(da, cs) for cs in c_stems) for da in diff_a)
                has_pole_b_diff = any(any(self.nli.hybrid._stems_match(db, cs) for cs in c_stems) for db in diff_b)

                if has_pole_a_diff and has_pole_b_diff:
                    joint_pole_texts = [p.span.raw_text for p in pole_a_nodes + pole_b_nodes]
                    bridge_nli = self.nli.verify_step(joint_pole_texts, c_text)

                    if bridge_nli.contradiction_score > 0.60 or not bridge_nli.is_valid_entailment(threshold=0.08):
                        candidate.contribution_class = ContributionClass.UNSUPPORTED
                        continue

                    p_meta.is_resolved_to_higher_order = True
                    p_meta.resolving_bridge_premise_ids.append(candidate.id)

                    candidate.contribution_class = ContributionClass.HIGHER_ORDER_SYNTHESIS
                    candidate.type = NodeType.SUPER_ANCHOR
                    candidate.is_super_anchor = True
                    candidate.is_anchor = True
                    candidate.resonance_frequency = 2.50
                    candidate.confidence = 0.98

                    for e in edges:
                        if (e.source_node_id in pole_a_ids and e.target_node_id in pole_b_ids) or \
                           (e.source_node_id in pole_b_ids and e.target_node_id in pole_a_ids):
                            e.weight = 0.15
                            e.status = EdgeStatus.DYNAMIC_TENSION
                            e.relation_type = RelationType.DYNAMIC_TENSION
                            if e.weight_details:
                                e.weight_details.tension_force = 0.15
                                e.weight_details.final_weight = 0.15
                                e.weight_details.status = EdgeStatus.DYNAMIC_TENSION
                            tension_count += 1

                    for pole_node in pole_a_nodes + pole_b_nodes:
                        pole_node.is_quarantined = False
                        pole_node.is_contested = False

                        synth_edge = EdgeEvidence(
                            source_node_id=pole_node.id,
                            target_node_id=candidate.id,
                            relation_type=RelationType.SYNTHETIC_LINK,
                            entailment_score=0.95,
                            counterfactual_passed=True,
                            evidence_excerpt=c_text[:100],
                            weight=0.90,
                            status=EdgeStatus.SYNTHETIC_LINK,
                            weight_details=EdgeWeightDetails(
                                final_weight=0.90,
                                status=EdgeStatus.SYNTHETIC_LINK
                            )
                        )
                        edges.append(synth_edge)
                        synthetic_link_count += 1

                    resolved_count += 1
                    break

        # Aris Directive (CASE_26-28 pruning): remove paradox containers that did NOT
        # resolve into Higher-Order Synthesis. An unresolved container follows a
        # CONTRADICTORY node but brings no new synthesis/proof -> it must not pollute
        # the final ICG. Only resolved (resolving-bridge) containers stay meaningful.
        unresolved = [n for n in paradox_containers
                      if not (n.synthesis_metadata and n.synthesis_metadata.paradox_container
                              and n.synthesis_metadata.paradox_container.is_resolved_to_higher_order)]
        for n in unresolved:
            try:
                nodes.remove(n)
            except ValueError:
                pass
            node_map.pop(n.id, None)

        return resolved_count, tension_count, synthetic_link_count

    # =========================================================================
    # Aris Directive #7: Cognitive Void Mapping & Active Inquiry
    # =========================================================================
    def _detect_cognitive_voids(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        node_map: Dict[str, ClaimNode],
    ) -> tuple:
        """
        Scan all (ANCHOR, SUPER_ANCHOR) pairs for structural reasoning gaps.
        A COGNITIVE_VOID is declared when:
          - coverage(stems_A, stems_B) < T_VOID (=0.30)
          - max_edge_weight(A→B) < T_VOID (no strong direct path)
          - Both anchors have >= MIN_ANCHOR_STEMS unique content stems

        Void classification:
          EMPIRICAL_GAP          — no edges exist at all between the pair
          LOGICAL_DISCONTINUITY  — edges exist but coverage is low
          CONTRADICTORY_SILENCE  — REPULSION_BOUNDARY edge exists between them

        Returns:
            (void_count, tentative_count, inquiries: List[InquiryResult])
        """
        import json as _json

        # Collect significant anchor nodes only (Aris: avoid noise from tiny nodes)
        anchor_nodes = [
            n for n in nodes
            if n.type in (NodeType.ANCHOR, NodeType.SUPER_ANCHOR)
            and n.type != NodeType.PARADOX_CONTAINER
            and n.type != NodeType.COGNITIVE_VOID
            and len(_extract_stems(n.span.raw_text)) >= MIN_ANCHOR_STEMS
        ]

        if len(anchor_nodes) < 2:
            return 0, 0, []

        # Build edge lookup: (src_id, tgt_id) -> max weight
        edge_weight_map: Dict[tuple, float] = {}
        repulsion_pairs: Set[tuple] = set()
        for e in edges:
            key = (e.source_node_id, e.target_node_id)
            rkey = (e.target_node_id, e.source_node_id)
            edge_weight_map[key] = max(edge_weight_map.get(key, -999), e.weight)
            edge_weight_map[rkey] = max(edge_weight_map.get(rkey, -999), e.weight)
            if e.status == EdgeStatus.REPULSION_BOUNDARY or e.weight <= REPULSION_CONTRADICTION_THRESHOLD:
                repulsion_pairs.add(key)
                repulsion_pairs.add(rkey)

        void_count = 0
        tentative_count = 0
        inquiries: List[InquiryResult] = []

        # Track already-processed pairs to avoid symmetric duplicates
        processed_pairs: Set[tuple] = set()

        for i, node_a in enumerate(anchor_nodes):
            stems_a = _extract_stems(node_a.span.raw_text)
            for j, node_b in enumerate(anchor_nodes):
                if i >= j:
                    continue
                pair_key = (node_a.id, node_b.id)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                stems_b = _extract_stems(node_b.span.raw_text)
                cov = _coverage(stems_a, stems_b)
                max_w = max(
                    edge_weight_map.get((node_a.id, node_b.id), -999),
                    edge_weight_map.get((node_b.id, node_a.id), -999),
                )
                if max_w == -999:
                    max_w = 0.0

                # Significance filter: only declare a void if there is a
                # semantic proximity hint but no sufficient logical bridge
                # (prevents voids between completely unrelated tangential nodes)
                has_any_edge = (
                    (node_a.id, node_b.id) in edge_weight_map
                    or (node_b.id, node_a.id) in edge_weight_map
                )

                if cov >= T_VOID or max_w >= T_VOID:
                    # Well-connected pair — no void
                    continue

                # There is a void. Classify it.
                is_repulsion = (
                    (node_a.id, node_b.id) in repulsion_pairs
                    or (node_b.id, node_a.id) in repulsion_pairs
                )

                if is_repulsion:
                    void_type = VoidType.CONTRADICTORY_SILENCE
                elif has_any_edge:
                    void_type = VoidType.LOGICAL_DISCONTINUITY
                else:
                    # Only create EMPIRICAL_GAP if there is some semantic proximity
                    # (cov > 0 but < T_VOID), not for completely alien concepts
                    if cov <= 0.0:
                        continue  # Truly alien pair — not a meaningful void
                    void_type = VoidType.EMPIRICAL_GAP

                # Create COGNITIVE_VOID node
                void_id = f"void_{uuid.uuid4().hex[:8]}"
                void_span = TextSpan(
                    start_char=0,
                    end_char=0,
                    page=0,
                    sentence_idx=-1,
                    raw_text=(
                        f"[COGNITIVE_VOID:{void_type.value}] "
                        f"Gap between {node_a.id[:8]} and {node_b.id[:8]}"
                    )
                )
                void_meta = CognitiveVoidMetadata(
                    void_type=void_type,
                    void_status=VoidStatus.OPEN,
                    pole_a_anchor_id=node_a.id,
                    pole_b_anchor_id=node_b.id,
                    gap_coverage_score=round(cov, 4),
                    max_path_weight=round(max_w, 4),
                )
                void_node = ClaimNode(
                    id=void_id,
                    type=NodeType.COGNITIVE_VOID,
                    contribution_class=ContributionClass.UNKNOWN,
                    span=void_span,
                    synthesis_metadata=SynthesisMetadata(cognitive_void=void_meta),
                    confidence=0.0,
                    epistemic_confidence=0.0,
                )
                nodes.append(void_node)
                node_map[void_id] = void_node

                # Create TENTATIVE edges: A → VOID and B → VOID
                tentative_edge_ids: List[str] = []
                for pole_id in [node_a.id, node_b.id]:
                    t_edge = EdgeEvidence(
                        source_node_id=pole_id,
                        target_node_id=void_id,
                        relation_type=RelationType.TENTATIVE_BRIDGE,
                        entailment_score=cov,
                        counterfactual_passed=False,
                        evidence_excerpt=f"[tentative bridge to {void_type.value}]",
                        weight=W_TENTATIVE_DEFAULT,
                        status=EdgeStatus.TENTATIVE,
                        weight_details=EdgeWeightDetails(
                            final_weight=W_TENTATIVE_DEFAULT,
                            status=EdgeStatus.TENTATIVE,
                        )
                    )
                    edges.append(t_edge)
                    tentative_edge_ids.append(t_edge.edge_id)
                    tentative_count += 1

                # Generate structured inquiry
                inquiry = self.inquiry_generator.generate(
                    void_node_id=void_id,
                    pole_a_id=node_a.id,
                    pole_b_id=node_b.id,
                    text_a=node_a.span.raw_text,
                    text_b=node_b.span.raw_text,
                    void_type=void_type,
                    gap_coverage_score=cov,
                    max_path_weight=max_w,
                    tentative_edge_ids=tentative_edge_ids,
                )
                # Store inquiry back into void node metadata
                void_node.synthesis_metadata.cognitive_void.inquiry = inquiry
                inquiries.append(inquiry)
                void_count += 1

        return void_count, tentative_count, inquiries

    def _calculate_metrics(
        self,
        nodes: List[ClaimNode],
        edges: List[EdgeEvidence],
        ecc: float = 0.85,
        pruned_count: int = 0,
        paradox_count: int = 0,
        quarantined_count: int = 0,
        repulsion_count: int = 0,
        resolved_count: int = 0,
        tension_count: int = 0,
        synth_link_count: int = 0,
        void_count: int = 0,
        tentative_count: int = 0,
        void_inquiries: Optional[List] = None,
    ) -> MetricsSummary:
        # Exclude structural meta-nodes (PARADOX_CONTAINER, COGNITIVE_VOID) from contribution ratios
        _excluded_types = {NodeType.PARADOX_CONTAINER, NodeType.COGNITIVE_VOID}
        total = max(1, len([n for n in nodes if n.type not in _excluded_types]))
        counts = {cls: 0 for cls in ContributionClass}
        for n in nodes:
            if n.type not in _excluded_types:
                counts[n.contribution_class] = counts.get(n.contribution_class, 0) + 1

        repro_ratio = round(counts[ContributionClass.REPRODUCTION] / total, 3)
        synth_ratio = round(counts[ContributionClass.SYNTHESIS] / total, 3)
        src_nov_synth_ratio = round(counts[ContributionClass.SOURCE_NOVEL_SYNTHESIS] / total, 3)
        higher_order_ratio = round(counts[ContributionClass.HIGHER_ORDER_SYNTHESIS] / total, 3)
        orig_ratio = round(counts[ContributionClass.ORIGINAL_CONTRIBUTION] / total, 3)
        infer_ratio = round(counts[ContributionClass.INFERENCE] / total, 3)
        unsup_ratio = round(counts[ContributionClass.UNSUPPORTED] / total, 3)
        contradict_ratio = round(counts[ContributionClass.CONTRADICTORY] / total, 3)
        unknown_ratio = round(counts[ContributionClass.UNKNOWN] / total, 3)

        novelties = [
            n.synthesis_metadata.source_novelty_score 
            for n in nodes if n.synthesis_metadata and n.synthesis_metadata.source_novelty_score > 0
        ]
        avg_novelty = round(sum(novelties) / len(novelties), 3) if novelties else 0.20

        synthesis_count = counts[ContributionClass.SYNTHESIS] + counts[ContributionClass.SOURCE_NOVEL_SYNTHESIS] + counts[ContributionClass.HIGHER_ORDER_SYNTHESIS]
        synthesis_depth = round(min(1.0, (synthesis_count * 2.0) / total), 3)
        inference_depth = round(min(1.0, (counts[ContributionClass.INFERENCE] * 1.5) / total), 3)
        source_integration = round(min(1.0, (counts[ContributionClass.REPRODUCTION] * 0.5 + synthesis_count * 1.0) / total), 3)

        supported_nodes = set()
        for e in edges:
            if e.status in [EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK] and e.relation_type not in [RelationType.FALLACY_UNSUPPORTED, RelationType.FALLACY_CONTRADICTION, RelationType.INSUFFICIENT_EVIDENCE, RelationType.NEGATIVE_GRAVITY_REPULSION]:
                supported_nodes.add(e.target_node_id)
        evidence_coverage = round(min(1.0, len(supported_nodes) / max(1, total - counts[ContributionClass.REPRODUCTION])), 3)

        valid_edge_scores = [
            e.entailment_score for e in edges 
            if e.status not in [EdgeStatus.DECORATIVE_MENTION, EdgeStatus.REPULSION_BOUNDARY] and e.relation_type not in [RelationType.FALLACY_UNSUPPORTED, RelationType.FALLACY_CONTRADICTION, RelationType.INSUFFICIENT_EVIDENCE, RelationType.NEGATIVE_GRAVITY_REPULSION]
        ]
        coherence = round(sum(valid_edge_scores) / len(valid_edge_scores), 3) if valid_edge_scores else 0.10

        # Graph Density & Edge Filtering Metrics
        core_edges = sum(1 for e in edges if e.status in [EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK])
        weak_edges = sum(1 for e in edges if e.status == EdgeStatus.WEAK_LINK)
        decorative_edges = sum(1 for e in edges if e.status == EdgeStatus.DECORATIVE_MENTION)
        
        max_possible_edges = total * (total - 1) if total > 1 else 1
        density_raw = round(len(edges) / max_possible_edges, 3)
        density_filtered = round(core_edges / max_possible_edges, 3)

        # Intellectual Resonance & Emergent Topology Metrics
        res_nodes = [
            n.synthesis_metadata.resonance.resonance_score
            for n in nodes if n.synthesis_metadata and n.synthesis_metadata.resonance and n.synthesis_metadata.resonance.is_resonance_active
        ]
        active_resonance_count = len(res_nodes)
        max_res_score = max(res_nodes) if res_nodes else 0.0
        anchor_count = sum(1 for n in nodes if n.is_anchor)
        super_anchor_count = sum(1 for n in nodes if n.is_super_anchor)

        pos_score = (
            0.25 * avg_novelty +
            0.25 * synthesis_depth +
            0.20 * inference_depth +
            0.15 * source_integration +
            0.15 * evidence_coverage
        )
        
        unsup_penalty = unsup_ratio * 0.40
        contradict_penalty = contradict_ratio * 0.60
        raw_ics = max(0.0, pos_score - unsup_penalty - contradict_penalty) * coherence
        ics = round(min(1.0, raw_ics), 3)

        global_epistemic = round(ics * math.sqrt(ecc), 3)

        # Serialize void_inquiries to JSON for MetricsSummary
        import json as _json
        void_inquiries = void_inquiries or []
        void_map = [
            {
                "void_node_id": inq.void_node_id,
                "void_type": inq.void_type.value,
                "pole_a": inq.pole_a_anchor_id,
                "pole_b": inq.pole_b_anchor_id,
                "inquiry_question": inq.inquiry_question,
                "hypotheses": inq.hypotheses,
            }
            for inq in void_inquiries
        ]
        void_map_json = _json.dumps(void_map, ensure_ascii=False)

        return MetricsSummary(
            reproduction_ratio=repro_ratio,
            synthesis_ratio=synth_ratio,
            source_novel_synthesis_ratio=src_nov_synth_ratio,
            higher_order_synthesis_ratio=higher_order_ratio,
            original_contribution_ratio=orig_ratio,
            inference_ratio=infer_ratio,
            unsupported_ratio=unsup_ratio,
            contradictory_ratio=contradict_ratio,
            unknown_ratio=unknown_ratio,
            novelty_score=avg_novelty,
            synthesis_depth=synthesis_depth,
            inference_depth=inference_depth,
            source_integration=source_integration,
            evidence_coverage=evidence_coverage,
            reasoning_coherence=coherence,
            external_corpus_coverage=ecc,
            global_epistemic_confidence=global_epistemic,
            graph_density_raw=density_raw,
            graph_density_filtered=density_filtered,
            core_edges_count=core_edges,
            weak_edges_count=weak_edges,
            decorative_edges_count=decorative_edges,
            active_resonance_nodes_count=active_resonance_count,
            max_resonance_score=max_res_score,
            anchor_nodes_count=anchor_count,
            super_anchor_nodes_count=super_anchor_count,
            pruned_redundant_edges_count=pruned_count,
            paradox_containers_count=paradox_count,
            resolved_paradoxes_count=resolved_count,
            quarantined_nodes_count=quarantined_count,
            repulsion_edges_count=repulsion_count,
            dynamic_tension_edges_count=tension_count,
            synthetic_link_edges_count=synth_link_count,
            cognitive_voids_count=void_count,
            tentative_edges_count=tentative_count,
            void_map_json=void_map_json,
            intellectual_contribution_score=ics
        )

    # =========================================================================
    # Aris Directive #8: Inquiry Resolver — Void → Knowledge Transformation
    # =========================================================================

    # Resolution threshold: evidence must meet this confidence to close a void
    VOID_RESOLUTION_THRESHOLD: float = 0.70

    def resolve_cognitive_void(
        self,
        graph: "ICGGraph",
        void_id: str,
        evidence_text: str,
        confidence_score: float,
    ) -> Dict[str, Any]:
        """
        Process an answer to a Cognitive Void's Inquiry and close the gap.

        Algorithm:
          1. Locate COGNITIVE_VOID node by void_id in graph.nodes
          2. If confidence_score < VOID_RESOLUTION_THRESHOLD → return INSUFFICIENT_CONFIDENCE
          3. Mark VoidStatus → RESOLVED, archive evidence in CognitiveVoidMetadata
          4. Remove TENTATIVE_BRIDGE edges from graph.edges
          5. Create direct A → B RESOLVED_BRIDGE edge with weight = confidence_score
          6. Propagate coverage refresh: recalculate epistemic_confidence for A and B
          7. Update MetricsSummary counters
          8. Return resolution report dict

        Args:
            graph:            ICGGraph to mutate in-place
            void_id:          ID of the COGNITIVE_VOID node to resolve
            evidence_text:    External evidence text that answers the inquiry
            confidence_score: Float in [0.0, 1.0] — analyst confidence in the evidence

        Returns:
            dict with keys: status, void_id, new_edge_id, resolved_weight, message
        """
        # Locate the void node
        void_node = next((n for n in graph.nodes if n.id == void_id), None)
        if void_node is None:
            return {"status": "NOT_FOUND", "void_id": void_id, "message": f"Node {void_id} not in graph"}

        if void_node.type != NodeType.COGNITIVE_VOID:
            return {"status": "NOT_A_VOID", "void_id": void_id, "message": f"Node {void_id} is {void_node.type}, not COGNITIVE_VOID"}

        void_meta = void_node.synthesis_metadata.cognitive_void if void_node.synthesis_metadata else None
        if void_meta is None:
            return {"status": "NO_METADATA", "void_id": void_id, "message": "CognitiveVoidMetadata missing"}

        if void_meta.void_status == VoidStatus.RESOLVED:
            return {"status": "ALREADY_RESOLVED", "void_id": void_id, "message": "Void is already resolved"}

        # Confidence gate (Aris: strict threshold)
        if confidence_score < self.VOID_RESOLUTION_THRESHOLD:
            return {
                "status": "INSUFFICIENT_CONFIDENCE",
                "void_id": void_id,
                "message": f"confidence_score={confidence_score:.3f} < threshold={self.VOID_RESOLUTION_THRESHOLD}",
                "required_confidence": self.VOID_RESOLUTION_THRESHOLD,
            }

        pole_a_id = void_meta.pole_a_anchor_id
        pole_b_id = void_meta.pole_b_anchor_id

        # Archive evidence in void metadata (Aris: archival, not deletion)
        void_meta.void_status = VoidStatus.RESOLVED
        void_meta.resolved_evidence_text = evidence_text[:500]
        void_meta.resolved_confidence = round(confidence_score, 4)

        # Remove TENTATIVE_BRIDGE edges pointing to/from this void
        tentative_ids_to_remove: Set[str] = set()
        if void_meta.inquiry:
            tentative_ids_to_remove = set(void_meta.inquiry.tentative_edge_ids)
        graph.edges = [
            e for e in graph.edges
            if not (
                e.edge_id in tentative_ids_to_remove
                or (e.status == EdgeStatus.TENTATIVE and void_id in (e.source_node_id, e.target_node_id))
            )
        ]

        # Infer relation type from evidence_text via NLI
        rel_type = self._infer_relation_type_from_evidence(evidence_text)

        # Create A → B direct RESOLVED_BRIDGE edge
        resolved_weight = round(min(0.95, confidence_score * 0.95), 4)  # Cap at 0.95
        edge_status = EdgeStatus.CORE_ACTIVE_LINK if resolved_weight > 0.20 else EdgeStatus.WEAK_LINK

        resolved_edge = EdgeEvidence(
            source_node_id=pole_a_id,
            target_node_id=pole_b_id,
            relation_type=rel_type,
            entailment_score=confidence_score,
            counterfactual_passed=True,
            evidence_excerpt=evidence_text[:100],
            weight=resolved_weight,
            status=edge_status,
            weight_details=EdgeWeightDetails(
                final_weight=resolved_weight,
                status=edge_status,
            )
        )
        graph.edges.append(resolved_edge)
        void_meta.resolved_edge_id = resolved_edge.edge_id

        # Local coverage propagation: refresh epistemic_confidence for anchor poles
        self._propagate_coverage_refresh(graph, pole_a_id, pole_b_id, resolved_weight)

        # Aris Directive #9: Recompute Tension for neighboring cognitive voids
        affected_neighbor_tensions = recompute_neighbor_tensions(void_id, graph)

        # Update MetricsSummary: decrement void count, increment resolved bridges
        ms = graph.metrics_summary
        ms.cognitive_voids_count = max(0, ms.cognitive_voids_count - 1)
        ms.tentative_edges_count = max(0, ms.tentative_edges_count - 2)
        if edge_status == EdgeStatus.CORE_ACTIVE_LINK:
            ms.core_edges_count += 1
        else:
            ms.weak_edges_count += 1

        return {
            "status": "RESOLVED",
            "void_id": void_id,
            "new_edge_id": resolved_edge.edge_id,
            "resolved_weight": resolved_weight,
            "relation_type": rel_type.value,
            "pole_a": pole_a_id,
            "pole_b": pole_b_id,
            "affected_neighbor_tensions": affected_neighbor_tensions,
            "message": f"Void resolved. Bridge edge created: {pole_a_id[:8]} → {pole_b_id[:8]} (W={resolved_weight})",
        }

    def _infer_relation_type_from_evidence(self, evidence_text: str) -> "RelationType":
        """
        Lightweight heuristic: infer the most appropriate RelationType from
        the evidence text (no LLM call — stemmer + keyword matching).
        Falls back to ASSOCIATION if no match.
        """
        text_lower = evidence_text.lower()
        # Synthesis / causal keywords
        if any(kw in text_lower for kw in ["синтез", "объединяет", "интегрирует", "combines", "synthesizes", "bridges"]):
            return RelationType.SYNTHESIZES
        if any(kw in text_lower for kw in ["следует", "вытекает", "implies", "infers", "entails", "therefore"]):
            return RelationType.INFERS
        if any(kw in text_lower for kw in ["расширяет", "развивает", "extends", "builds on", "elaborates"]):
            return RelationType.EXTENDS
        if any(kw in text_lower for kw in ["воспроизводит", "повторяет", "reproduces", "duplicates"]):
            return RelationType.REPRODUCES
        # Default: neutral association
        return RelationType.ASSOCIATION

    def _propagate_coverage_refresh(
        self,
        graph: "ICGGraph",
        pole_a_id: str,
        pole_b_id: str,
        new_edge_weight: float,
    ) -> None:
        """
        After void resolution, recalculate epistemic_confidence for both anchor poles.
        Coverage boost: resolution of a void can only increase epistemic_confidence —
        we take max(prior_value, new_value) to guarantee monotonic improvement.
        """
        ecc = graph.metrics_summary.external_corpus_coverage
        for node in graph.nodes:
            if node.id in (pole_a_id, pole_b_id):
                prior_epistemic = node.epistemic_confidence
                # Count incoming/outgoing core edges after resolution
                connected_edges = [
                    e for e in graph.edges
                    if (e.source_node_id == node.id or e.target_node_id == node.id)
                    and e.status in (EdgeStatus.CORE_ACTIVE_LINK, EdgeStatus.SYNTHETIC_LINK)
                ]
                core_edge_count = len(connected_edges)
                # Coverage boost delta: each new core edge adds a proportional boost
                # Boost = confidence * sqrt(ecc) + boost_delta
                boost_delta = round(new_edge_weight * 0.05 * min(core_edge_count, 5), 4)
                candidate = round(min(1.0, node.confidence * math.sqrt(ecc) + boost_delta), 4)
                # Guarantee monotonic improvement: never let resolution decrease confidence
                node.epistemic_confidence = max(prior_epistemic, candidate)
