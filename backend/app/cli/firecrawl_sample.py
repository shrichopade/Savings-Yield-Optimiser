from __future__ import annotations

# firecrawl_sample.py — CLI tool to test Firecrawl extraction on a single URL
# Usage: python -m backend.app.cli.firecrawl_sample --url <page> --limit 5

import argparse
import json
from pathlib import Path
import sys

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    # When running this file directly, add the repo root so `import backend...` works.
    sys.path.insert(0, str(_repo_root))

from backend.app.ingestion.firecrawl import FirecrawlClient, build_rates_list_schema
from backend.app.settings import get_settings


def main() -> None:
    # Parse CLI args, call Firecrawl, then print the extracted JSON to stdout.
    # Returns: nothing (prints JSON).
    parser = argparse.ArgumentParser(description="Firecrawl sample scraper (bank name + rate).")
    parser.add_argument(
        "--url",
        required=True,
        help="A UK savings/ISA comparison page or provider page URL to scrape.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many top offers to extract (best effort).",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.firecrawl_api_key:
        raise SystemExit(
            "Missing FIRECRAWL_API_KEY. Set it in your environment before running this command."
        )

    # Create a Firecrawl client and ask it to extract a small list of offers.
    client = FirecrawlClient(api_key=settings.firecrawl_api_key)
    extracted = client.scrape_json(
        url=args.url,
        json_schema=build_rates_list_schema(limit=args.limit),
        prompt=(
            f"Extract the first/top {args.limit} savings/ISA products from this page. "
            "For each offer, return bank/provider name, product name/label if shown, "
            "the displayed interest rate/AER, and the provider's official product URL if present."
        ),
    )

    json.dump(extracted, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

