"""Pipeline for S&P 500 company news fetching."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sector_intel.config import load_rss_sources
from sector_intel.config_sp500 import load_sp500_companies
from sector_intel.dedup import deduplicate
from sector_intel.ingest.company_news import fetch_sp500_news
from sector_intel.models import Article
from sector_intel.render_sp500 import render_sp500_post

logger = logging.getLogger(__name__)


def run_sp500(
    *,
    run_date: date,
    sp500_path: Path,
    rss_config_path: Path,
    templates_dir: Path,
    output_dir: Path,
) -> dict[str, list[Article]]:
    """
    Run S&P 500 company news pipeline.
    
    Args:
        run_date: Date to run the pipeline for
        sp500_path: Path to sp500_companies.yml
        rss_config_path: Path to rss_sources.yml (for request config)
        templates_dir: Path to templates directory
        output_dir: Path to output directory
    
    Returns:
        Dict mapping sector names to article lists
    """
    # Load configurations
    companies_by_sector = load_sp500_companies(sp500_path)
    _, req = load_rss_sources(rss_config_path)
    
    logger.info(f"Starting S&P 500 company news pipeline for {run_date}")
    
    # Fetch news for all companies
    articles_by_sector = fetch_sp500_news(
        companies_by_sector=companies_by_sector,
        user_agent=req.user_agent,
        timeout_seconds=req.timeout_seconds,
        max_duration_seconds=3600,  # 1 hour max
    )
    
    # Deduplicate articles within each sector
    for sector in articles_by_sector:
        articles_by_sector[sector] = deduplicate(articles_by_sector[sector])
    
    # Apply 24-hour window filter
    run_datetime = datetime.combine(run_date, datetime.min.time()).replace(hour=12, tzinfo=timezone.utc)
    window_start = run_datetime - timedelta(hours=24)
    window_end = run_datetime
    
    filtered_by_sector: dict[str, list[Article]] = {}
    total_before = 0
    total_after = 0
    
    for sector, articles in articles_by_sector.items():
        total_before += len(articles)
        filtered_articles: list[Article] = []
        
        for article in articles:
            if article.published_at is None:
                filtered_articles.append(article)
                continue
            
            pub_time = article.published_at
            if pub_time.tzinfo is None:
                pub_time = pub_time.replace(tzinfo=timezone.utc)
            
            if window_start <= pub_time <= window_end:
                filtered_articles.append(article)
        
        filtered_by_sector[sector] = filtered_articles
        total_after += len(filtered_articles)
    
    logger.info(f"Filtered {total_before} articles to {total_after} within 24-hour window")
    
    # Render and save S&P 500 post
    date_str = run_date.isoformat()
    day_dir = output_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    
    content = render_sp500_post(
        date_str=date_str,
        articles_by_sector=filtered_by_sector,
        templates_dir=templates_dir,
        template_name="sp500_daily.md.j2",
        max_articles_per_sector=50,  # Limit to top 50 most recent per sector
    )
    
    out_path = day_dir / "sp500.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote S&P 500 post: {out_path} ({total_after} articles)")
    
    return filtered_by_sector
