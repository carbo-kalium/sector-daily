from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sector_intel.models import FeedSource


@dataclass(frozen=True, slots=True)
class RequestConfig:
    user_agent: str
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class SectorConfig:
    etf: str | None
    keywords: list[str]
    companies: list[str]


@dataclass(frozen=True, slots=True)
class SectorRules:
    default_sector: str
    sectors: dict[str, SectorConfig]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML at {path}: expected mapping at root")
    return data


def load_rss_sources(config_path: str | Path) -> tuple[list[FeedSource], RequestConfig]:
    path = Path(config_path)
    data = _read_yaml(path)

    raw_sources = data.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError(f"Invalid rss_sources.yml: missing non-empty 'sources' list")

    sources: list[FeedSource] = []
    for s in raw_sources:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name", "")).strip()
        url = str(s.get("url", "")).strip()
        if not name or not url:
            continue
        sources.append(FeedSource(name=name, url=url))

    request = data.get("request") or {}
    if not isinstance(request, dict):
        request = {}

    user_agent = str(request.get("user_agent") or "sector-intel/0.1").strip()
    timeout_seconds = int(request.get("timeout_seconds") or 20)

    return sources, RequestConfig(user_agent=user_agent, timeout_seconds=timeout_seconds)


def load_sector_rules(config_path: str | Path) -> SectorRules:
    path = Path(config_path)
    data = _read_yaml(path)

    default_sector = str(data.get("default_sector") or "Other").strip() or "Other"

    raw_sectors = data.get("sectors")
    if not isinstance(raw_sectors, dict) or not raw_sectors:
        raise ValueError("Invalid sectors.yml: missing non-empty 'sectors' mapping")

    sectors: dict[str, SectorConfig] = {}
    for sector_name, cfg in raw_sectors.items():
        if not isinstance(sector_name, str) or not sector_name.strip():
            continue
        if not isinstance(cfg, dict):
            continue
        
        etf = str(cfg.get("etf", "")).strip() or None
        
        keywords_raw = cfg.get("keywords")
        keywords = [str(k).strip() for k in (keywords_raw or []) if str(k).strip()]
        
        companies_raw = cfg.get("companies")
        companies = [str(c).strip() for c in (companies_raw or []) if str(c).strip()]
        
        if keywords or companies:
            sectors[sector_name.strip()] = SectorConfig(
                etf=etf,
                keywords=keywords,
                companies=companies,
            )

    if not sectors:
        raise ValueError("Invalid sectors.yml: no sector keywords configured")

    return SectorRules(default_sector=default_sector, sectors=sectors)
