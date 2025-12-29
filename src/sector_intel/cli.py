from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from sector_intel.pipeline import PipelineConfig, run
from sector_intel.pipeline_sp500 import run_sp500


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sector-intel")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Fetch RSS, classify into sectors, and generate Markdown posts")
    run_p.add_argument("--date", default=date.today().isoformat(), help="Run date in YYYY-MM-DD")
    run_p.add_argument("--mode", default="sectors", choices=["sectors", "sp500", "both"], help="Fetch mode: sectors, sp500, or both")
    run_p.add_argument("--rss", default="config/rss_sources.yml", help="Path to RSS sources YAML")
    run_p.add_argument("--sectors", default="config/sectors.yml", help="Path to sector rules YAML")
    run_p.add_argument("--sp500", default="config/sp500_companies.yml", help="Path to S&P 500 companies YAML")
    run_p.add_argument("--templates", default="templates", help="Templates directory")
    run_p.add_argument("--template", default="sector_daily.md.j2", help="Template filename")
    run_p.add_argument("--output", default="output", help="Output directory")

    p.add_argument("--log-level", default="INFO", help="Logging level")

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO))

    if args.cmd == "run":
        run_date = date.fromisoformat(args.date)
        
        # Run sector-based news fetching
        if args.mode in ["sectors", "both"]:
            cfg = PipelineConfig(
                rss_sources_path=Path(args.rss),
                sector_rules_path=Path(args.sectors),
                templates_dir=Path(args.templates),
                template_name=str(args.template),
                output_dir=Path(args.output),
            )
            run(run_date=run_date, cfg=cfg)
        
        # Run S&P 500 company news fetching
        if args.mode in ["sp500", "both"]:
            run_sp500(
                run_date=run_date,
                sp500_path=Path(args.sp500),
                rss_config_path=Path(args.rss),
                templates_dir=Path(args.templates),
                output_dir=Path(args.output),
            )
        
        return

    raise SystemExit(2)
