from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sector_intel.models import Article
from sector_intel.utils.text import make_excerpt


def _env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_sector_post(
    *,
    templates_dir: str | Path,
    template_name: str,
    output_path: str | Path,
    date: str,
    sector: str,
    etf: str | None,
    articles: list[Article],
    source_count: int,
) -> None:
    templates_dir = Path(templates_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = _env(templates_dir)
    template = env.get_template(template_name)

    article_views = [_article_view(a) for a in articles]
    
    top_titles = ", ".join(
        a["title"][:50] + ("..." if len(a["title"]) > 50 else "")
        for a in article_views[:3]
    ) if article_views else "No stories today"
    
    summary_keywords = _extract_keywords(articles) if articles else "market updates"

    rendered = template.render(
        date=date,
        sector=sector,
        etf=etf or "N/A",
        articles=article_views,
        article_count=len(articles),
        top_titles=top_titles,
        summary_keywords=summary_keywords,
        source_count=source_count,
    )

    output_path.write_text(rendered.strip() + "\n", encoding="utf-8")


def _extract_keywords(articles: list[Article], max_keywords: int = 5) -> str:
    from collections import Counter
    import re
    
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "be", "has",
        "have", "had", "will", "can", "could", "should", "would", "may", "might"
    }
    
    words = []
    for a in articles[:10]:
        text = (a.title or "") + " " + (a.summary or "")
        text_lower = text.lower()
        tokens = re.findall(r'\b[a-z]{4,}\b', text_lower)
        words.extend([w for w in tokens if w not in stopwords])
    
    if not words:
        return "market updates"
    
    common = Counter(words).most_common(max_keywords)
    return ", ".join(w for w, _ in common)


def _article_view(a: Article) -> dict:
    d = asdict(a)
    dt = d.get("published_at")
    d["published_at_iso"] = dt.isoformat() if dt else None

    excerpt = None
    if a.summary:
        excerpt = a.summary
    elif a.content:
        excerpt = a.content

    if excerpt:
        excerpt = make_excerpt(excerpt, max_chars=280)

    d["excerpt"] = excerpt
    return d
