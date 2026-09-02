"""
Discourse Analysis & Argumentative Structure Extractor (app/icg/discourse.py)
Identifies EDUs, attribution citations, reasoning connectives, and propositional modality
across Russian (RU), English (EN), and Uzbek (UZ).
"""

from typing import List, Dict, Optional, Tuple, Set
import re
from app.icg.models import ClaimNode, TextSpan, Proposition, NodeType, ContributionClass


CITATION_PATTERN = re.compile(
    r'\[(\d+(?:\s*[-–,]\s*\d+)*)\]|\(([A-Za-zА-ЯЁа-яё\-]+(?:\s+et\s+al\.?|\s+va\s+b\.)?,\s*\d{4})\)'
)

INFERENCE_CONNECTIVES = {
    # Russian reasoning connectives
    "следовательно", "таким образом", "отсюда следует", "отсюда вытекает",
    "в связи с этим", "из этого следует", "приходим к выводу", "что приводит к",
    "в результате чего", "что доказывает", "это свидетельствует о",
    "значит", "то есть", "другими словами", "вывод:", "итог:",
    "следует что", "означает", "подразумевает",
    # English reasoning connectives
    "therefore", "thus", "hence", "consequently", "as a result",
    "it follows that", "which implies that", "which proves that", "yielding",
    "this means", "in other words", "which leads to",
    # Uzbek reasoning connectives
    "shunday qilib", "natijada", "demak", "xulosa qilib aytganda",
    "buning natijasida", "shundan kelib chiqadiki", "xulosa qilish mumkinki"
}

SYNTHESIS_CONNECTIVES = {
    # Russian synthesis connectives
    "объединяя данные подходы", "комбинируя", "интегрируя", "синтезируя данные",
    "совмещение", "совместное применение", "в совокупности", "на стыке",
    # English synthesis connectives
    "combining these approaches", "synthesizing", "integrating", "by joining",
    # Uzbek synthesis connectives
    "ushbu yondashuvlarni birlashtirib", "kombinatsiya qilib", "sintez qilib",
    "integratsiyalash orqali", "birgalikda qo'llash"
}

ATTRIBUTION_CONNECTIVES = {
    # Russian attribution
    "в исследовании", "в статье", "в работе", "в отчете", "согласно", "по данным",
    "показано", "установлено", "доказано", "отмечено",
    # English attribution
    "in study", "in research", "according to", "as demonstrated by", "shown by", "proposed by", "reported that",
    # Uzbek attribution
    "tadqiqotida", "maqolasida", "ishida", "hisobotida", "mualliflar tomonidan",
    "ko'rsatilgan", "isbotlangan", "aniqlangan", "ta'kidlangan"
}

HYPOTHESIS_MARKERS = {
    # Russian hypothesis markers
    "мы предполагаем", "предполагается, что", "выдвигаем гипотезу", "можно предположить",
    "мы формулируем гипотезу", "перспективным представляется", "возможно, что",
    # English hypothesis markers
    "we hypothesize", "we propose", "it is hypothesized", "we conjecture", "it is possible that",
    # Uzbek hypothesis markers
    "biz faraz qilamiz", "taxmin qilinadiki", "farazni ilgari suramiz", "faraz qilmoqdamiz", "mumkinki"
}

ACADEMIC_ABBREVS = [
    "et al.", "va b.", "e.g.", "i.e.", "рис.", "табл.", "см.", "т.д.", "т.п.", "т.е.",
    "dr.", "prof.", "masalan", "1-rasm", "2-jadval", "kabi"
]


def detect_language(text: str) -> str:
    text_lower = text.lower()
    uzbek_indicators = ["ko'rsatilgan", "shunday qilib", "tadqiqotida", "natijada", "birlashtirib", "faraz", "bo'yicha"]
    if any(ind in text_lower for ind in uzbek_indicators) or bool(re.search(r"\b(va|bilan|uchun|ham|esa)\b", text_lower)):
        return "uz"
    
    english_indicators = ["the", "in", "and", "is", "therefore", "study", "consequently", "demonstrated", "reported"]
    if any(ind in text_lower for ind in english_indicators):
        return "en"
        
    return "ru"


def split_into_edus(text: str) -> List[Tuple[int, int, str]]:
    """
    Splits text into elementary discourse units (EDUs / sentences) safely handling academic abbreviations.
    """
    protected = text
    for abb in ACADEMIC_ABBREVS:
        placeholder = abb.replace(".", "§§§")
        protected = re.sub(re.escape(abb), placeholder, protected, flags=re.IGNORECASE)

    raw_sentences = re.split(r'(?<=[.!?])\s+', protected.strip())
    edus = []
    current_pos = 0

    for sent in raw_sentences:
        sent_str = sent.replace("§§§", ".").strip()
        if not sent_str:
            continue
        start_idx = text.find(sent_str, current_pos)
        if start_idx == -1:
            start_idx = current_pos
        end_idx = start_idx + len(sent_str)
        current_pos = end_idx
        edus.append((start_idx, end_idx, sent_str))

    return edus


split_sentences_with_spans = split_into_edus


def extract_claim_nodes_from_text(document_id: str, text: str) -> List[ClaimNode]:
    edus = split_into_edus(text)
    nodes: List[ClaimNode] = []

    for idx, (start_char, end_char, sent_text) in enumerate(edus):
        sent_lower = sent_text.lower()
        lang = detect_language(sent_text)

        citations = []
        for m in CITATION_PATTERN.finditer(sent_text):
            if m.group(1):
                citations.extend([c.strip() for c in re.split(r'[-–,]', m.group(1)) if c.strip()])
            elif m.group(2):
                citations.append(m.group(2).strip())

        found_inference = [c for c in INFERENCE_CONNECTIVES if c in sent_lower]
        found_synthesis = [c for c in SYNTHESIS_CONNECTIVES if c in sent_lower]
        found_attribution = [c for c in ATTRIBUTION_CONNECTIVES if c in sent_lower]
        found_hypothesis = [c for c in HYPOTHESIS_MARKERS if c in sent_lower]

        if found_hypothesis:
            modality = "hypothesis"
        elif found_synthesis:
            modality = "synthesis_claim"
        elif found_inference:
            modality = "inference"
        elif citations or found_attribution:
            modality = "fact_with_citation"
        else:
            modality = "assertion"

        all_connectives = found_inference + found_synthesis + found_hypothesis

        prop = Proposition(
            subject="",
            predicate="",
            object_phrase="",
            modality=modality,
            conditions=[],
            connectives=all_connectives,
            language=lang
        )

        span = TextSpan(
            start_char=start_char,
            end_char=end_char,
            page=1,
            sentence_idx=idx,
            raw_text=sent_text
        )

        node = ClaimNode(
            id=f"claim_{idx:04d}",
            type=NodeType.CLAIM,
            contribution_class=ContributionClass.UNKNOWN,
            span=span,
            proposition=prop,
            sources_cited=citations
        )
        nodes.append(node)

    return nodes
