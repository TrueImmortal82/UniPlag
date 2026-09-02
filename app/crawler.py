import re
import urllib.request
import urllib.robotparser
from urllib.parse import urlparse
from html import unescape

UA = "UniPlagBot/1.0 (university plagiarism checker)"
MAX_BYTES = 2 * 1024 * 1024


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|br)>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if len(ln) > 2)


def fetch_url(url: str, respect_robots: bool = True) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Поддерживаются только http/https")
    if respect_robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        try:
            rp.read()
            if not rp.can_fetch(UA, url):
                raise PermissionError(f"Запрещено robots.txt: {url}")
        except PermissionError:
            raise
        except Exception:
            pass

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read(MAX_BYTES)
        charset = resp.headers.get_content_charset() or "utf-8"
    html = raw.decode(charset, errors="ignore")

    title_m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = unescape(title_m.group(1)).strip()[:300] if title_m else url
    body = _strip_html(html)
    words = len(re.findall(r"\S+", body))
    if words < 50:
        raise ValueError("Страница почти без текста — пропущена")
    return {"title": title, "text": body, "domain": parsed.netloc, "url": url}
