#!/usr/bin/env python3
"""Quick test script for S&P 500 company news fetching."""

import logging
from datetime import date
from pathlib import Path

from src.sector_intel.config import load_rss_sources
from src.sector_intel.config_sp500 import load_sp500_companies
from src.sector_intel.ingest.company_news import fetch_company_news, deduplicate_by_title_similarity

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)

# Load configurations
sp500_path = Path("config/sp500_companies.yml")
rss_config_path = Path("config/rss_sources.yml")

companies_by_sector = load_sp500_companies(sp500_path)
_, req = load_rss_sources(rss_config_path)

# Test with first 10 companies from different sectors
test_companies = []
for sector, companies in companies_by_sector.items():
    if len(test_companies) < 10:
        # Take first company from each sector
        if companies:
            test_companies.append({
                'sector': sector,
                'ticker': companies[0]['ticker'],
                'name': companies[0]['name'],
                'search_terms': companies[0]['search_terms']
            })

logger.info(f"Testing with {len(test_companies)} companies:")
for company in test_companies:
    logger.info(f"  - {company['ticker']}: {company['name']} ({company['sector']})")

print("\n" + "="*80)
print("Starting news fetch test...")
print("="*80 + "\n")

# Fetch news for each test company
results = {}
for i, company in enumerate(test_companies, 1):
    ticker = company['ticker']
    name = company['name']
    sector = company['sector']
    search_terms = company['search_terms']
    
    logger.info(f"[{i}/{len(test_companies)}] Fetching news for {ticker} ({name})...")
    
    articles = fetch_company_news(
        ticker=ticker,
        company_name=name,
        search_terms=search_terms,
        user_agent=req.user_agent,
        timeout_seconds=req.timeout_seconds,
        delay_range=(0.5, 1.0),  # Shorter delays for testing
    )
    
    # Sort by publish date
    sorted_articles = sorted(
        articles,
        key=lambda a: (
            a.published_at is not None,
            a.published_at.timestamp() if a.published_at else 0.0,
        ),
        reverse=True,
    )
    
    # Deduplicate by title similarity
    unique_articles = deduplicate_by_title_similarity(sorted_articles, threshold=0.75)
    
    # Limit to top 10
    limited_articles = unique_articles[:10]
    
    results[ticker] = {
        'name': name,
        'sector': sector,
        'total_count': len(articles),
        'unique_count': len(unique_articles),
        'article_count': len(limited_articles),
        'articles': limited_articles[:3]  # Keep first 3 for display
    }
    
    logger.info(f"  ✓ {len(articles)} total → {len(unique_articles)} unique → {len(limited_articles)} shown")

# Display results
print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80 + "\n")

total_articles = sum(r['article_count'] for r in results.values())
total_fetched = sum(r['total_count'] for r in results.values())
total_unique = sum(r['unique_count'] for r in results.values())
print(f"Total articles fetched: {total_fetched}")
print(f"After deduplication: {total_unique}")
print(f"After limiting (max 10/company): {total_articles}")
print(f"Average shown per company: {total_articles / len(test_companies):.1f}\n")

for ticker, result in results.items():
    print(f"\n{ticker} - {result['name']} ({result['sector']})")
    print(f"  Articles: {result['total_count']} total → {result['unique_count']} unique → {result['article_count']} shown")
    
    if result['articles']:
        print("  Sample headlines:")
        for i, article in enumerate(result['articles'], 1):
            print(f"    {i}. {article.title[:80]}...")
            print(f"       Source: {article.source_name}")
            if article.published_at:
                print(f"       Published: {article.published_at}")

print("\n" + "="*80)
print("Test complete!")
print("="*80)
