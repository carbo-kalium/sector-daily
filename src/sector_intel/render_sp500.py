"""Render S&P 500 company news posts."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from sector_intel.models import Article


def render_sp500_post(
    *,
    date_str: str,
    articles_by_sector_and_company: dict[str, dict[str, list[Article]]],
    companies_by_sector: dict[str, list[dict]],
    templates_dir: Path,
    template_name: str = "sp500_daily.md.j2",
) -> str:
    """
    Render S&P 500 company news post using Jinja template.
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        articles_by_sector_and_company: Dict mapping sector -> ticker -> articles
        companies_by_sector: Dict mapping sector -> company info (for names)
        templates_dir: Directory containing Jinja templates
        template_name: Template filename
    
    Returns:
        Rendered markdown content
    """
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template(template_name)
    
    # Create a lookup map for company names
    ticker_to_name = {}
    for sector, companies in companies_by_sector.items():
        for company in companies:
            ticker_to_name[company['ticker']] = company['name']
    
    # Prepare data for template: sort sectors and companies
    sorted_sectors = {}
    
    for sector in sorted(articles_by_sector_and_company.keys()):
        company_articles_map = articles_by_sector_and_company[sector]
        
        # Sort companies by ticker
        sorted_companies = {}
        for ticker in sorted(company_articles_map.keys()):
            articles = company_articles_map[ticker]
            company_name = ticker_to_name.get(ticker, ticker)
            
            sorted_companies[ticker] = {
                'name': company_name,
                'articles': articles,
            }
        
        sorted_sectors[sector] = sorted_companies
    
    return template.render(
        date=date_str,
        sectors=sorted_sectors,
    )
