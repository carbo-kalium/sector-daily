"""Load S&P 500 company configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml


def load_sp500_companies(config_path: Path) -> Dict[str, List[dict]]:
    """
    Load S&P 500 companies grouped by sector.
    
    Args:
        config_path: Path to sp500_companies.yml
    
    Returns:
        Dict mapping sector names to lists of company dicts
    """
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get('sp500_companies', {})
