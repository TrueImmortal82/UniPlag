"""
NLI Verifier v0.5 — Multi-Layered Semantic Verifier (app/icg/nli_verifier.py)
=============================================================================
Директива №19: Многослойный Верификатор
  Layer 1: Semantic Vector (cosine similarity + dynamic threshold)
  Layer 2: Value Conflict Detector (сила отрицания + семантическое отклонение)
  Layer 3: Context Bridge (расширение контекста для коротких текстов)
"""

from typing import List, Tuple, Dict, Optional, Set
import re
import math


class NLIVerificationResult:
    def __init__(
        self,
        entailment_score: float,
        contradiction_score: float,
        neutral_score: float,
        counterfactual_passed: bool = True,
        fallacy_reason: Optional[str] = None,
        is_multi_source_synthesis: bool = False,
        layer_used: str = "lexical",
        confidence: float = 0.5,
        contradiction_pending: bool = False,
    ):
        self.entailment_score = entailment_score
        self.contradiction_score = contradiction_score
        self.neutral_score = neutral_score
        self.counterfactual_passed = counterfactual_passed
        self.fallacy_reason = fallacy_reason
        self.is_multi_source_synthesis = is_multi_source_synthesis
        self.layer_used = layer_used
        self.confidence = confidence
        self.contradiction_pending = contradiction_pending

    def is_valid_entailment(self, threshold: float = 0.04) -> bool:
        return self.entailment_score >= threshold and self.counterfactual_passed

    def is_contradiction(self, threshold: float = 0.40) -> bool:
        return self.contradiction_score >= threshold


