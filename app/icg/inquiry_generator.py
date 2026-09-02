"""
Inquiry Generator (app/icg/inquiry_generator.py)
Aris Directive #7: Cognitive Void Mapping & Active Inquiry (CVM)

Converts a COGNITIVE_VOID (gap between two key anchor nodes) into a
structured, non-trivial inquiry: a concrete bridging hypothesis and a list
of specific facts that would close the gap.

Design principles (per Aris):
  - Questions MUST be specific, NOT "я не знаю" / "I don't know"
  - Each question encodes:
      * the two opposing theses (A and B)
      * the type of void (EMPIRICAL_GAP / LOGICAL_DISCONTINUITY / CONTRADICTORY_SILENCE)
      * a concrete bridging hypothesis derived from semantic proximity
  - Hypotheses are ordered by specificity (most specific first)
"""

from __future__ import annotations
import re
from typing import List, Tuple, Set, Optional

from app.icg.models import (
    VoidType,
    VoidStatus,
    InquiryResult,
    CognitiveVoidMetadata,
)

# ---------------------------------------------------------------------------
# Configuration constants (Aris Directive #7 — no magic numbers in code)
# ---------------------------------------------------------------------------
T_VOID: float = 0.30          # Coverage threshold below which a void is declared
W_TENTATIVE_MIN: float = 0.10  # Minimum TENTATIVE edge weight
W_TENTATIVE_MAX: float = 0.30  # Maximum TENTATIVE edge weight
W_TENTATIVE_DEFAULT: float = 0.15  # Default TENTATIVE edge weight

# Minimum significance filter: COGNITIVE_VOID only between ANCHOR / SUPER_ANCHOR nodes
# that have at least this many unique content stems (prevents trivial one-word anchors)
MIN_ANCHOR_STEMS: int = 3

# CONTRADICTORY_SILENCE is triggered when a REPULSION_BOUNDARY edge exists AND
# coverage is still below T_VOID even after factoring in all edges
REPULSION_CONTRADICTION_THRESHOLD: float = -0.50  # edge weight below this = repulsion


# ---------------------------------------------------------------------------
# Stem extraction (lightweight, bilingual RU/EN, no heavy dependencies)
# ---------------------------------------------------------------------------
_STOP_RU = {
    "и", "в", "на", "с", "по", "для", "что", "как", "из", "от", "до",
    "не", "это", "но", "а", "же", "при", "также", "то", "так", "или",
    "если", "то", "чем", "чего", "ли", "к", "у", "о", "об", "за"
}
_STOP_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "by", "as",
    "it", "this", "that", "not", "from", "into", "can", "may", "will"
}
_STOP = _STOP_RU | _STOP_EN


def _extract_stems(text: str) -> Set[str]:
    """
    Lightweight stemmer: lower, tokenise, remove stopwords, keep stem prefix.
    Works bilingual RU/EN without external dependencies.
    """
    tokens = re.findall(r"[а-яёa-z]{3,}", text.lower())
    return {t[:6] for t in tokens if t not in _STOP}


def _coverage(stems_a: Set[str], stems_b: Set[str]) -> float:
    """Stem overlap ratio: |A ∩ B| / max(|A|, |B|)."""
    if not stems_a or not stems_b:
        return 0.0
    return len(stems_a & stems_b) / max(len(stems_a), len(stems_b))


def _short(text: str, max_len: int = 60) -> str:
    """Return first max_len chars of text, stripped, ending with '...' if cut."""
    t = text.strip()
    return t[:max_len].rstrip() + "..." if len(t) > max_len else t


