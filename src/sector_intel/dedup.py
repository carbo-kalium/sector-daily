from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, urlunsplit

from sector_intel.models import Article


def canonicalize_url(url: str) -> str:
    """Normalize URLs for deduping (strip fragments, normalize scheme/host casing)."""

    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() if parts.scheme else "https"
    netloc = parts.netloc.lower()
    path = parts.path or ""
    query = parts.query or ""
    return urlunsplit((scheme, netloc, path, query, ""))


def fingerprint(article: Article) -> str:
    """Compute a stable fingerprint used for basic deduplication."""

    link = canonicalize_url(article.link) if article.link else ""
    base = "|".join([
        (article.guid or ""),
        link,
        (article.title or "").strip().lower(),
        (article.source_name or "").strip().lower(),
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def deduplicate(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    out: list[Article] = []

    for a in articles:
        fp = fingerprint(a)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(a)

    return out
