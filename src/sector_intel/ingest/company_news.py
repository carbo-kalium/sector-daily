"""Fetch company-specific news from Google News RSS feeds."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import replace
from difflib import SequenceMatcher
from typing import List
from urllib.parse import quote_plus

from sector_intel.ingest.rss import fetch_and_normalize
from sector_intel.models import Article, FeedSource

logger = logging.getLogger(__name__)


def is_similar_title(title1: str, title2: str, threshold: float = 0.75) -> bool:
    """
    Check if two article titles are similar using sequence matching.
    
    Args:
        title1: First title
        title2: Second title
        threshold: Similarity threshold (0-1), default 0.75
    
    Returns:
        True if titles are similar enough to be considered duplicates
    """
    # Normalize titles for comparison
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    
    # Calculate similarity ratio
    ratio = SequenceMatcher(None, t1, t2).ratio()
    return ratio >= threshold


def deduplicate_by_title_similarity(articles: List[Article], threshold: float = 0.75) -> List[Article]:
    """
    Remove articles with similar titles (likely covering same story).
    
    Args:
        articles: List of articles to deduplicate
        threshold: Similarity threshold (0-1)
    
    Returns:
        Deduplicated list of articles
    """
    if not articles:
        return []
    
    unique_articles = []
    
    for article in articles:
        # Check if this article is similar to any already added
        is_duplicate = False
        for existing in unique_articles:
            if is_similar_title(article.title, existing.title, threshold):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_articles.append(article)
    
    return unique_articles


def fetch_company_news(
    ticker: str,
    company_name: str,
    search_terms: List[str],
    user_agent: str,
    timeout_seconds: int = 20,
    delay_range: tuple[float, float] = (0.5, 2.0),
) -> List[Article]:
    """
    Fetch news for a specific company using Google News RSS.
    
    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        search_terms: List of search terms (ticker, name, abbreviations)
        user_agent: User agent string for requests
        timeout_seconds: Request timeout
        delay_range: Random delay range in seconds (min, max)
    
    Returns:
        List of articles for this company
    """
    # Build search query using ticker and company name
    # Format: "Apple AAPL stock" or "Microsoft MSFT stock"
    primary_term = search_terms[0] if search_terms else company_name
    query = f"{primary_term} {ticker} stock"
    encoded_query = quote_plus(query)
    
    # Google News RSS search URL
    feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    feed_source = FeedSource(
        name=f"{company_name} ({ticker})",
        url=feed_url
    )
    
    try:
        # Add random delay to avoid rate limiting
        delay = random.uniform(*delay_range)
        time.sleep(delay)
        
        articles = fetch_and_normalize(feed_source, user_agent=user_agent, timeout_seconds=timeout_seconds)
        
        logger.debug(f"Fetched {len(articles)} articles for {ticker} ({company_name})")
        return articles
        
    except Exception as e:
        logger.warning(f"Failed to fetch news for {ticker} ({company_name}): {e}")
        return []


def fetch_sp500_news(
    companies_by_sector: dict[str, list[dict]],
    user_agent: str,
    timeout_seconds: int = 20,
    max_duration_seconds: int = 3600,
    max_articles_per_company: int = 10,
) -> dict[str, dict[str, list[Article]]]:
    """
    Fetch news for all S&P 500 companies with rate limiting and per-company deduplication.
    
    Args:
        companies_by_sector: Dict mapping sector names to list of company dicts
        user_agent: User agent string
        timeout_seconds: Request timeout
        max_duration_seconds: Maximum time to spend fetching (default 1 hour)
        max_articles_per_company: Max articles to keep per company after deduplication (default 10)
    
    Returns:
        Dict mapping sector names to dicts of {company_ticker: [articles]}
    """
    start_time = time.time()
    articles_by_sector: dict[str, dict[str, list[Article]]] = {}
    total_companies = sum(len(companies) for companies in companies_by_sector.values())
    
    logger.info(f"Starting S&P 500 news fetch for {total_companies} companies (max {max_duration_seconds}s)")
    
    processed = 0
    for sector, companies in companies_by_sector.items():
        company_articles_map: dict[str, list[Article]] = {}
        
        for company in companies:
            # Check if we've exceeded max duration
            elapsed = time.time() - start_time
            if elapsed > max_duration_seconds:
                logger.warning(f"Reached max duration ({max_duration_seconds}s), stopping at {processed}/{total_companies} companies")
                break
            
            ticker = company['ticker']
            name = company['name']
            search_terms = company.get('search_terms', [name, ticker])
            
            # Fetch news for this company
            company_articles = fetch_company_news(
                ticker=ticker,
                company_name=name,
                search_terms=search_terms,
                user_agent=user_agent,
                timeout_seconds=timeout_seconds,
            )
            
            if not company_articles:
                # Skip companies with no news
                processed += 1
                continue
            
            # Sort by publish date (most recent first)
            sorted_articles = sorted(
                company_articles,
                key=lambda a: (
                    a.published_at is not None,
                    a.published_at.timestamp() if a.published_at else 0.0,
                ),
                reverse=True,
            )
            
            # Deduplicate by title similarity
            unique_articles = deduplicate_by_title_similarity(sorted_articles, threshold=0.75)
            
            # Limit to top N most recent unique articles
            limited_articles = unique_articles[:max_articles_per_company]
            
            # Set sector for all articles using replace() since Article is frozen
            articles_with_sector = [replace(article, sector=sector) for article in limited_articles]
            
            # Only include company if it has articles after filtering
            if articles_with_sector:
                company_articles_map[ticker] = articles_with_sector
                logger.debug(f"{ticker}: {len(limited_articles)} unique articles (from {len(company_articles)} total)")
            
            processed += 1
            
            if processed % 50 == 0:
                logger.info(f"Progress: {processed}/{total_companies} companies ({elapsed:.1f}s elapsed)")
        
        articles_by_sector[sector] = company_articles_map
        total_sector_articles = sum(len(articles) for articles in company_articles_map.values())
        logger.info(f"Fetched {total_sector_articles} articles for {sector} sector ({len(company_articles_map)} companies with news)")
    
    total_articles = sum(
        sum(len(articles) for articles in company_map.values())
        for company_map in articles_by_sector.values()
    )
    elapsed = time.time() - start_time
    logger.info(f"Completed S&P 500 fetch: {total_articles} articles from {processed} companies in {elapsed:.1f}s")
    
    return articles_by_sector
