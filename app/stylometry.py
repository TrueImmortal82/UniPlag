import math
import re
from collections import Counter

from .textutil import sentences

STOP_WORDS_RU = {
    "и", "а", "но", "или", "что", "который", "это", "в", "на", "с", "по",
    "не", "за", "из", "для", "от", "до", "при", "о", "об", "у", "к",
    "как", "так", "его", "её", "их", "ее", "уже", "все", "всё", "та",
    "то", "ты", "мы", "вы", "он", "она", "оно", "они", "бы", "же",
    "ли", "ни", "да", "нет", "вот", "тут", "там", "где", "когда",
    "если", "потому", "поэтому", "однако", "тоже", "также", "ещё",
    "еще", "более", "очень", "между", "перед", "после", "через",
    "над", "под", "без", "про", "только", "всего", "сам", "сама",
    "само", "сами", "этот", "эта", "эти", "тот", "та", "те",
}

STOP_WORDS_EN = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his",
    "himself", "she", "her", "hers", "herself", "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o",
    "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn",
    "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan",
    "shouldn", "wasn", "weren", "won", "wouldn",
}

CONTENT_POS_RU = {
    "существительное", "глагол", "прилагательное", "наречие",
}

CONTENT_POS_EN = {
    "noun", "verb", "adjective", "adverb",
}


def _is_stop(word: str, lang: str) -> bool:
    w = word.lower().strip(".,;:!?—–-\"'«»()[]{}…")
    if lang == "ru":
        return w in STOP_WORDS_RU
    return w in STOP_WORDS_EN


def _detect_lang(text: str) -> str:
    sample = text[:2000]
    cyr = sum(1 for ch in sample if "\u0400" <= ch <= "\u04FF")
    return "ru" if cyr / max(len(sample), 1) > 0.25 else "en"


def extract_stylometric_features(text: str) -> dict:
    sents = sentences(text)
    if len(sents) < 3:
        return _empty_features()

    lang = _detect_lang(text)
    sent_texts = [s[2].strip() for s in sents]
    sent_lens = [len(st.split()) for st in sent_texts]
    words = text.split()
    clean_words = [w.strip(".,;:!?—–-\"'«»()[]{}…") for w in words if len(w) > 1]

    mean_sent_len = sum(sent_lens) / len(sent_lens)
    sorted_lens = sorted(sent_lens)
    median_sent_len = sorted_lens[len(sorted_lens) // 2]
    std_sent_len = math.sqrt(sum((x - mean_sent_len) ** 2 for x in sent_lens) / len(sent_lens))
    sent_len_cv = std_sent_len / max(mean_sent_len, 1)

    word_lens = [len(w) for w in clean_words if w]
    mean_word_len = sum(word_lens) / max(len(word_lens), 1)

    unique_words = set(w.lower() for w in clean_words)
    ttr = len(unique_words) / max(len(clean_words), 1)

    content_words = [w.lower() for w in clean_words if not _is_stop(w, lang)]
    content_ratio = len(content_words) / max(len(clean_words), 1)

    content_ttr = len(set(content_words)) / max(len(content_words), 1) if content_words else 0.0

    punct_chars = sum(1 for ch in text if ch in ".,;:!?—–-")
    punct_density = punct_chars / max(len(text), 1)

    comma_ratio = text.count(",") / max(len(words), 1)
    semicolon_ratio = text.count(";") / max(len(words), 1)
    exclamation_ratio = text.count("!") / max(len(words), 1)
    question_ratio = text.count("?") / max(len(words), 1)

    sent_starts = [st.split()[0].lower() if st.split() else "" for st in sent_texts]
    start_repeats = len(sent_starts) - len(set(sent_starts))
    start_repeat_ratio = start_repeats / max(len(sent_starts), 1)

    same_len_pairs = 0
    for i in range(len(sent_lens)):
        for j in range(i + 1, len(sent_lens)):
            if abs(sent_lens[i] - sent_lens[j]) <= 2:
                same_len_pairs += 1
    total_pairs = len(sent_lens) * (len(sent_lens) - 1) / 2
    structure_similarity = same_len_pairs / max(total_pairs, 1)

    bigrams = [f"{clean_words[i].lower()} {clean_words[i+1].lower()}"
               for i in range(len(clean_words) - 1)]
    bigram_counts = Counter(bigrams)
    repeated_bigrams = sum(1 for c in bigram_counts.values() if c > 1)
    bigram_repeat_ratio = repeated_bigrams / max(len(bigram_counts), 1)

    entropy = _shannon_entropy(text)

    return {
        "mean_sent_len": round(mean_sent_len, 2),
        "median_sent_len": round(median_sent_len, 2),
        "std_sent_len": round(std_sent_len, 2),
        "sent_len_cv": round(sent_len_cv, 4),
        "mean_word_len": round(mean_word_len, 2),
        "ttr": round(ttr, 4),
        "content_ratio": round(content_ratio, 4),
        "content_ttr": round(content_ttr, 4),
        "punct_density": round(punct_density, 4),
        "comma_ratio": round(comma_ratio, 4),
        "semicolon_ratio": round(semicolon_ratio, 4),
        "exclamation_ratio": round(exclamation_ratio, 4),
        "question_ratio": round(question_ratio, 4),
        "start_repeat_ratio": round(start_repeat_ratio, 4),
        "bigram_repeat_ratio": round(bigram_repeat_ratio, 4),
        "structure_similarity": round(structure_similarity, 4),
        "entropy": round(entropy, 4),
        "burstiness": round(sent_len_cv, 4),
        "n_sents": len(sents),
        "n_words": len(words),
    }


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freq = Counter(text.lower())
    total = len(text)
    ent = 0.0
    for count in freq.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


FEATURE_NAMES = [
    "mean_sent_len", "median_sent_len", "std_sent_len", "sent_len_cv",
    "mean_word_len", "ttr", "content_ratio", "content_ttr",
    "punct_density", "comma_ratio", "semicolon_ratio",
    "exclamation_ratio", "question_ratio",
    "start_repeat_ratio", "bigram_repeat_ratio", "structure_similarity",
    "entropy", "burstiness",
]


def _empty_features() -> dict:
    return {k: 0.0 for k in FEATURE_NAMES + ["n_sents", "n_words"]}


def semantic_density(text: str) -> float:
    words = text.lower().split()
    if len(words) < 10:
        return 0.5

    lang = _detect_lang(text)
    clean = [w.strip(".,;:!?—–-\"'«»()[]{}…") for w in words if len(w) > 1]

    content = [w for w in clean if not _is_stop(w, lang)]
    content_ratio = len(content) / max(len(clean), 1)

    unique_content = set(content)
    content_ttr = len(unique_content) / max(len(content), 1)

    named_entities = len(re.findall(r"\b[А-Я][а-я]+\b|\b[A-Z][a-z]+\b", text))
    ne_density = min(named_entities / max(len(words), 1) * 10, 1.0)

    numbers = len(re.findall(r"\b\d+\b", text))
    num_density = min(numbers / max(len(words), 1) * 20, 1.0)

    avg_word_len = sum(len(w) for w in content) / max(len(content), 1)
    word_complexity = min(avg_word_len / 8.0, 1.0)

    density = (
        0.35 * content_ratio +
        0.25 * content_ttr +
        0.20 * ne_density +
        0.10 * num_density +
        0.10 * word_complexity
    )
    return round(min(max(density, 0.0), 1.0), 3)
