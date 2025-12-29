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
    
    # Fetch news for all companies (returns dict[sector, dict[ticker, articles]])
    # Articles are already deduplicated per company and limited to 10 per company
    articles_by_sector_and_company = fetch_sp500_news(
        companies_by_sector=companies_by_sector,
        user_agent=req.user_agent,
        timeout_seconds=req.timeout_seconds,
        max_duration_seconds=3600,  # 1 hour max
        max_articles_per_company=10,  # Max 10 unique articles per company
    )
    
    # Apply 24-hour window filter to all articles
    run_datetime = datetime.combine(run_date, datetime.min.time()).replace(hour=12, tzinfo=timezone.utc)
    window_start = run_datetime - timedelta(hours=24)
    window_end = run_datetime
    
    filtered_by_sector_and_company: dict[str, dict[str, list[Article]]] = {}
    total_before = 0
    total_after = 0
    
    for sector, company_articles_map in articles_by_sector_and_company.items():
        filtered_company_map: dict[str, list[Article]] = {}
        
        for ticker, articles in company_articles_map.items():
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
            
            # Only include company if it has articles after 24h filtering
            if filtered_articles:
                filtered_company_map[ticker] = filtered_articles
                total_after += len(filtered_articles)
        
        filtered_by_sector_and_company[sector] = filtered_company_map
    
    logger.info(f"Filtered {total_before} articles to {total_after} within 24-hour window")
    
    # Render and save S&P 500 post
    date_str = run_date.isoformat()
    day_dir = output_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    
    content = render_sp500_post(
        date_str=date_str,
        articles_by_sector_and_company=filtered_by_sector_and_company,
        companies_by_sector=companies_by_sector,
        templates_dir=templates_dir,
        template_name="sp500_daily.md.j2",
    )
    
    out_path = day_dir / "sp500.md"
    out_path.write_text(content, encoding="utf-8")
    logger.info(f"Wrote S&P 500 post: {out_path} ({total_after} articles)")
    
    return filtered_by_sector_and_company
