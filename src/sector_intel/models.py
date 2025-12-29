from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Article:
    """Normalized representation of an RSS entry."""

    source_name: str
    title: str
    link: str

    guid: str | None = None
    published_at: datetime | None = None
    author: str | None = None

    summary: str | None = None
    content: str | None = None

    sector: str | None = None

    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FeedSource:
    name: str
    url: str
