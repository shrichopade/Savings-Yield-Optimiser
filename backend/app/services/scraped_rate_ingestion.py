from __future__ import annotations

# scraped_rate_ingestion.py — takes scraped “offers” and writes them into SQLite
# The key idea is “upsert”: update existing records or create them if missing.

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.app.db.connection import connection
from backend.app.settings import get_settings


@dataclass(frozen=True)
class ScrapedRate:
    bank_name: str
    product_name: str | None
    interest_rate: str  # raw text, e.g. "4.51% Variable"
    aer_percent: float | None = None
    provider_product_url: str | None = None


def _now_iso_z() -> str:
    # Create an ISO timestamp in UTC for “when we checked this rate”.
    # Returns: string like 2026-01-01T12:34:56.789Z.
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


_PERCENT_RE = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*%")


def _extract_aer_percent(raw: str) -> float | None:
    """
    Best-effort extraction of the first percentage number from the scraped string.
    Examples:
      "4.51% Variable" -> 4.51
      "4.85% AER" -> 4.85
    """
    # We do this because scraped pages often give rate text like "4.85% AER" not a clean number.
    m = _PERCENT_RE.search(raw or "")
    if not m:
        return None
    try:
        return float(m.group("num"))
    except ValueError:
        return None


def _product_type_for_category(category: str) -> str:
    """
    Map offer category to the schema's product_type values.
    Schema comment expects: 'fixed_savings' | 'cash_isa'
    """
    # This keeps product_type consistent even though we have multiple ISA categories in the UI.
    if category == "fixed_savings":
        return "fixed_savings"
    if category.startswith("cash_isa"):
        return "cash_isa"
    # Default to a conservative bucket; callers should pass a supported category.
    return "cash_isa"


def _canonical_product_name(
    *,
    category: str,
    term_months: int,
    isa_subtype: str,
    scraped_product_name: str | None,
) -> str:
    """
    To avoid duplicates from fluctuating comparison-site labels, we derive a stable
    product name by category/subtype/term, falling back to scraped label only when
    it provides additional stable specificity.
    """
    # In plain English: we want a name that stays consistent across refresh runs,
    # so the same offer doesn’t get inserted as a “new” product every time.
    scraped_label = (scraped_product_name or "").strip()

    if category == "fixed_savings":
        # If we don't know the term, keep the scraped label to avoid collapsing different products.
        if int(term_months) <= 0 and scraped_label:
            return scraped_label
        return f"Fixed Savings ({int(term_months)}m)"

    if category == "cash_isa_easy_access":
        # Prefer scraped label when present (bank pages often have distinct ISA product names).
        return scraped_label or "Cash ISA - Easy Access"

    if category == "cash_isa_fixed":
        if scraped_label:
            return scraped_label
        return f"Cash ISA - Fixed ({int(term_months)}m)"

    if category == "cash_isa_notice":
        return "Cash ISA - Notice"

    # Last resort: use scraped label if present, otherwise generic.
    return scraped_label or "Cash ISA"


