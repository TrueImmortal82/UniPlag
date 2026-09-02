import re


TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё_]+(?:['’\-][0-9A-Za-zА-Яа-яЁё]+)*")
SENT_RE = re.compile(r"[^.!?\n]+[.!?…]*")


def tokenize(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


def sentences(text: str) -> list[tuple[int, int, str]]:
    out = []
    for m in SENT_RE.finditer(text):
        s = m.group(0).strip()
        if s:
            out.append((m.start(), m.end(), s))
    return out