# ---------------------------------------------------------------------------
# Bridging hypothesis inference
# ---------------------------------------------------------------------------
def _infer_bridge_hypothesis(
    text_a: str,
    text_b: str,
    stems_a: Set[str],
    stems_b: Set[str],
    void_type: VoidType,
) -> Tuple[str, List[str]]:
    """
    Synthesise a specific bridging hypothesis from the semantic gap between
    two anchor texts.  Returns (inquiry_question, hypotheses_list).

    Strategy:
      1. Compute 'unique to A' and 'unique to B' stem sets (differentiating stems)
      2. Identify the domain tension (what A asserts uniquely vs what B asserts uniquely)
      3. Formulate a falsifiable bridging question
    """
    unique_a = stems_a - stems_b
    unique_b = stems_b - stems_a

    # Build short descriptors for each pole
    snippet_a = _short(text_a, 55)
    snippet_b = _short(text_b, 55)

    # Top distinguishing tokens (original, not stemmed) from each side
    all_tokens_a = [
        t for t in re.findall(r"[а-яёa-z]{4,}", text_a.lower())
        if t not in _STOP and t[:6] in unique_a
    ]
    all_tokens_b = [
        t for t in re.findall(r"[а-яёa-z]{4,}", text_b.lower())
        if t not in _STOP and t[:6] in unique_b
    ]

    # De-dup while preserving first occurrence
    seen: Set[str] = set()
    top_a: List[str] = []
    for tok in all_tokens_a:
        if tok not in seen:
            seen.add(tok)
            top_a.append(tok)
        if len(top_a) >= 3:
            break

    seen = set()
    top_b: List[str] = []
    for tok in all_tokens_b:
        if tok not in seen:
            seen.add(tok)
            top_b.append(tok)
        if len(top_b) >= 3:
            break

    key_a = " / ".join(top_a) if top_a else "(концепт A)"
    key_b = " / ".join(top_b) if top_b else "(концепт B)"

    # Void-type specific question template (Aris requirement: non-trivial)
    if void_type == VoidType.EMPIRICAL_GAP:
        q = (
            f"Когнитивная пустота (EMPIRICAL_GAP): граф не содержит фактических "
            f"данных, связывающих тезис [{key_a}] (источник: «{snippet_a}») "
            f"с тезисом [{key_b}] (источник: «{snippet_b}»). "
            f"Гипотеза: между этими концептами существует прямая эмпирическая связь, "
            f"требующая внешнего источника."
        )
        hyps = [
            f"Существует ли экспериментальное подтверждение связи между «{key_a}» и «{key_b}»?",
            f"Какой механизм или посредник связывает {key_a} с {key_b}?",
            f"Содержит ли академический корпус работы, совмещающие оба концепта?",
        ]
    elif void_type == VoidType.LOGICAL_DISCONTINUITY:
        q = (
            f"Когнитивная пустота (LOGICAL_DISCONTINUITY): рёбра между тезисом "
            f"[{key_a}] и тезисом [{key_b}] присутствуют, но их логическая "
            f"непрерывность нарушена (coverage < T_void={T_VOID}). "
            f"Гипотеза: между «{key_a}» и «{key_b}» отсутствует промежуточный "
            f"логический переход, требующий явной формулировки."
        )
        hyps = [
            f"Какой логический шаг связывает {key_a} с {key_b}?",
            f"Существует ли промежуточный принцип или закон, соединяющий оба тезиса?",
            f"Не является ли переход от {key_a} к {key_b} скрытым допущением автора?",
        ]
    else:  # CONTRADICTORY_SILENCE
        q = (
            f"Когнитивная пустота (CONTRADICTORY_SILENCE): тезисы [{key_a}] и "
            f"[{key_b}] находятся в зоне активного отталкивания (REPULSION_BOUNDARY). "
            f"Синтез невозможен без разрешения противоречия. "
            f"Гипотеза: конфликт между «{key_a}» и «{key_b}» фундаментален и "
            f"требует либо внешнего арбитра, либо Higher-Order Synthesis."
        )
        hyps = [
            f"Возможно ли согласование {key_a} и {key_b} через мета-принцип более высокого порядка?",
            f"Является ли противоречие между {key_a} и {key_b} абсолютным или контекстно-зависимым?",
            f"Существуют ли эмпирические данные, разрешающие конфликт {key_a} vs {key_b}?",
        ]

    return q, hyps


# ---------------------------------------------------------------------------
# Main public interface
# ---------------------------------------------------------------------------

class InquiryGenerator:
    """
    Aris Directive #7: Converts a detected cognitive void into a structured
    InquiryResult — a concrete hypothesis and list of required facts.
    """

    def generate(
        self,
        void_node_id: str,
        pole_a_id: str,
        pole_b_id: str,
        text_a: str,
        text_b: str,
        void_type: VoidType,
        gap_coverage_score: float,
        max_path_weight: float,
        tentative_edge_ids: Optional[List[str]] = None,
    ) -> InquiryResult:
        """
        Generate a structured InquiryResult for a COGNITIVE_VOID node.

        Args:
            void_node_id:       ID of the COGNITIVE_VOID node in the graph
            pole_a_id / b_id:   IDs of the two anchor poles
            text_a / b:         Raw text spans of the two anchor poles
            void_type:          Classified void type
            gap_coverage_score: Stem coverage between A and B (< T_void)
            max_path_weight:    Max weight of any existing path A→B
            tentative_edge_ids: IDs of the TENTATIVE edges already created
        """
        stems_a = _extract_stems(text_a)
        stems_b = _extract_stems(text_b)

        question, hypotheses = _infer_bridge_hypothesis(
            text_a=text_a,
            text_b=text_b,
            stems_a=stems_a,
            stems_b=stems_b,
            void_type=void_type,
        )

        return InquiryResult(
            void_node_id=void_node_id,
            pole_a_anchor_id=pole_a_id,
            pole_b_anchor_id=pole_b_id,
            inquiry_question=question,
            hypotheses=hypotheses,
            void_type=void_type,
            tentative_edge_ids=tentative_edge_ids or [],
        )


# Convenience singleton
_generator_instance: Optional[InquiryGenerator] = None


def get_inquiry_generator() -> InquiryGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = InquiryGenerator()
    return _generator_instance


# ---------------------------------------------------------------------------
# Module-level helpers re-exported for graph_builder convenience
# ---------------------------------------------------------------------------
__all__ = [
    "InquiryGenerator",
    "get_inquiry_generator",
    "_extract_stems",
    "_coverage",
    "T_VOID",
    "W_TENTATIVE_DEFAULT",
    "W_TENTATIVE_MIN",
    "W_TENTATIVE_MAX",
    "MIN_ANCHOR_STEMS",
    "REPULSION_CONTRADICTION_THRESHOLD",
]
