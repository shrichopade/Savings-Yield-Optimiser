from __future__ import annotations

# offers.py — SQL queries that power the “tables” shown in the frontend
# This file reads from SQLite and returns plain dictionaries for API responses.

from dataclasses import dataclass
from typing import Any, Iterable

import sqlite3


@dataclass(frozen=True)
class OfferQuery:
    category: str
    term_months: int | None
    deposit_gbp: int | None
    exclude_restricted: bool


def _to_bool(value: Any) -> bool | None:
    # Convert SQLite-style 0/1/NULL values into Python booleans.
    # Inputs: any value (often int-like or None).
    # Returns: True/False/None.
    if value is None:
        return None
    return bool(int(value))


def _badges_from_row(row: sqlite3.Row) -> list[str]:
    # Build a simple list of “badges” the UI can display (e.g., restricted/bonus/conditional).
    # Inputs: one SQLite row representing an offer.
    # Returns: list of short badge identifiers.
    badges: list[str] = []
    if row["is_conditional_rate"] == 1:
        badges.append("conditional_rate")
    if row["bonus_percent"] is not None:
        badges.append("bonus")
    if row["withdrawals_allowed"] == 0:
        badges.append("no_withdrawals")
    if row["new_customer_only"] == 1:
        badges.append("new_customer_only")
    if row["new_money_required"] == 1:
        badges.append("new_money_required")
    if row["transfer_in_supported"] == 1:
        badges.append("transfer_in")
    if row["partial_transfers_allowed"] == 1:
        badges.append("partial_transfer")
    if row["is_flexible_isa"] == 1:
        badges.append("flexible_isa")
    return badges


def fetch_table_rows(conn: sqlite3.Connection, q: OfferQuery) -> list[dict[str, Any]]:
    # Fetch rows for a specific table (category + optional term) with optional filters.
    # Inputs:
    # - conn: open SQLite connection
    # - q: OfferQuery containing table scope + filters
    # Returns: list of dictionaries (each dictionary is one table row for the frontend).
    #
    # Important: we join via product_offer.current_snapshot_id so we only return “current” snapshots.
    params: dict[str, Any] = {"category": q.category}

    where: list[str] = [
        "po.category = :category",
        "po.status = 'active'",
        "os.status = 'active'",
    ]

    if q.category in ("fixed_savings", "cash_isa_fixed"):
        if q.term_months is not None:
            params["term_months"] = q.term_months
            where.append("po.term_months = :term_months")

    if q.deposit_gbp is not None:
        params["deposit_gbp"] = q.deposit_gbp
        where.append("(os.min_opening_deposit_gbp IS NULL OR os.min_opening_deposit_gbp <= :deposit_gbp)")
        where.append("(os.max_balance_gbp IS NULL OR os.max_balance_gbp >= :deposit_gbp)")

    if q.exclude_restricted:
        # Minimal definition of “restricted” for MVP:
        # if snapshot explicitly flags new_customer_only/new_money_required.
        where.append("(IFNULL(os.new_customer_only, 0) = 0)")
        where.append("(IFNULL(os.new_money_required, 0) = 0)")

    where_sql = " AND ".join(where)

    sql = f"""
    SELECT
      po.offer_id,
      pvd.name AS provider_name,
      pr.name AS product_name,
      po.category,
      CASE WHEN po.term_months = -1 THEN NULL ELSE po.term_months END AS term_months,

      os.aer_percent,
      os.payout_frequency,
      os.min_opening_deposit_gbp,
      os.max_balance_gbp,
      os.withdrawals_allowed,
      os.early_closure_allowed,
      os.new_customer_only,
      os.new_money_required,
      os.transfer_in_supported,
      os.partial_transfers_allowed,
      os.is_flexible_isa,
      os.is_conditional_rate,
      os.bonus_percent,
      os.verified_at,

      (
        SELECT s.url
        FROM snapshot_source ss
        JOIN source s ON s.source_id = ss.source_id
        WHERE ss.snapshot_id = os.snapshot_id
        ORDER BY s.source_id ASC
        LIMIT 1
      ) AS source_url
    FROM product_offer po
    JOIN product pr ON pr.product_id = po.product_id
    JOIN provider pvd ON pvd.provider_id = pr.provider_id
    JOIN offer_snapshot os ON os.snapshot_id = po.current_snapshot_id
    WHERE {where_sql}
    ORDER BY
      os.aer_percent IS NULL ASC,
      os.aer_percent DESC,
      (IFNULL(os.new_customer_only, 0) + IFNULL(os.new_money_required, 0)) ASC,
      pvd.name ASC,
      pr.name ASC
    LIMIT 200;
    """

    cur = conn.execute(sql, params)
    rows = cur.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        # Convert from SQLite row objects into plain Python types for FastAPI/Pydantic.
        result.append(
            {
                "offer_id": int(row["offer_id"]),
                "provider_name": row["provider_name"],
                "product_name": row["product_name"],
                "category": row["category"],
                "term_months": row["term_months"],
                "aer_percent": row["aer_percent"],
                "payout_frequency": row["payout_frequency"],
                "min_opening_deposit_gbp": row["min_opening_deposit_gbp"],
                "max_balance_gbp": row["max_balance_gbp"],
                "withdrawals_allowed": _to_bool(row["withdrawals_allowed"]),
                "early_closure_allowed": _to_bool(row["early_closure_allowed"]),
                "new_customer_only": _to_bool(row["new_customer_only"]),
                "new_money_required": _to_bool(row["new_money_required"]),
                "transfer_in_supported": _to_bool(row["transfer_in_supported"]),
                "partial_transfers_allowed": _to_bool(row["partial_transfers_allowed"]),
                "is_flexible_isa": _to_bool(row["is_flexible_isa"]),
                "verified_at": row["verified_at"],
                "source_url": row["source_url"],
                "badges": _badges_from_row(row),
            }
        )

    return result

