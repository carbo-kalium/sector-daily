from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sector_intel.classification.keyword_rules import KeywordSectorClassifier
from sector_intel.config import load_rss_sources, load_sector_rules
from sector_intel.dedup import deduplicate
from sector_intel.ingest.rss import fetch_and_normalize
from sector_intel.models import Article
from sector_intel.render import render_sector_post

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    rss_sources_path: Path
    sector_rules_path: Path
    templates_dir: Path
    template_name: str
    output_dir: Path


def run(*, run_date: date, cfg: PipelineConfig) -> dict[str, list[Article]]:
    sources, req = load_rss_sources(cfg.rss_sources_path)
    rules = load_sector_rules(cfg.sector_rules_path)

    classifier = KeywordSectorClassifier(rules)

    all_articles: list[Article] = []
    for s in sources:
        logger.info("Fetching: %s (%s)", s.name, s.url)
        try:
            all_articles.extend(
                fetch_and_normalize(s, user_agent=req.user_agent, timeout_seconds=req.timeout_seconds)
            )
        except Exception:
            logger.exception("Failed fetching source: %s", s.url)

    all_articles = deduplicate(all_articles)

    classified: list[Article] = [classifier.assign_sector(a) for a in all_articles]

    by_sector: dict[str, list[Article]] = defaultdict(list)
    for a in classified:
        by_sector[a.sector or rules.default_sector].append(a)

    date_str = run_date.isoformat()
    day_dir = cfg.output_dir / date_str

    all_sectors = sorted(
        set(rules.sectors.keys()) | {rules.default_sector} | set(by_sector.keys()),
        key=lambda s: s.lower(),
    )

    rendered: dict[str, list[Article]] = {}
    for sector in all_sectors:
        items = by_sector.get(sector, [])
        items_sorted = sorted(
            items,
            key=lambda a: (
                a.published_at is not None,
                a.published_at.timestamp() if a.published_at else 0.0,
            ),
            reverse=True,
        )
        rendered[sector] = items_sorted

        sector_config = rules.sectors.get(sector)
        etf_ticker = sector_config.etf if sector_config else None

        safe_sector = sector.lower().replace(" ", "-")
        out_path = day_dir / f"{safe_sector}.md"
        render_sector_post(
            templates_dir=cfg.templates_dir,
            template_name=cfg.template_name,
            output_path=out_path,
            date=date_str,
            sector=sector,
            etf=etf_ticker,
            articles=items_sorted,
            source_count=len(sources),
        )

    return rendered
