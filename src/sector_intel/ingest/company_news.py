"""Fetch company-specific news from Google News RSS feeds."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import replace
from typing import List
from urllib.parse import quote_plus

from sector_intel.ingest.rss import fetch_and_normalize
from sector_intel.models import Article, FeedSource

logger = logging.getLogger(__name__)


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
) -> dict[str, list[Article]]:
    """
    Fetch news for all S&P 500 companies with rate limiting.
    
    Args:
        companies_by_sector: Dict mapping sector names to list of company dicts
        user_agent: User agent string
        timeout_seconds: Request timeout
        max_duration_seconds: Maximum time to spend fetching (default 1 hour)
    
    Returns:
        Dict mapping sector names to lists of articles
    """
    start_time = time.time()
    articles_by_sector: dict[str, list[Article]] = {}
    total_companies = sum(len(companies) for companies in companies_by_sector.values())
    
    logger.info(f"Starting S&P 500 news fetch for {total_companies} companies (max {max_duration_seconds}s)")
    
    processed = 0
    for sector, companies in companies_by_sector.items():
        sector_articles: list[Article] = []
        
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
            
            # Set sector for all articles using replace() since Article is frozen
            articles_with_sector = [replace(article, sector=sector) for article in company_articles]
            
            sector_articles.extend(articles_with_sector)
            processed += 1
            
            if processed % 50 == 0:
                logger.info(f"Progress: {processed}/{total_companies} companies ({elapsed:.1f}s elapsed)")
        
        articles_by_sector[sector] = sector_articles
        logger.info(f"Fetched {len(sector_articles)} articles for {sector} sector ({len(companies)} companies)")
    
    total_articles = sum(len(articles) for articles in articles_by_sector.values())
    elapsed = time.time() - start_time
    logger.info(f"Completed S&P 500 fetch: {total_articles} articles from {processed} companies in {elapsed:.1f}s")
    
    return articles_by_sector
