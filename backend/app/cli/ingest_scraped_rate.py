from __future__ import annotations

# ingest_scraped_rate.py — CLI tool to take scraped JSON and upsert it into SQLite
# Useful for debugging: you can pipe Firecrawl output straight into this script.

import argparse
import json
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    # When running directly, make sure `import backend...` works.
    sys.path.insert(0, str(_repo_root))

from backend.app.services.scraped_rate_ingestion import ScrapedRate, upsert_scraped_rate  # noqa: E402


def main() -> None:
    # Read JSON from a string, stdin, or file, then upsert each offer into SQLite.
    # Returns: nothing (prints a JSON array of upsert results).
    parser = argparse.ArgumentParser(description="Upsert a scraped rate JSON into SQLite.")
    parser.add_argument(
        "--json",
        required=True,
        help="JSON string, '-' to read from stdin, or @path/to/file.json",
    )
    parser.add_argument("--source-url", required=True, help="Source URL where this rate was scraped from")
    parser.add_argument("--verified-at", default=None, help="ISO timestamp for Last Checked (default: now)")
    parser.add_argument("--category", default="cash_isa_easy_access")
    parser.add_argument("--term-months", type=int, default=-1)
    parser.add_argument("--isa-subtype", default="easy_access", help="Offer ISA subtype (ignored for fixed_savings).")
    args = parser.parse_args()

    # Use one consistent verified_at for the whole batch unless user provided one.
    verified_at = args.verified_at
    if verified_at is None:
        # Import here to avoid making _now_iso_z part of the public module API.
        from backend.app.services.scraped_rate_ingestion import _now_iso_z  # type: ignore

        verified_at = _now_iso_z()

    raw = args.json
    if raw == "-":
        # Read the full JSON text from stdin (works well with PowerShell piping).
        raw = sys.stdin.read()
    elif raw.startswith("@"):
        # `@file.json` means “read JSON from this file path”.
        raw = Path(raw[1:]).read_text(encoding="utf-8")

    payload = json.loads(raw)

    # Accept a few common shapes:
    # - {"offers":[...]} wrapper
    # - a raw list [...]
    # - a single object {...}
    offers: list[dict] = []
    if isinstance(payload, dict) and "offers" in payload and isinstance(payload["offers"], list):
        offers = payload["offers"]
    elif isinstance(payload, list):
        offers = payload
    elif isinstance(payload, dict):
        offers = [payload]
    else:
        raise SystemExit("Unsupported JSON format. Expected object, list, or {offers:[...]} wrapper.")

    results = []
    for item in offers:
        # Convert the JSON dict into our typed ScrapedRate dataclass.
        scraped = ScrapedRate(
            bank_name=str(item["bank_name"]),
            product_name=str(item["product_name"]) if item.get("product_name") else None,
            interest_rate=str(item["interest_rate"]),
            aer_percent=float(item["aer_percent"]) if item.get("aer_percent") is not None else None,
            provider_product_url=str(item["provider_product_url"]) if item.get("provider_product_url") else None,
        )
        results.append(
            # Upsert writes into provider/product/offer/snapshot/source tables.
            upsert_scraped_rate(
                scraped=scraped,
                source_url=args.source_url,
                verified_at=verified_at,
                category=args.category,
                term_months=args.term_months,
                isa_subtype=args.isa_subtype,
            )
        )

    json.dump(results, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