class HybridNLIVerifier:
    POS_POLARITY = {
        "увелич", "повыш", "улучш", "рост", "эффектив", "устойчив", "положительн", "стабильн",
        "быстр", "меньш", "высокодобротн", "когерентн", "ускорен", "ускор",
        "increas", "higher", "improv", "boost", "enhanc", "gain", "effectiv", "stabl",
        "positiv", "fast", "speed", "accelerat",
        "oshir", "ko'pay", "yaxshi", "samarali", "barqaror", "tez", "o'sish",
    }
    NEG_POLARITY = {
        "уменьш", "сниж", "ухудш", "деград", "паден", "неэффектив", "неустойчив",
        "отрицательн", "нестабильн", "нестабильност", "замедл", "замедлен",
        "decreas", "lower", "degrad", "worsen", "drop", "loss", "ineffectiv",
        "unstabl", "negativ", "instabl", "slow", "decelerat",
        "kamay", "pasay", "yomon", "tushish", "beqaror", "sekin",
    }
    METRIC_NOUNS = {
        "скорост", "точност", "стабильн", "стабильност", "производительност",
        "эффективност", "надежност", "сходимост", "пропускн", "поиск", "вычислен",
        "speed", "accurac", "perform", "throughput", "efficienc", "reliabl",
        "tezlik", "aniqlik", "barqarorlik", "unumdorlik",
    }
    RU_SUFFIXES = [
        'овать','ивать','ение','ения','ением','ости','ость','ами','ями','ого','его',
        'ому','ему','ыми','ими','ать','ять','ить','еть','ую','юю','ей','ой','ем','ом',
        'ах','ях','ов','ев','ей','ам','ям','а','е','и','о','у','ы','ь','я',
    ]
    EN_SUFFIXES = [
        'ation','ations','ing','ings','ally','ically','able','ible',
        'ness','ment','ments','ies','ed','es','ly','s',
    ]
    UZ_SUFFIXES = [
        'lik','lar','ning','dan','dagi','ida','ish','ishi','moqda',
        'gan','kan','adi','boshi','sida','kor','lari','larda','lardan',
    ]
    META_DISCOURSE_WORDS = {
        "и","в","на","с","по","для","что","как","это","при","из","к","о","об",
        "то","же","от","до","без","над","под","так","мы","вы","он","она","они",
        "и", "a", "an", "the", "in", "on", "at", "for", "to", "of", "with",
        "by", "that", "this", "it", "from", "as", "is", "are", "was", "were",
        "be", "been", "and", "or", "but", "if", "then", "therefore", "thus",
    }
    SYNONYM_PAIRS = [
        ("gpu","графическ"), ("gpu","процессор"), ("nvme","storage"), ("nvme","накопител"),
        ("io","latency"), ("database","storage"), ("network","distributed"),
        ("полупроводник","микрпроцессор"), ("бизнес","коммерческ"),
        ("онкология","опухол"), ("онкология","рак"),
        ("алгорitm","hisoblash"), ("нейрон","тarmoq"),
    ]

    NEGATION_WORDS = {
        "не", "нет", "not", "never", "никогда", "невозможн", "недопустим",
        "impossible", "falsif", "refut", "reject", "опроверг", "отверг",
        "ложн", "запрещ", "противореч",
    }

    # Aris Directive #10 fix (Cognitive Immunity): inherently negative verbs/predicates
    # negate BY THEMSELVES — "эксперименты опровергают..." — and must not wait for a
    # clausal next-token check. Without them explicit refutation was invisible.
    INHERENT_NEGATION_PREFIXES = (
        "опроверг", "отверг", "запрещ", "противореч", "исключ",
        "falsif", "refut", "reject", "deny", "denied", "contradict", "negat",
        "невозможн", "недопустим",
    )

    # Aris Directive #3 (Cognitive Immunity): antonym predicates asserting OPPOSITE
    # effects on the SAME subject are a hard contradiction ('повышение налогов
    # стимулирует рост' vs 'повышение налогов подавляет рост'), never an entailment.
    ANTONYM_PAIRS = (
        ("стимулир", "подавляет"), ("стимулир", "подавля"),
        ("увеличивает", "уменьшает"), ("увелич", "уменьш"),
        ("повышает", "снижает"), ("повыш", "сниж"),
        ("ускоряет", "замедляет"), ("ускор", "замедл"),
        ("улучшает", "ухудшает"), ("улучш", "ухудш"),
        ("укрепляет", "ослабляет"), ("укрепл", "ослаб"),
        ("служит", "вредит"), ("поощряет", "препятствует"), ("поощря", "препятств"),
        ("повышает", "понижает"), ("повыш", "пониж"),
        ("растёт", "падает"), ("рост", "паден"),
        ("increas", "decreas"), ("rais", "lower"), ("improv", "worsen"),
        ("accelerat", "decelerat"), ("boost", "reduc"), ("expand", "shrink"),
        ("promot", "hind"), ("stimulat", "suppress"), ("strengthen", "weaken"),
    )

    def __init__(self, use_dense_embeddings: bool = True):
        self.dense_model = None
        if use_dense_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.dense_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.dense_model = None

    def stem_token(self, w: str) -> str:
        w = w.lower()
        for sfx in self.RU_SUFFIXES:
            if w.endswith(sfx) and len(w) - len(sfx) >= 3:
                return w[:-len(sfx)]
        for sfx in self.EN_SUFFIXES:
            if w.endswith(sfx) and len(w) - len(sfx) >= 3:
                return w[:-len(sfx)]
        for sfx in self.UZ_SUFFIXES:
            if w.endswith(sfx) and len(w) - len(sfx) >= 3:
                return w[:-len(sfx)]
        return w

    def _extract_content_stems(self, text: str) -> Set[str]:
        words = re.findall(r"[A-Za-zА-ЯЁа-яё0-9_\-']+", text.lower())
        stems = set()
        for w in words:
            if w not in self.META_DISCOURSE_WORDS and len(w) >= 2:
                if '-' in w:
                    for p in w.split('-'):
                        if p not in self.META_DISCOURSE_WORDS and len(p) >= 2:
                            stems.add(self.stem_token(p))
                stems.add(self.stem_token(w))
        return stems

    def _stems_match(self, s1: str, s2: str) -> bool:
        if s1 == s2:
            return True
        if len(s1) >= 4 and len(s2) >= 4:
            if s1 in s2 or s2 in s1:
                return True
        for a, b in self.SYNONYM_PAIRS:
            if (a in s1 and b in s2) or (b in s1 and a in s2):
                return True
        return False

    _NUM_TOKEN = re.compile(r"[+-]?\d[\d\s\u00A0]{0,12}(?:[.,]\d+)?")
    _KM_S = re.compile(r"км/с|\bkm/s\b|\bkmps\b", re.IGNORECASE)

    def _extract_numeric_facts(self, text: str) -> List[Tuple[str, str]]:
        """Return (normalised_number, subject_context) pairs found in a span.

        Numbers are normalised by stripping separators and whitespace so that
        '300 000', '300000', '300.000' all collide onto the same canonical value.
        """
        out: List[Tuple[str, str]] = []
        low = text.lower()
        for m in self._NUM_TOKEN.finditer(text):
            raw = m.group(0)
            num = re.sub(r"[\s\u00A0]", "", raw)
            num = num.replace(",", ".") if num.count(".") == 0 else num
            try:
                float(num)
            except ValueError:
                continue
            # subject context: the ~24 chars before the number (excluding the number itself)
            ctx_start = max(0, m.start() - 24)
            ctx = low[ctx_start:m.start()]
            out.append((num, ctx))
        return out

    def _same_subject(self, ctx_a: str, ctx_b: str) -> bool:
        """Crude subject-overlap check for two numeric fact contexts."""
        if not ctx_a or not ctx_b:
            return False
        toks_a = {t for t in re.findall(r"[a-zа-яё0-9_]+", ctx_a)
                  if len(t) >= 3 and t not in self.META_DISCOURSE_WORDS}
        toks_b = {t for t in re.findall(r"[a-zа-яё0-9_]+", ctx_b)
                  if len(t) >= 3 and t not in self.META_DISCOURSE_WORDS}
        if not toks_a or not toks_b:
            return False
        share = sum(1 for tb in toks_b if any(self._stems_match(ta, tb) for ta in toks_a))
        return share / max(len(toks_b), 1) >= 0.5

    def _numeric_magnitude_conflict(self, premise: str, hypothesis: str) -> bool:
        """Two conflicting numeric values for the same subject are a contradiction
        (anti-smoothing): '300000 km/s' vs '500000 km/s', or '100' vs '-100'.

        Guarded to avoid false positives:
          - opposite signs on a non-zero magnitude => hard conflict;
          - zero vs non-zero => hard conflict;
          - same-sign disproportional magnitudes (>=1.5x) only count when either
            side asserts the value with an EXCLUSIVE equality predicate ('равен',
            'равно', 'составляет', 'is', 'equals'...). A comparative/conjunctive
            reference ('batch size 256' vs 'batch size 512') is NOT a contradiction —
            the two values are compatible points on the same parameter, not rival
            determinations of it, so it must not be smoothed away as entailment
            nor flagged as conflict.
        """
        p_facts = self._extract_numeric_facts(premise)
        h_facts = self._extract_numeric_facts(hypothesis)
        if not p_facts or not h_facts:
            return False

        p_low = premise.lower()
        h_low = hypothesis.lower()
        equality_rx = re.compile(r"(равен|равна|равно|равны|составля|является|является равн|"
                                 r"равняется|равняется|=|is equal|equals|amounts to|stands at|"
                                 r"\b=\b)", re.IGNORECASE)
        p_asserts_value = bool(equality_rx.search(p_low))
        h_asserts_value = bool(equality_rx.search(h_low))

        for pnum, pctx in p_facts:
            pv = float(pnum)
            for hnum, hctx in h_facts:
                hv = float(hnum)
                if not self._same_subject(pctx, hctx):
                    continue
                # opposite sign on non-zero magnitudes: hard conflict
                if (pv > 0 and hv < 0) or (pv < 0 and hv > 0):
                    return True
                # zero vs non-zero: hard conflict
                if (pv == 0) != (hv == 0):
                    return True
                if pv == 0 and hv == 0:
                    continue
                # same-sign proportional difference: only a conflict when a value is
                # asserted as THE determination of the quantity, not a comparative point
                ratio = pv / hv if hv != 0 else float("inf")
                big_gap = ratio >= 1.5 or ratio <= 0.666
                if big_gap and (p_asserts_value or h_asserts_value):
                    return True
        return False

    def _antonym_conflict(self, premise: str, hypothesis: str) -> bool:
        """Flag an antonym-predicate contradiction: 'X стимулирует рост' vs
        'X подавляет рост' — the same subject claimed to produce opposite effects.

        Uses class-level ANTONYM_PAIRS so no new magic data lives in the hot path.
        """
        p_low = premise.lower()
        h_low = hypothesis.lower()
        for a, b in self.ANTONYM_PAIRS:
            if (a in p_low and b in h_low) or (b in p_low and a in h_low):
                return True
        return False

    def _check_metric_polarity_conflict(self, p_stems: Set[str], h_stems: Set[str]) -> bool:
        common = set()
        for m in self.METRIC_NOUNS:
            if any(self._stems_match(m, p) for p in p_stems) and any(self._stems_match(m, h) for h in h_stems):
                common.add(m)
        if not common:
            return False
        p_pos = any(any(self._stems_match(s, p) for s in self.POS_POLARITY) for p in p_stems)
        p_neg = any(any(self._stems_match(s, p) for s in self.NEG_POLARITY) for p in p_stems)
        h_pos = any(any(self._stems_match(s, h) for s in self.POS_POLARITY) for h in h_stems)
        h_neg = any(any(self._stems_match(s, h) for s in self.NEG_POLARITY) for h in h_stems)
        return bool((p_pos and h_neg) or (p_neg and h_pos))

    RU_VERB_ENDINGS = (
        'аться','яться','еться','утся','ються','ется','ются','атсь','ятсь',
        'ать','ять','еть','ить','уть','ыть','ять','оть','ить',
        'ает','яет','ует','юет','ит','ат','ят','ут','ют','ем','им','ишь','ешь',
        'ал','ял','ил','ала','ила','ало','или','али',
        'ается','ится','ется','утся','ятся','атся',
    )

    def _is_clausal_negation(self, tokens: List[str], idx: int) -> bool:
        """True if a negation token at idx negates a VERB/PREDICATE (clausal),
        not a fused property descriptor or nominal compound."""
        w = tokens[idx].lower()
        if w in ("не", "нет"):
            # look ahead to next content token: clausal if it is a verb
            for j in range(idx + 1, min(idx + 3, len(tokens))):
                nxt = tokens[j].strip(".,;:!?—–-()")
                if not nxt:
                    continue
                return any(nxt.lower().endswith(e) for e in self.RU_VERB_ENDINGS) or \
                       nxt.lower() in ("будет", "есть", "является", "стал", "стало", "остается")
        # English
        if w in ("not", "never"):
            for j in range(idx + 1, min(idx + 3, len(tokens))):
                nxt = tokens[j].strip(".,;:!?—–-()")
                if not nxt:
                    continue
                return any(nxt.lower().endswith(e) for e in ('ing', 'ed', 'es', 's')) or \
                       nxt.lower() in ("is", "are", "was", "were", "be", "have", "has", "does", "do", "will")
        return False

    def _count_negations(self, text: str) -> int:
        low = text.lower()
        words = re.findall(r"[A-Za-zА-ЯЁа-яё0-9_\-']+", low)
        count = 0
        for i, w in enumerate(words):
            # Inherent negation predicates count unconditionally.
            if any(w.startswith(pr) for pr in self.INHERENT_NEGATION_PREFIXES):
                count += 1
                continue
            # Skip fused property descriptors like нечувствительность/невозможность/недостаток
            if w.startswith("не") and len(w) > 4 and not w.startswith("не-"):
                stem = w[2:]
                if any(stem.startswith(s) for s in ("чувствит", "возможн", "достат", "устойчив", "обходим")):
                    continue
            if w in self.NEGATION_WORDS:
                if self._is_clausal_negation(words, i):
                    count += 1
            else:
                # compound negation prefix on a verb (e.g. не-подтвержден, не влияет)
                if w.startswith("не-") and any(w[3:].endswith(e) for e in self.RU_VERB_ENDINGS):
                    count += 1
        return count

    def _detect_value_conflict(self, premise: str, hypothesis: str, p_stems: Set[str], h_stems: Set[str]) -> float:
        score = 0.0
        p_neg = self._count_negations(premise)
        h_neg = self._count_negations(hypothesis)
        # Aris Directive (Layer 2 cleanup): clausal-negation asymmetry is only a WEAK
        # modifier, never a sole contradiction trigger. Directional polarity inversion
        # (below) or explicit value-pairs are the real contradiction signals.
        if abs(p_neg - h_neg) >= 1:
            overlap = len(p_stems & h_stems) / max(len(h_stems), 1)
            if overlap > 0.15:
                score = min(0.30, 0.10 + overlap * 0.20)
        # Aris Directive #10 fix (Cognitive Immunity): explicit REFUTATION of the SAME
        # concept the premise asserts positively is a STRONG contradiction, not a weak
        # asymmetry modifier. One side negates, the other asserts, overlap confirms we
        # are talking about the same claim -> no "smoothing of the poles".
        if (p_neg == 0 and h_neg >= 1) or (h_neg == 0 and p_neg >= 1):
            overlap = len(p_stems & h_stems) / max(len(h_stems), 1)
            if overlap >= 0.15:
                score = max(score, min(0.95, 0.75 + overlap * 0.20))
        if self._check_metric_polarity_conflict(p_stems, h_stems):
            score = max(score, 0.85)
        # Aris Directive #3 (Cognitive Immunity): conflicting numeric magnitudes for
        # the same subject are a hard contradiction — never 'entails'. Without this,
        # '300000 km/s' vs '500000 km/s' (or 'Y=100' vs 'Y=-100') were smoothed into
        # entailment, which violates pole preservation.
        if self._numeric_magnitude_conflict(premise, hypothesis):
            score = max(score, 0.92)
        # Aris Directive #3 (Cognitive Immunity): antonym verbs asserting opposite
        # effects on the same subject are a hard contradiction, not entailment.
        if self._antonym_conflict(premise, hypothesis):
            score = max(score, 0.90)
        p_low = premise.lower()
        h_low = hypothesis.lower()
        value_pairs = [
            ("равен", "не равен"), ("является", "не является"),
            ("доказ", "не доказ"), ("подтвержд", "опроверг"),
            ("возможн", "невозможн"), ("истинн", "ложн"),
            ("влияет", "не влияет"), ("связан", "не связан"),
            ("cause", "does not cause"), ("is", "is not"),
            ("does", "does not"), ("can", "cannot"),
            ("enable", "prevent"), ("increase", "decrease"),
        ]
        for pos, neg in value_pairs:
            if (pos in p_low and neg in h_low) or (neg in p_low and pos in h_low):
                score = max(score, 0.90)
        return score

    def _dense_similarity(self, text1: str, text2: str) -> float:
        if self.dense_model is None:
            return 0.0
        try:
            from sentence_transformers.util import cos_sim
            e1 = self.dense_model.encode(text1, show_progress_bar=False)
            e2 = self.dense_model.encode(text2, show_progress_bar=False)
            return float(cos_sim(e1, e2))
        except Exception:
            return 0.0

    def _context_bridge(self, texts: List[str]) -> str:
        if not texts:
            return ""
        if all(len(t.split()) > 15 for t in texts):
            return ""
        combined = " ".join(texts)
        words = combined.split()
        if len(words) < 30:
            return ""
        return ""

    def verify_pair(self, premise: str, hypothesis: str) -> NLIVerificationResult:
        p_stems = self._extract_content_stems(premise)
        h_stems = self._extract_content_stems(hypothesis)

        if not p_stems or not h_stems:
            return NLIVerificationResult(0.0, 0.0, 1.0, counterfactual_passed=False,
                                         fallacy_reason="No content tokens", layer_used="empty")

        matched = set()
        for h in h_stems:
            for p in p_stems:
                if self._stems_match(p, h):
                    matched.add(h)
                    break
        lexical_ratio = len(matched) / max(len(h_stems), 1)

        dense_sim = self._dense_similarity(premise, hypothesis)

        contradiction_score = self._detect_value_conflict(premise, hypothesis, p_stems, h_stems)
        if contradiction_score > 0.40:
            return NLIVerificationResult(
                entailment_score=0.05,
                contradiction_score=round(contradiction_score, 3),
                neutral_score=round(1.0 - contradiction_score, 3),
                counterfactual_passed=False,
                fallacy_reason="Value conflict / negation contradiction detected",
                layer_used="layer2_value_conflict",
                confidence=0.85,
            )

        if lexical_ratio == 0.0 and dense_sim < 0.25:
            return NLIVerificationResult(
                entailment_score=0.02, contradiction_score=0.10, neutral_score=0.88,
                counterfactual_passed=False,
                fallacy_reason="Non-sequitur: zero conceptual grounding",
                layer_used="layer1_vector",
                confidence=0.90,
            )

        combined = max(
            lexical_ratio * 1.8,
            (lexical_ratio * 0.4 + dense_sim * 0.6) * 1.5,
            dense_sim * 1.2,
        )

        if combined < 0.06:
            return NLIVerificationResult(
                entailment_score=round(combined, 3), contradiction_score=0.10,
                neutral_score=round(1.0 - combined, 3),
                counterfactual_passed=False,
                fallacy_reason=f"Low overlap ({combined:.2f}) — insufficient conceptual grounding",
                layer_used="layer1_vector",
                confidence=0.80,
            )

        entailment = min(0.95, combined)
        return NLIVerificationResult(
            entailment_score=round(entailment, 3),
            contradiction_score=0.05,
            neutral_score=round(max(0.0, 1.0 - entailment), 3),
            counterfactual_passed=True,
            layer_used="layer1_vector",
            confidence=round(min(0.95, 0.5 + dense_sim * 0.5), 3),
        )

    def verify_multi_premise(self, premises: List[str], hypothesis: str) -> NLIVerificationResult:
        if len(premises) == 1:
            return self.verify_pair(premises[0], hypothesis)

        h_stems = self._extract_content_stems(hypothesis)
        all_p_stems = set()
        premise_stems_list = []
        for p in premises:
            ps = self._extract_content_stems(p)
            premise_stems_list.append(ps)
            all_p_stems |= ps

        matched = set()
        for h in h_stems:
            for p in all_p_stems:
                if self._stems_match(p, h):
                    matched.add(h)
                    break
        total_overlap = len(matched)

        if not h_stems or total_overlap == 0:
            contradiction_score = 0.0
            for p in premises:
                cs = self._detect_value_conflict(p, hypothesis, self._extract_content_stems(p), h_stems)
                contradiction_score = max(contradiction_score, cs)
            if contradiction_score > 0.40:
                return NLIVerificationResult(
                    entailment_score=0.05, contradiction_score=round(contradiction_score, 3),
                    neutral_score=round(1.0 - contradiction_score, 3),
                    counterfactual_passed=False,
                    fallacy_reason="Value conflict across all premises",
                    layer_used="layer2_value_conflict", confidence=0.85,
                )
            return NLIVerificationResult(
                entailment_score=0.0, contradiction_score=0.1, neutral_score=0.9,
                counterfactual_passed=False,
                fallacy_reason="Non-sequitur: zero conceptual grounding between premises and conclusion",
                layer_used="layer1_vector", confidence=0.90,
            )

        coverage = total_overlap / max(len(h_stems), 1)

        max_contradiction = 0.0
        for p in premises:
            cs = self._detect_value_conflict(p, hypothesis, self._extract_content_stems(p), h_stems)
            max_contradiction = max(max_contradiction, cs)
        contradiction_pending = bool(0.40 <= max_contradiction <= 0.70)
        # Aris Directive (Layer 2 cleanup): only a STRONG directional contradiction
        # (>0.70) may auto-reject. The disputed band [0.40,0.70] is a "doubt buffer"
        # and must be escalated to the LLM judge, never auto-resolved to CONTRADICTORY.
        if max_contradiction > 0.70:
            return NLIVerificationResult(
                entailment_score=0.05, contradiction_score=round(max_contradiction, 3),
                neutral_score=round(1.0 - max_contradiction, 3),
                counterfactual_passed=False,
                fallacy_reason="Value conflict with premise",
                layer_used="layer2_value_conflict", confidence=0.85,
            )

        dense_sims = []
        for p in premises:
            ds = self._dense_similarity(p, hypothesis)
            dense_sims.append(ds)
        avg_dense = sum(dense_sims) / max(len(dense_sims), 1)
        max_dense = max(dense_sims) if dense_sims else 0.0

        combined = max(
            coverage * 1.8,
            (coverage * 0.35 + avg_dense * 0.65) * 1.5,
            max_dense * 1.3,
        )

        if combined < 0.05:
            return NLIVerificationResult(
                entailment_score=round(combined, 3), contradiction_score=0.15,
                neutral_score=round(1.0 - combined, 3),
                counterfactual_passed=False,
                fallacy_reason=f"Low coverage ({combined:.2f}) — insufficient grounding",
                layer_used="layer1_vector", confidence=0.80,
            )

        contributions = sum(1 for ps in premise_stems_list
                           if any(any(self._stems_match(p, h) for p in ps) for h in h_stems))
        is_synthesis = (contributions >= 2 and total_overlap >= 2)
        entailment = min(0.95, combined)

        return NLIVerificationResult(
            entailment_score=round(entailment, 3),
            contradiction_score=round(max_contradiction, 3),
            neutral_score=round(max(0.0, 1.0 - entailment), 3),
            counterfactual_passed=True,
            is_multi_source_synthesis=is_synthesis,
            layer_used="layer1_vector",
            confidence=round(min(0.95, 0.5 + avg_dense * 0.5), 3),
            contradiction_pending=contradiction_pending,
        )