def upsert_scraped_rate(
    *,
    scraped: ScrapedRate,
    source_url: str,
    source_type: str = "comparison_site",
    verified_at: str | None = None,
    category: str = "cash_isa_easy_access",
    term_months: int = -1,
    isa_subtype: str = "easy_access",
) -> dict[str, Any]:
    """
    Upsert a minimal offer into SQLite:
      - provider.name = bank_name
      - product.name is derived canonically from category/term/subtype to avoid duplicates
      - product_offer.category/term_months/isa_subtype
      - offer_snapshot.verified_at = Last Checked
      - offer_snapshot.aer_percent parsed from interest_rate string when possible
      - source + snapshot_source linkage to persist Source URL(s)

    Returns identifiers for debugging/verification.
    """
    # Inputs:
    # - scraped: the offer we extracted from a web page
    # - source_url/source_type: where we got this information from
    # - verified_at: “when we checked it” (defaults to now)
    # - category/term_months/isa_subtype: which table the offer belongs to
    #
    # Returns:
    # - a dictionary of IDs (provider_id, offer_id, snapshot_id, etc.) useful for debugging.
    settings = get_settings()
    verified_at = verified_at or _now_iso_z()
    aer = scraped.aer_percent if scraped.aer_percent is not None else _extract_aer_percent(scraped.interest_rate)

    product_name = _canonical_product_name(
        category=category,
        term_months=term_months,
        isa_subtype=isa_subtype,
        scraped_product_name=scraped.product_name,
    )
    product_type = _product_type_for_category(category)

    with connection(settings.db_path) as conn:
        cur = conn.cursor()

        # Provider
        cur.execute(
            """
            INSERT INTO provider (name)
            VALUES (?)
            ON CONFLICT(name) DO UPDATE SET
              updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            RETURNING provider_id;
            """,
            (scraped.bank_name,),
        )
        provider_id = int(cur.fetchone()[0])

        # Product identity:
        # Use (provider_id + product_type + canonical product_name) so multiple products from the same bank
        # don't overwrite each other (e.g., Santander Regular Saver vs Edge Saver).
        cur.execute(
            """
            INSERT INTO product (provider_id, name, product_type)
            VALUES (?, ?, ?)
            ON CONFLICT(provider_id, name, product_type) DO UPDATE SET
              updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            RETURNING product_id;
            """,
            (provider_id, product_name, product_type),
        )
        product_id = int(cur.fetchone()[0])

        # Offer (stable identity)
        cur.execute(
            """
            INSERT INTO product_offer (product_id, category, term_months, isa_subtype, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(product_id, category, term_months, isa_subtype) DO UPDATE SET
              status=excluded.status,
              updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            RETURNING offer_id;
            """,
            (product_id, category, int(term_months), isa_subtype or "", "active"),
        )
        offer_id = int(cur.fetchone()[0])

        # Snapshot (Last Checked)
        # We always insert a new snapshot for the new verified_at to ensure "last_checked" updates
        # even if the rate is unchanged. If the unique constraint (offer_id, verified_at) collides,
        # we overwrite the same timestamp's snapshot values.
        cur.execute(
            """
            INSERT INTO offer_snapshot (offer_id, verified_at, aer_percent, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(offer_id, verified_at) DO UPDATE SET
              aer_percent=excluded.aer_percent,
              status=excluded.status
            RETURNING snapshot_id;
            """,
            (offer_id, verified_at, aer, "active"),
        )
        snapshot_id = int(cur.fetchone()[0])

        # Source URL
        cur.execute(
            """
            INSERT INTO source (url, source_type, retrieved_at)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
              source_type=excluded.source_type,
              retrieved_at=excluded.retrieved_at
            RETURNING source_id;
            """,
            (source_url, source_type, verified_at),
        )
        source_id = int(cur.fetchone()[0])

        cur.execute(
            """
            INSERT OR IGNORE INTO snapshot_source (snapshot_id, source_id)
            VALUES (?, ?);
            """,
            (snapshot_id, source_id),
        )

        # Point offer to latest snapshot.
        cur.execute(
            "UPDATE product_offer SET current_snapshot_id=? WHERE offer_id=?;",
            (snapshot_id, offer_id),
        )

        provider_source_id: int | None = None
        if scraped.provider_product_url:
            # Store the provider’s official product page as an additional source (when available).
            cur.execute(
                """
                INSERT INTO source (url, source_type, retrieved_at)
                VALUES (?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                  source_type=excluded.source_type,
                  retrieved_at=excluded.retrieved_at
                RETURNING source_id;
                """,
                (scraped.provider_product_url, "provider_page", verified_at),
            )
            provider_source_id = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT OR IGNORE INTO snapshot_source (snapshot_id, source_id)
                VALUES (?, ?);
                """,
                (snapshot_id, provider_source_id),
            )

    return {
        "provider_id": provider_id,
        "product_id": product_id,
        "offer_id": offer_id,
        "snapshot_id": snapshot_id,
        "verified_at": verified_at,
        "aer_percent": aer,
        "source_id": source_id,
        "provider_source_id": provider_source_id,
    }

