"""Render S&P 500 company news posts."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from sector_intel.models import Article


def render_sp500_post(
    *,
    date_str: str,
    articles_by_sector: dict[str, list[Article]],
    templates_dir: Path,
    template_name: str = "sp500_daily.md.j2",
) -> str:
    """
    Render S&P 500 company news post using Jinja template.
    
    Args:
        date_str: Date string (YYYY-MM-DD)
        articles_by_sector: Dict mapping sector names to article lists
        templates_dir: Directory containing Jinja templates
        template_name: Template filename
    
    Returns:
        Rendered markdown content
    """
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template(template_name)
    
    # Sort articles by publish date within each sector
    sorted_articles_by_sector = {}
    for sector, articles in articles_by_sector.items():
        sorted_articles = sorted(
            articles,
            key=lambda a: (
                a.published_at is not None,
                a.published_at.timestamp() if a.published_at else 0.0,
            ),
            reverse=True,
        )
        sorted_articles_by_sector[sector] = sorted_articles
    
    # Sort sectors alphabetically
    sorted_sectors = dict(sorted(sorted_articles_by_sector.items()))
    
    return template.render(
        date=date_str,
        articles_by_sector=sorted_sectors,
    )