class NLIVerifier:
    def __init__(self, external_search=None):
        self.hybrid = HybridNLIVerifier(use_dense_embeddings=True)
        self._reasoning_cache: Dict[str, NLIVerificationResult] = {}
        self._chain_context: List[str] = []
        self._chain_depth: int = 0
        self.external_search = external_search

    def reset_chain(self):
        self._chain_context = []
        self._chain_depth = 0

    def push_chain(self, claim_text: str):
        self._chain_context.append(claim_text[:150])
        self._chain_depth += 1
        if len(self._chain_context) > 5:
            self._chain_context = self._chain_context[-5:]

    def _build_context_anchor(self) -> str:
        if not self._chain_context:
            return ""
        anchor = " ".join(self._chain_context)
        if len(anchor) > 400:
            anchor = anchor[-400:]
        return anchor

    def _llm_reasoning_with_anchor(self, premises: List[str], conclusion: str) -> Optional[NLIVerificationResult]:
        import hashlib

        cache_key = hashlib.md5((str(premises) + conclusion + str(self._chain_depth)).encode()).hexdigest()
        if cache_key in self._reasoning_cache:
            return self._reasoning_cache[cache_key]

        prev_res = self._reasoning_cache.get(cache_key)
        system = (
            "You are a logical reasoning engine for an Intellectual Contribution Graph. "
            "Given the accumulated chain context and the current premises, decide whether the "
            "new conclusion follows. Respond with EXACTLY one word: ENTAILMENT, CONTRADICTION, or NEUTRAL."
        )
        anchor = self._build_context_anchor()
        user = (f"Chain context: {anchor}\n\nPremises: {' '.join(premises)[:400]}\n\n"
                f"New conclusion: {conclusion[:250]}\n\nOne-word verdict:")
        answer = self._chat_ollama(self.CHAIN_JUDGE_MODEL, system, user, num_predict=12, timeout=60)
        if not answer:
            answer = self._chat_ollama(self.CHAIN_JUDGE_FALLBACK, system, user, num_predict=12, timeout=60)
        answer = answer.upper()

        if "ENTAILMENT" in answer:
            result = NLIVerificationResult(
                entailment_score=0.88, contradiction_score=0.05, neutral_score=0.07,
                counterfactual_passed=True, layer_used="layer3_context_anchor", confidence=0.92,
            )
        elif "CONTRADICTION" in answer:
            result = NLIVerificationResult(
                entailment_score=0.05, contradiction_score=0.92, neutral_score=0.03,
                counterfactual_passed=False, layer_used="layer3_context_anchor", confidence=0.92,
            )
        else:
            result = prev_res

        if result:
            self._reasoning_cache[cache_key] = result
        return result

    CHAIN_JUDGE_MODEL = "gemma4:31b-cloud"
    CHAIN_JUDGE_FALLBACK = "gemma4:latest"
    GRAY_ZONE_LO = 0.50
    GRAY_ZONE_HI = 0.70
    GOLDEN_ARCHIVE_PATH = None  # set via enable_golden_archive()

    # Aris Directive (Fact-Judge Module а): "Detector of Absolutism".
    # Strong factual claims / marketing absolutes that assert a guarantee, uniqueness,
    # totality or a falsifiable superlative without supporting evidence.
    ABSOLUTISM_PATTERNS = [
        r"\bгарантированн\w*", r"\bгарантиру\w*", r"\bабсолютн\w*",
        r"\b100%", r"\b100\s*-\s*процент\w*", r"\bединственн\w*.?стандарт\w*",
        r"\bмиров\w*.\s*стандарт\w*", r"\bнеизбежн\w*", r"\bбезусловн\w*",
        r"\bполностью\s+исключа\w*", r"\bоднозначн\w*", r"\bбезоговорочн\w*",
        r"\bисключительн\w*", r"\bсовершенн\w*", r"\bидеальн\w*",
        r"\bневозможно\s+не\b", r"\bединственн\w*.?способ\w*",
        r"\bуникальн\w*", r"\bреволюционн\w*",
        # Totality / totalizing outcome claims: "полностью/всех/любых/все + outcome".
        r"(полностью|полн\.?)\s+(замени\w*|устран\w*|предотвращ\w*|решит\w*|взлом\w*|автоматиз\w*|защити\w*|удал\w*|излечи\w*|очища\w*|контролиру\w*)",
        r"(полностью|полн\.?)\s+\w+\s+(весь|всех|всё|все|любых|любые|любые|любо|любом)\w*",
        r"(замени\w*|устран\w*|решит\w*|взломает\w*|построит\w*|заменит)\s+(всех|все|всё|весь|любых|любые)\w*",
        r"неограниченн\w*", r"кардинальн\w*", r"безграничн\w*", r"беспрецедентн\w*",
        r"\bмгновенно\b", r"\bмгновенн\w*",
        # English totality + certainty-of-outcome.
        r"\buniqu\w*\b", r"\brevolutionar\w*\b", r"\bunlimited\b", r"\bboundless\b", r"\bunprecedented\b",
        r"\b(completely|fully|entirely|totally|absolutely|definitely|certainly|undeniably|inevitably|immediately)\s+\w+",
        r"\bwill\s+(completely|fully|entirely|totally|definitely|certainly|inevitably|instantly|immediately)\s+\w+",
        r"\b(any|all|every)\s+\w+\s+(will|must|can)\b",
        # "Obviously follows / clearly implies" over-confident causal leaps.
        r"\bочевидно\s+(вытекает|следует|очевидн\w*)\b", r"\bбесспорно\b", r"\bнесомненно\b",
        r"\b(obviously|clearly|undeniably|unquestionably)\s+foll\w+\b",
        r"\bdefinitiv\w*\b", r"\bproven\s+to\s+(work|heal|cure|solve)\b",
    ]

    # Terms that neutralize a strong factual reading (hedges/caveats) so we do NOT flag them.
    ABSOLUTISM_HEDGE_PATTERNS = [
        r"\b(предположительно|вероятно|возможно|возможн\w*|may|might|could|potentially|possibly|perhaps)\b",
        r"\b(предв?арительн\w*|limited|prelimin)\w*\b",
        r"\bв\s+некоторых\s+случаях\b", r"\bnot\s+always\b", r"\bу\s+некоторых\b",
        r"\btends?\s+to\b", r"\bcorrelat\w*\b",
    ]

    # ECC thresholds for the Fact-Judge (Module б): below these the asserted factual claim
    # has no authoritative confirmation -> hard UNSUPPORTED.
    FACT_ECC_FOUND_THRESHOLD = 0.30     # external_similarity below -> unconfirmed
    FACT_ECC_ECC_MIN = 0.75             # corpus coverage must be meaningful to trust a negative

    def enable_golden_archive(self, path: str):
        """Aris Directive: persist every chain-continuity verdict for distillation."""
        self.GOLDEN_ARCHIVE_PATH = path

    def _log_golden(self, chain_tail: List[str], conclusion: str, verdict: str,
                    justification: str, features: dict):
        if not self.GOLDEN_ARCHIVE_PATH:
            return
        import os, json, datetime
        os.makedirs(os.path.dirname(self.GOLDEN_ARCHIVE_PATH), exist_ok=True)
        rec = {
            "ts": datetime.datetime.now().isoformat(),
            "chain": chain_tail[-6:],
            "conclusion": conclusion,
            "verdict": verdict,
            "justification": justification,
            "features": features,
        }
        try:
            with open(self.GOLDEN_ARCHIVE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _chat_ollama(self, model: str, system: str, user: str,
                     num_predict: int = 220, timeout: int = 120) -> str:
        import urllib.request, urllib.error, json
        payload = {
            "model": model, "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"num_predict": num_predict, "temperature": 0.1}
        }
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            return (resp.get("message", {}).get("content", "") or resp.get("response", "")).strip()
        except Exception:
            return ""

    def chain_continuity_judge(self, conclusion: str,
                               chain_tail: Optional[List[str]] = None) -> Tuple[str, str]:
        """Aris Directive: Chain-continuity judge (31b, full tail). Returns (verdict, justification).
        verdict in {CONTINUE, BREAK, CONTRADICT, EMPTY}"""
        tail = (chain_tail or self._chain_context or [])
        if not tail:
            return "EMPTY", "no chain context"
        system = (
            "You are a CHAIN-CONTINUITY judge for a reasoning chain in an academic graph. "
            "A chain is a sequence of already-established reasoning steps. Decide whether the NEW STEP "
            "naturally continues the chain (follows from the accumulated context) or is a BREAK "
            "(jumps to an unrelated topic or domain with no basis in the chain). "
            "Respond with EXACTLY:\n"
            "VERDICT: CONTINUE | BREAK | CONTRADICT\n"
            "JUSTIFICATION: <2-3 short sentences>"
        )
        chain_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(tail))
        user = (f"CHAIN SO FAR:\n{chain_text}\n\nNEW STEP:\n{conclusion}\n\n"
                f"Does the new step CONTINUE the chain or BREAK it?")
        out = self._chat_ollama(self.CHAIN_JUDGE_MODEL, system, user)
        if not (out and ("VERDICT" in out.upper())):
            out = self._chat_ollama(self.CHAIN_JUDGE_FALLBACK, system, user)
        verdict = "EMPTY"
        for tok in ("CONTINUE", "BREAK", "CONTRADICT"):
            if f"VERDICT: {tok}" in out.upper():
                verdict = tok
                break
        justification = out.strip()
        return verdict, justification

    def contradiction_judge(self, premises: List[str], conclusion: str,
                            fast_contradiction: float) -> Tuple[str, str]:
        """Aris Directive (Layer 2 gray zone): distinguish a REAL contradiction from a
        COMPLEX SYNTHESIS / refinement when the deterministic Layer 2 is unsure (0.40-0.70).
        Returns (verdict, justification); verdict in {CONTRADICT, SYNTHESIS, NEUTRAL, EMPTY}."""
        system = (
            "You are a CONTRADICTION judge for an academic reasoning chain. "
            "Given a set of premises and a new conclusion, decide whether the new step is a REAL direct "
            "contradiction of the premises, or a legitimate SYNTHESIS/refinement that combines or builds "
            "on complementary premises (even if it mentions negated properties of individual components). "
            "Respond with EXACTLY:\n"
            "VERDICT: CONTRADICT | SYNTHESIS | NEUTRAL\n"
            "JUSTIFICATION: <2-3 short sentences>"
        )
        p_text = " | ".join(premises)[:900]
        user = (f"PREMISES:\n{p_text}\n\nNEW STEP:\n{conclusion}\n\n"
                f"The deterministic layer scored this as a possible contradiction ({fast_contradiction:.2f}).\n"
                f"Is it a REAL contradiction or a SYNTHESIS?")
        out = self._chat_ollama(self.CHAIN_JUDGE_MODEL, system, user)
        if not (out and ("VERDICT" in out.upper())):
            out = self._chat_ollama(self.CHAIN_JUDGE_FALLBACK, system, user)
        verdict = "EMPTY"
        for tok in ("CONTRADICT", "SYNTHESIS", "NEUTRAL"):
            if f"VERDICT: {tok}" in out.upper():
                verdict = tok
                break
        return verdict, out.strip()

    def _apply_judge_result(self, fast_result: NLIVerificationResult, verdict: str,
                            justification: str) -> NLIVerificationResult:
        import hashlib
        cache_key = hashlib.md5((justification[:80]).encode()).hexdigest()
        if verdict == "BREAK":
            res = NLIVerificationResult(
                entailment_score=0.03, contradiction_score=0.05, neutral_score=0.92,
                counterfactual_passed=False,
                fallacy_reason=f"Chain-continuity BREAK: {justification[:200]}",
                layer_used="layer3_chain_continuity", confidence=0.90,
            )
        elif verdict == "CONTRADICT":
            res = NLIVerificationResult(
                entailment_score=0.05, contradiction_score=0.90, neutral_score=0.05,
                counterfactual_passed=False,
                fallacy_reason=f"Chain-continuity CONTRADICT: {justification[:200]}",
                layer_used="layer3_chain_continuity", confidence=0.90,
            )
        else:  # CONTINUE or EMPTY -> keep the fast result (already entailment candidate)
            res = fast_result
        self._reasoning_cache[cache_key] = res
        return res

    # =========================================================================
    # Aris Directive (Fact-Judge): Detector of Absolutism + External Confirmability
    # =========================================================================
    def _detect_absolutism(self, text: str) -> Tuple[bool, str]:
        """Module (а). Detect a 'strong factual claim' — marketing absolutes that
        assert guarantee/uniqueness/totality but need external proof.
        Returns (is_strong_claim, matched_trigger)."""
        if not text:
            return False, ""
        low = text.lower()
        # Hedges neutralize the strong reading (legit cautious science must not be flagged).
        for h in self.ABSOLUTISM_HEDGE_PATTERNS:
            if re.search(h, low):
                return False, ""
        for pat in self.ABSOLUTISM_PATTERNS:
            m = re.search(pat, low)
            if m:
                return True, m.group(0)
        return False, ""

    def _external_confirmability(self, conclusion: str) -> Tuple[bool, float, str]:
        """Module (б). Consult ECC (External Corpus Check). Returns
        (confirmed, score, reference). 'Confirmed' = the asserted claim's substance was
        found in the authoritative corpus; a low score + meaningful ECC => unconfirmed."""
        if self.external_search is None:
            return False, 0.0, "no-external-engine"
        try:
            att = self.external_search.verify_global_novelty(conclusion)
        except Exception:
            return False, 0.0, "err"
        sim = att.external_similarity
        ecc = att.external_corpus_coverage
        # Trust a negative only when corpus coverage is meaningful.
        if att.found_in_external_corpus and sim >= self.FACT_ECC_FOUND_THRESHOLD:
            return True, sim, att.matched_external_reference or ""
        if ecc >= self.FACT_ECC_ECC_MIN:
            return False, sim, f"ecc={ecc:.2f}"
        return False, sim, f"low-ecc={ecc:.2f}"

    def fact_judge(self, conclusion: str, fast_result: NLIVerificationResult) -> Optional[NLIVerificationResult]:
        """Aris Directive: Fact-Judge. Runs in the Slow path. If the step is a strong
        factual claim (absolutism) but the external corpus does NOT confirm it, return a
        hard UNSUPPORTED — factual falsehood outranks logical smoothness (even if
        Chain-Judge said CONTINUE)."""
        strong, trigger = self._detect_absolutism(conclusion)
        if not strong:
            return None
        confirmed, sim, ref = self._external_confirmability(conclusion)
        if confirmed:
            return None
        why = (f"Strong factual claim ('{trigger}') lacks external confirmation "
               f"(ext_sim={sim:.2f}, {ref})")
        return NLIVerificationResult(
            entailment_score=0.03, contradiction_score=0.05, neutral_score=0.92,
            counterfactual_passed=False,
            fallacy_reason=f"Fact-Judge UNSUPPORTED: {why}",
            layer_used="layer3_fact_judge", confidence=0.88,
        )

    def verify_step(self, premises: List[str], conclusion: str, use_llm: bool = False,
                    enable_chain_judge: Optional[bool] = None) -> NLIVerificationResult:
        if not premises:
            return NLIVerificationResult(
                entailment_score=0.0, contradiction_score=0.0, neutral_score=1.0,
                counterfactual_passed=False,
                fallacy_reason="No premises provided (Unsupported Claim)",
                layer_used="empty", confidence=1.0,
            )

        fast_result = self.hybrid.verify_multi_premise(premises, conclusion)

        # ---- Fast/Slow Split (Aris Directive): gray-zone chain-continuity judge ----
        do_chain_judge = (enable_chain_judge if enable_chain_judge is not None else use_llm)
        if do_chain_judge and fast_result.counterfactual_passed:
            dense_sim = self.hybrid._dense_similarity(
                " ".join(premises)[:500], conclusion[:300]
            )
            combined = fast_result.entailment_score
            in_gray_zone = (self.GRAY_ZONE_LO <= dense_sim <= self.GRAY_ZONE_HI) or \
                           (combined and 0.10 <= combined <= 0.50)
            if in_gray_zone:
                verdict, just = self.chain_continuity_judge(conclusion, list(premises))
                self._log_golden(list(premises), conclusion, verdict, just,
                                 {"dense": round(dense_sim, 3), "combined": round(combined, 3)})
                if verdict != "EMPTY":
                    return self._apply_judge_result(fast_result, verdict, just)

        # ---- Aris Directive (Layer 2 gray zone): escalation for disputed contradiction ----
        if do_chain_judge and fast_result.contradiction_pending:
            c_verdict, c_just = self.contradiction_judge(premises, conclusion,
                                                         fast_result.contradiction_score)
            self._log_golden(
                list(premises), conclusion, c_verdict, c_just,
                {"type": "layer2_contradiction",
                 "contradiction_score": round(fast_result.contradiction_score, 3)})
            if c_verdict == "CONTRADICT":
                return NLIVerificationResult(
                    entailment_score=0.05, contradiction_score=0.90, neutral_score=0.05,
                    counterfactual_passed=False,
                    fallacy_reason=f"Layer2 judge CONTRADICT: {c_just[:200]}",
                    layer_used="layer3_contradiction_judge", confidence=0.90,
                    contradiction_pending=False,
                )
            if c_verdict == "SYNTHESIS":
                return NLIVerificationResult(
                    entailment_score=max(fast_result.entailment_score, 0.80),
                    contradiction_score=0.05, neutral_score=0.05,
                    counterfactual_passed=True,
                    is_multi_source_synthesis=True,
                    fallacy_reason=f"Layer2 judge: SYNTHESIS (not contradiction): {c_just[:200]}",
                    layer_used="layer3_contradiction_judge", confidence=0.90,
                    contradiction_pending=False,
                )

        # ---- Aris Directive (Fact-Judge): Detector of Absolutism + External Confirmability ----
        # Runs in the Slow path AFTER Chain-Judge. Even if Chain-Judge said CONTINUE, a strong
        # factual claim that the external corpus does NOT confirm => hard UNSUPPORTED.
        if do_chain_judge:
            fact_res = self.fact_judge(conclusion, fast_result)
            if fact_res is not None:
                _, trigger = self._detect_absolutism(conclusion)
                simulated_conf, sim, ref = self._external_confirmability(conclusion)
                self._log_golden(
                    list(premises), conclusion, "UNSUPPORTED",
                    fact_res.fallacy_reason or "",
                    {"type": "fact_judge", "trigger": trigger,
                     "ext_sim": round(sim, 3), "confirmed": simulated_conf, "ref": ref})
                return fact_res

        if use_llm:
            trigger = False
            if fast_result.layer_used == "layer1_vector":
                if fast_result.entailment_score <= 0.20:
                    dense_sim = self.hybrid._dense_similarity(
                        " ".join(premises)[:500], conclusion[:300]
                    )
                    if dense_sim > 0.15:
                        trigger = True
                elif 0.20 < fast_result.entailment_score <= 0.50 and self._chain_depth >= 2:
                    trigger = True
            elif fast_result.layer_used == "layer2_value_conflict" and self._chain_depth >= 2:
                if 0.30 <= fast_result.contradiction_score <= 0.60:
                    trigger = True

            if trigger:
                llm_result = self._llm_reasoning_with_anchor(premises, conclusion)
                if llm_result is not None:
                    return llm_result

        return fast_result
