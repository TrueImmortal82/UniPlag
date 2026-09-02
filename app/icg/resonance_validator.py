"""
Resonance Output Validator & Utility Gain Engine (app/icg/resonance_validator.py)
Aris Directive #17: Synthesis of Intellectual Resonance & Output Verification

Implements:
  1. Synthesis Thesis Generation & Structured Semantic Output.
  2. Information-Theoretic Tautology & Entropy Filter (A x B = C, not trivial A + B).
  3. Utility Gain Computation: U_gain = Novelty * ExplanatoryPower * Verifiability * (1.0 - TautologyScore).
  4. Circular Reasoning & Intellectual Echo Loop Detection with Automatic Ghost Degradation.
  5. Utility-Based Bridge Damping and Graph Quality Protection.
"""

from __future__ import annotations

import re
import math
from typing import List, Dict, Tuple, Optional, Set

from app.icg.models import (
    ICGGraph, ClaimNode, NodeType, EdgeEvidence, RelationType, EdgeStatus,
    ProposedCrossDomainBridge, SynthesisThesis, SynthesisVectorScore,
)
from app.icg.nli_verifier import NLIVerifier


class ResonanceOutputValidator:
    """
    Validates that synthetic bridges and tunneling outputs deliver genuine, non-tautological
    intellectual utility and are free from self-referential circular reasoning loops (Aris Directive #17).
    """

    STOP_WORDS = {
        "и", "в", "на", "с", "по", "для", "к", "о", "об", "за", "из", "от", "при",
        "до", "то", "что", "как", "так", "это", "этот", "эта", "эти", "быть", "является",
        "были", "было", "все", "всех", "но", "а", "или", "не", "же", "уже", "между",
        "and", "in", "on", "with", "for", "to", "of", "about", "from", "at", "by",
        "is", "are", "was", "were", "the", "a", "an", "that", "which", "as", "both",
    }

    VAGUE_WORDS = {
        "неопределенн", "неопределен", "сложн", "разн", "похож", "различн", "мног",
        "некоторы", "абстрактн", "общ", "весьма", "достаточн", "complex", "vague", "similar", "different",
    }

    OPERATIONAL_WORDS = {
        # Mathematical / statistical core
        "спектральн", "плотност", "матриц", "ковариац", "распределен", "изоморф",
        "корреляц", "уравнен", "теорем", "инвариант", "энтропи", "формализм", "топологи",
        "градиент", "динамик", "квантил", "вероятност", "функциональн", "собственн",
        "вектор", "тензор", "гамильтон", "оператор", "проекцион",
        # Biophysics operational terms
        "туннельн", "туннелирован", "проводимост", "барьер", "нанометр", "субнанометр",
        "порог", "пороговый", "потенциал", "синаптическ", "рецептор", "кальциев",
        "нейромедиатор", "гиппокамп", "аксон", "миелин", "деполяризац", "реполяризац",
        "nmda", "ltp", "atp", "nav",
        # Quantum physics operational terms
        "декогеренц", "суперпозиц", "гамов", "белл", "шрёдингер", "запутанност",
        "коллапс", "нелокальн", "локальн", "плансков", "квантов", "фотон", "кубит",
        # Finance / economics operational terms
        "парет", "арбитраж", "волатильност", "дисконтирован", "марковиц",
        "value-at-risk", "var", "black-scholes",
        # English equivalents
        "spectral", "density", "matrix", "covariance", "isomorph",
        "correlation", "equation", "theorem", "invariant", "entropy", "formalism",
        "tunneling", "conductance", "barrier", "threshold", "synaptic", "receptor",
        "decoherence", "superposition", "entanglement", "projection", "hamiltonian",
    }

    def __init__(self, nli_verifier: Optional[NLIVerifier] = None):
        self.nli_verifier = nli_verifier or NLIVerifier()

    def _extract_concepts(self, text: str) -> Set[str]:
        words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]{3,}', text.lower())
        return {w for w in words if w not in self.STOP_WORDS}

    def generate_synthesis_thesis(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
        synthesis_claim: str,
    ) -> SynthesisThesis:
        """
        Generates and evaluates a structured SynthesisThesis from a proposed/reinforced bridge (Aris Directive #17).
        """
        u = next((n for n in graph.nodes if n.id == bridge.source_node_id), None)
        v = next((n for n in graph.nodes if n.id == bridge.target_node_id), None)

        u_text = u.span.raw_text if u else ""
        v_text = v.span.raw_text if v else ""

        u_concepts = self._extract_concepts(u_text)
        v_concepts = self._extract_concepts(v_text)
        thesis_concepts = self._extract_concepts(synthesis_claim)

        # 1. Information Entropy / Tautology Analysis (Aris Requirement #1)
        # Novel concepts introduced in thesis that are absent from both premises
        new_concepts = thesis_concepts - (u_concepts | v_concepts)
        substantive_new_concepts = {
            w for w in new_concepts
            if not any(w.startswith(vw) for vw in self.VAGUE_WORDS)
        }
        vague_matches = sum(1 for w in thesis_concepts if any(w.startswith(vw) for vw in self.VAGUE_WORDS))
        total_concepts = max(1, len(thesis_concepts))

        if len(substantive_new_concepts) == 0:
            # Zero substantive new concepts: Pure trivial rewording (A + B without C)
            tautology_score = 0.95
        elif len(substantive_new_concepts) == 1:
            tautology_score = 0.70
        else:
            # Substantive new conceptual framework introduced
            novel_ratio = len(substantive_new_concepts) / total_concepts
            tautology_score = round(max(0.05, 1.0 - novel_ratio * 1.6), 4)

        if vague_matches >= 2:
            tautology_score = min(1.0, tautology_score + 0.35)

        # 2. Verifiability / Operationalization (Aris Requirement #3)
        op_matches = sum(1 for w in thesis_concepts if any(w.startswith(ow) for ow in self.OPERATIONAL_WORDS))
        verifiability_score = round(min(1.0, 0.30 + op_matches * 0.25), 4)

        # 3. Novelty & Explanatory Power via NLI
        nli_u = self.nli_verifier.hybrid.verify_pair(u_text, synthesis_claim)
        nli_v = self.nli_verifier.hybrid.verify_pair(v_text, synthesis_claim)
        
        # Explanatory power: scaled composite coherence of both poles
        base_entail = (nli_u.entailment_score + nli_v.entailment_score) / 2.0
        explanatory_power = round(min(1.0, max(0.60, base_entail * 1.60 + 0.15)), 4)

        # Novelty: ratio of substantive new conceptual grounding
        novelty_score = round(min(1.0, (len(substantive_new_concepts) / max(1, len(thesis_concepts))) * 1.5 + 0.30), 4)

        # 4. Utility Gain Calculation (Aris Requirement #3)
        # U_gain = Novelty * ExplanatoryPower * Verifiability * (1.0 - TautologyScore)
        utility_gain = round(
            novelty_score * explanatory_power * verifiability_score * max(0.0, 1.0 - tautology_score),
            4
        )

        is_tautological = (tautology_score >= 0.70 or utility_gain < 0.20)

        thesis = SynthesisThesis(
            bridge_id=bridge.bridge_id,
            source_node_id=bridge.source_node_id,
            target_node_id=bridge.target_node_id,
            synthesis_claim=synthesis_claim,
            novelty_score=novelty_score,
            explanatory_power=explanatory_power,
            verifiability_score=verifiability_score,
            tautology_score=tautology_score,
            utility_gain=utility_gain,
            is_circular=False,
            is_tautological=is_tautological,
        )
        return thesis

    def detect_and_degrade_circular_loops(
        self,
        graph: ICGGraph,
    ) -> List[List[str]]:
        """
        Detects self-referential synthetic loops and degrades circular edges into ghost status (Aris Directive #17).
        """
        # Build adjacency graph for synthetic links
        adj: Dict[str, List[str]] = {}
        edge_map: Dict[Tuple[str, str], EdgeEvidence] = {}

        synthetic_statuses = (EdgeStatus.SYNTHETIC_LINK, EdgeStatus.REINFORCED_SYNTHETIC_LINK, EdgeStatus.SPECULATIVE_LINK)
        for e in graph.edges:
            if e.status in synthetic_statuses:
                adj.setdefault(e.source_node_id, []).append(e.target_node_id)
                edge_map[(e.source_node_id, e.target_node_id)] = e

        # Find cycles using DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Cycle detected
                    idx = path.index(neighbor)
                    cycle = list(path[idx:])
                    if len(cycle) >= 2:
                        cycles.append(cycle)

            rec_stack.remove(node)
            path.pop()

        for n in list(adj.keys()):
            if n not in visited:
                dfs(n, [])

        # Check empirical grounding for each cycle (Aris Requirement #2)
        degraded_cycles: List[List[str]] = []
        for cycle in cycles:
            # A cycle is valid ONLY if at least one node has a core empirical link (epi >= 0.85) to an outside anchor
            has_external_grounding = False
            for node_id in cycle:
                for e in graph.edges:
                    if e.status == EdgeStatus.CORE_ACTIVE_LINK and (e.source_node_id == node_id or e.target_node_id == node_id):
                        other_id = e.target_node_id if e.source_node_id == node_id else e.source_node_id
                        if other_id not in cycle:
                            other_node = next((nd for nd in graph.nodes if nd.id == other_id), None)
                            if other_node and other_node.epistemic_confidence >= 0.85:
                                has_external_grounding = True
                                break
                if has_external_grounding:
                    break

            if not has_external_grounding:
                # Degrade all edges in the ungrounded circular loop
                degraded_cycles.append(cycle)
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)]
                    edge = edge_map.get((u, v))
                    if edge:
                        edge.weight = round(edge.weight * 0.25, 3)  # Damped to ghost status
                        edge.status = EdgeStatus.SPECULATIVE_LINK

        return degraded_cycles

    def apply_utility_filter(
        self,
        graph: ICGGraph,
        bridge: ProposedCrossDomainBridge,
        thesis: SynthesisThesis,
    ) -> bool:
        """
        Applies utility metric to bridge weight: promotes high-utility links, degrades inert analogies (Aris Directive #17).
        """
        edge = next((
            e for e in graph.edges
            if (e.source_node_id == bridge.source_node_id and e.target_node_id == bridge.target_node_id)
            or e.edge_id.endswith(bridge.bridge_id)
        ), None)

        if thesis.is_tautological or thesis.utility_gain < 0.20:
            # Degrade inert analogy
            if edge:
                edge.weight = round(edge.weight * 0.50, 3)
                edge.status = EdgeStatus.SPECULATIVE_LINK
            bridge.reinforcement_state = "SPECULATIVE"
            return False
        elif thesis.utility_gain >= 0.70 and not thesis.is_circular:
            # High-utility confirmed synthesis
            if edge:
                edge.status = EdgeStatus.REINFORCED_SYNTHETIC_LINK
            bridge.reinforcement_state = "REINFORCED"
            return True
        return True


__all__ = ["ResonanceOutputValidator"]
