import hashlib
import random
import struct

from . import config
from .textutil import tokenize

_P = (1 << 61) - 1


def _perm_params(num: int, seed: int = 42) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    return [(rng.randrange(1, _P), rng.randrange(0, _P)) for _ in range(num)]


_PERMS = None


def perms() -> list[tuple[int, int]]:
    global _PERMS
    if _PERMS is None:
        _PERMS = _perm_params(config.MINHASH_PERM)
    return _PERMS


def shingle_hashes(tokens: list[tuple[str, int, int]]) -> list[int]:
    k = config.SHINGLE_K
    words = [t[0].lower().replace("ё", "е") for t in tokens]
    joined = [" ".join(words[i:i + k]) for i in range(len(words) - k + 1)]
    return [int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little") for s in joined]


def minhash_signature(hashes: list[int]) -> bytes:
    if not hashes:
        hashes = [0]
    sig = []
    for a, b in perms():
        m = min(((a * h + b) % _P) & 0xFFFFFFFFFFFFFFFF for h in hashes)
        sig.append(m)
    return struct.pack(f"<{len(sig)}Q", *sig)


def lsh_keys(sig: bytes) -> list[str]:
    rows = config.LSH_ROWS
    return [
        hashlib.md5(sig[b * rows * 8:(b + 1) * rows * 8]).hexdigest()
        for b in range(config.LSH_BANDS)
    ]


def fingerprint(text: str) -> dict:
    tokens = tokenize(text)
    hashes = shingle_hashes(tokens)
    sig = minhash_signature(hashes)
    return {
        "tokens": tokens,
        "hashes": hashes,
        "sig": sig,
        "keys": lsh_keys(sig),
    }


def jaccard(sig_a: bytes, sig_b: bytes) -> float:
    if not sig_a or len(sig_a) != len(sig_b):
        return 0.0
    n = len(sig_a) // 8
    same = sum(1 for x, y in zip(struct.unpack(f"<{n}Q", sig_a), struct.unpack(f"<{n}Q", sig_b)) if x == y)
    return same / n
