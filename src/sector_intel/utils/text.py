from __future__ import annotations

import re
from html import unescape

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Best-effort HTML tag removal for RSS summaries/content."""

    no_tags = _TAG_RE.sub(" ", text)
    return normalize_whitespace(unescape(no_tags))


def normalize_whitespace(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def make_excerpt(text: str, max_chars: int = 280) -> str:
    cleaned = normalize_whitespace(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"
