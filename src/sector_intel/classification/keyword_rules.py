from __future__ import annotations

from dataclasses import dataclass

from sector_intel.config import SectorRules
from sector_intel.models import Article


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    sector: str
    score: int


class KeywordSectorClassifier:
    def __init__(self, rules: SectorRules):
        self._default = rules.default_sector
        self._sector_keywords: dict[str, list[str]] = {}
        self._sector_companies: dict[str, list[str]] = {}
        
        for sector, config in rules.sectors.items():
            if config.keywords:
                self._sector_keywords[sector] = [k.lower() for k in config.keywords]
            if config.companies:
                self._sector_companies[sector] = [c.lower() for c in config.companies]

    def classify(self, article: Article) -> ClassificationResult:
        haystack = " ".join(
            [
                article.title or "",
                article.summary or "",
                article.content or "",
            ]
        ).lower()

        best_sector = self._default
        best_score = 0

        for sector in set(self._sector_keywords.keys()) | set(self._sector_companies.keys()):
            score = 0
            
            keywords = self._sector_keywords.get(sector, [])
            for kw in keywords:
                if not kw:
                    continue
                if kw in haystack:
                    score += 1
            
            companies = self._sector_companies.get(sector, [])
            for company in companies:
                if not company:
                    continue
                if company in haystack:
                    score += 2
            
            if score > best_score:
                best_sector = sector
                best_score = score

        return ClassificationResult(sector=best_sector, score=best_score)

    def assign_sector(self, article: Article) -> Article:
        res = self.classify(article)
        return Article(
            source_name=article.source_name,
            title=article.title,
            link=article.link,
            guid=article.guid,
            published_at=article.published_at,
            author=article.author,
            summary=article.summary,
            content=article.content,
            sector=res.sector,
            extra=article.extra,
        )
