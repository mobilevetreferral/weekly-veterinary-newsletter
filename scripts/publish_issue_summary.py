#!/usr/bin/env python3
"""Print the Markdown review summary for a generated newsletter issue."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from newsletter_workflow import BASE_DIR, OUTPUT_DIR, build_issue_slug, today_in_config_timezone


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a generated review-summary.md file.")
    parser.add_argument("--issue-date", help="Issue date in YYYY-MM-DD format. Defaults to today in the configured timezone.")
    return parser.parse_args()


def resolve_issue_date(raw: str | None) -> dt.date:
    if raw:
        return dt.date.fromisoformat(raw)
    return today_in_config_timezone()


def main() -> int:
    args = parse_args()
    issue_date = resolve_issue_date(args.issue_date)
    summary_path = OUTPUT_DIR / build_issue_slug(issue_date) / "review-summary.md"

    if not summary_path.exists():
        print(f"Review summary not found: {summary_path}", file=sys.stderr)
        return 1

    sys.stdout.write(summary_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
