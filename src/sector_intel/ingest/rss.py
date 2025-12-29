from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import feedparser
import requests
from dateutil import parser as date_parser

from sector_intel.models import Article, FeedSource
from sector_intel.utils.text import make_excerpt, strip_html

logger = logging.getLogger(__name__)


def fetch_feed(source: FeedSource, *, user_agent: str, timeout_seconds: int) -> feedparser.FeedParserDict:
    """Fetch RSS/Atom XML and parse via feedparser."""

    headers = {"User-Agent": user_agent}
    resp = requests.get(source.url, headers=headers, timeout=timeout_seconds)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, str) and value.strip():
        try:
            return date_parser.parse(value)
        except Exception:
            return None

    try:
        return date_parser.parse(str(value))
    except Exception:
        return None


def normalize_entry(entry: feedparser.FeedParserDict, source_name: str) -> Article:
    """Normalize a feedparser entry into the common Article schema."""

    title = str(entry.get("title") or "").strip()
    link = str(entry.get("link") or "").strip()
    guid = str(entry.get("id") or entry.get("guid") or "").strip() or None

    published_raw = entry.get("published") or entry.get("updated")
    published_at = _parse_datetime(published_raw)

    author = str(entry.get("author") or "").strip() or None

    summary_raw = entry.get("summary") or entry.get("description")
    summary = strip_html(str(summary_raw)) if summary_raw else None

    content_val: str | None = None
    content_list = entry.get("content")
    if isinstance(content_list, list) and content_list:
        first = content_list[0]
        if isinstance(first, dict) and first.get("value"):
            content_val = strip_html(str(first.get("value")))

    if content_val is None and entry.get("content") and isinstance(entry.get("content"), str):
        content_val = strip_html(str(entry.get("content")))

    excerpt_source = content_val or summary or ""
    excerpt = make_excerpt(excerpt_source) if excerpt_source else None

    extra: dict[str, Any] = {}
    for k in ("tags", "media_thumbnail", "media_content"):
        if k in entry:
            extra[k] = entry.get(k)

    return Article(
        source_name=source_name,
        title=title,
        link=link,
        guid=guid,
        published_at=published_at,
        author=author,
        summary=summary,
        content=content_val,
        extra=extra,
    )


def fetch_and_normalize(source: FeedSource, *, user_agent: str, timeout_seconds: int) -> list[Article]:
    parsed = fetch_feed(source, user_agent=user_agent, timeout_seconds=timeout_seconds)

    if getattr(parsed, "bozo", False):
        logger.warning("Bozo feed parse for %s: %s", source.url, getattr(parsed, "bozo_exception", None))

    entries = getattr(parsed, "entries", None)
    if not entries:
        return []

    articles: list[Article] = []
    for e in entries:
        try:
            a = normalize_entry(e, source.name)
            if a.title and a.link:
                articles.append(a)
        except Exception:
            logger.exception("Failed to normalize entry from %s", source.url)

    return articles
