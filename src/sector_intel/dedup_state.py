from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from sector_intel.dedup import fingerprint
from sector_intel.models import Article

logger = logging.getLogger(__name__)


class PersistentDedup:
    def __init__(self, state_dir: str | Path = ".state", retention_days: int = 7):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "seen_articles.json"
        self.retention_days = retention_days
        self._seen: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_file.exists():
            return
        try:
            with self.state_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._seen = data
        except Exception:
            logger.warning("Failed to load dedup state, starting fresh")
            self._seen = {}

    def _save(self) -> None:
        try:
            with self.state_file.open("w", encoding="utf-8") as f:
                json.dump(self._seen, f, indent=2)
        except Exception:
            logger.exception("Failed to save dedup state")

    def _cleanup_expired(self) -> None:
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
        expired = [fp for fp, ts in self._seen.items() if ts < cutoff]
        for fp in expired:
            del self._seen[fp]
        if expired:
            logger.info("Cleaned up %d expired fingerprints", len(expired))

    def is_seen(self, article: Article) -> bool:
        fp = fingerprint(article)
        return fp in self._seen

    def mark_seen(self, article: Article) -> None:
        fp = fingerprint(article)
        self._seen[fp] = datetime.now().isoformat()

    def deduplicate(self, articles: list[Article]) -> list[Article]:
        self._cleanup_expired()
        out = [a for a in articles if not self.is_seen(a)]
        for a in out:
            self.mark_seen(a)
        self._save()
        return out
