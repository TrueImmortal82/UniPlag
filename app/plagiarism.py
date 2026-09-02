import hashlib
from collections import defaultdict

from . import config
from .fingerprint import fingerprint, jaccard
from .textutil import tokenize


def _window_hash(words: list[str], i: int, k: int) -> int:
    s = " ".join(words[i:i + k])
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")


def align_fragments(q_text: str, c_text: str) -> tuple[int, list[tuple[int, int]]]:
    q_tokens = tokenize(q_text)
    c_tokens = tokenize(c_text)
    k = config.SHINGLE_K
    if len(q_tokens) < k or len(c_tokens) < k:
        return 0, []

    q_words = [t[0].lower().replace("ё", "е") for t in q_tokens]
    c_words = [t[0].lower().replace("ё", "е") for t in c_tokens]

    index: dict[int, list[int]] = defaultdict(list)
    for j in range(len(c_words) - k + 1):
        index[_window_hash(c_words, j, k)].append(j)

    diag: dict[int, set[int]] = defaultdict(set)
    for i in range(len(q_words) - k + 1):
        for j in index.get(_window_hash(q_words, i, k), ()):
            diag[i - j].add(i)

    fragments: list[tuple[int, int]] = []
    matched_words: set[int] = set()
    for starts in diag.values():
        run_start = prev = None
        runs: list[tuple[int, int]] = []
        for i in sorted(starts):
            if prev is not None and i - prev > 2:
                if prev - run_start >= config.MIN_FRAG_WORDS - 1:
                    runs.append((run_start, prev))
                run_start = i
            elif run_start is None:
                run_start = i
            prev = i
        if run_start is not None and prev - run_start >= config.MIN_FRAG_WORDS - 1:
            runs.append((run_start, prev))
        for a, b in runs:
            fragments.append((a, b))
            matched_words.update(range(a, b + k))

    total = len(q_tokens)
    percent = round(100.0 * len(matched_words) / total, 2) if total else 0.0
    spans = [(q_tokens[a][1], q_tokens[b + k - 1][2]) for a, b in fragments]
    return percent, merge_spans(spans)


def merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []
    spans.sort()
    out = [list(spans[0])]
    for s, e in spans[1:]:
        if s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


class CorpusIndex:
    def __init__(self) -> None:
        self._keys: dict[str, set[int]] = defaultdict(set)
        self._sigs: dict[int, bytes] = {}
        self.loaded = False

    def load(self, db) -> None:
        from .db import Document
        self._keys.clear()
        self._sigs.clear()
        for doc_id, text in db.query(Document.id, Document.text).all():
            self.add(doc_id, fingerprint(text))

    def add(self, doc_id: int, fp: dict) -> None:
        self._sigs[doc_id] = fp["sig"]
        for key in fp["keys"]:
            self._keys[key].add(doc_id)

    def remove(self, doc_id: int) -> None:
        self._sigs.pop(doc_id, None)

    def candidates(self, fp: dict, exclude: int) -> list[tuple[int, float]]:
        out: list[tuple[int, float]] = []
        if len(self._sigs) <= config.EXACT_SCAN_LIMIT:
            for doc_id, sig in self._sigs.items():
                if doc_id == exclude:
                    continue
                sim = jaccard(fp["sig"], sig)
                if sim >= config.CANDIDATE_THRESHOLD:
                    out.append((doc_id, sim))
        else:
            votes: dict[int, int] = defaultdict(int)
            for key in fp["keys"]:
                for doc_id in self._keys.get(key, ()):
                    if doc_id != exclude:
                        votes[doc_id] += 1
            for doc_id, v in votes.items():
                if v / config.LSH_BANDS < config.CANDIDATE_THRESHOLD / 2:
                    continue
                sim = jaccard(fp["sig"], self._sigs.get(doc_id, b""))
                if sim >= config.CANDIDATE_THRESHOLD:
                    out.append((doc_id, sim))
        out.sort(key=lambda x: -x[1])
        return out[:config.MAX_SOURCES]


corpus_index = CorpusIndex()


def ensure_index(db) -> None:
    if not corpus_index.loaded:
        corpus_index.load(db)
        corpus_index.loaded = True
