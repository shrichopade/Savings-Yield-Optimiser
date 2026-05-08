from __future__ import annotations

# firecrawl_moneysupermarket.py — CLI tool to scrape MoneySuperMarket via Firecrawl
# Usage: python -m backend.app.cli.firecrawl_moneysupermarket --kind cash_isa_easy_access --url <page>

import argparse
import json
from pathlib import Path
import sys

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    # When running directly, ensure Python can import the `backend` package.
    sys.path.insert(0, str(_repo_root))

from backend.app.ingestion.firecrawl import FirecrawlClient, build_rates_list_schema  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402


def main() -> None:
    # Scrape a MoneySuperMarket page and print extracted offers as JSON.
    # Inputs: command-line args (url, limit, kind).
    # Returns: nothing (prints JSON).
    parser = argparse.ArgumentParser(description="MoneySuperMarket scraper via Firecrawl (top N offers).")
    parser.add_argument("--url", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--kind",
        choices=["cash_isa_easy_access", "cash_isa_fixed", "fixed_savings"],
        required=True,
        help="Extraction intent (guides prompt).",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.firecrawl_api_key:
        raise SystemExit("Missing FIRECRAWL_API_KEY (set it in .env or env var).")

    # Use a slightly different prompt depending on which table/category we are targeting.
    prompt_kind = {
        "cash_isa_easy_access": "cash ISA easy access",
        "cash_isa_fixed": "fixed-rate cash ISA",
        "fixed_savings": "fixed-rate savings bond",
    }[args.kind]

    client = FirecrawlClient(api_key=settings.firecrawl_api_key)
    extracted = client.scrape_json(
        url=args.url,
        json_schema=build_rates_list_schema(limit=args.limit),
        prompt=(
            f"From this MoneySuperMarket page, extract the first/top {args.limit} {prompt_kind} offers. "
            "For each offer return: bank_name, product_name, interest_rate (as shown), aer_percent (numeric), "
            "and provider_product_url if present."
        ),
    )

    json.dump(extracted, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

