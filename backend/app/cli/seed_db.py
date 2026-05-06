from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.db.connection import connection
from backend.app.settings import get_settings


def _bool_to_int(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _upsert_provider(cur, provider: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO provider (name, provider_type, fscs_protected)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
          provider_type=excluded.provider_type,
          fscs_protected=excluded.fscs_protected,
          updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
        RETURNING provider_id;
        """,
        (
            provider["name"],
            provider.get("provider_type"),
            _bool_to_int(provider.get("fscs_protected")),
        ),
    )
    return int(cur.fetchone()[0])


def _upsert_product(cur, provider_id: int, product: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO product (provider_id, name, product_type)
        VALUES (?, ?, ?)
        ON CONFLICT(provider_id, name, product_type) DO UPDATE SET
          updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
        RETURNING product_id;
        """,
        (provider_id, product["name"], product["product_type"]),
    )
    return int(cur.fetchone()[0])


def _upsert_offer(cur, product_id: int, offer: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO product_offer (product_id, category, term_months, isa_subtype, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(product_id, category, term_months, isa_subtype) DO UPDATE SET
          status=excluded.status,
          updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
        RETURNING offer_id;
        """,
        (
            product_id,
            offer["category"],
            int(offer.get("term_months", -1)),
            offer.get("isa_subtype", "") or "",
            offer.get("status", "active"),
        ),
    )
    return int(cur.fetchone()[0])


def _insert_snapshot(cur, offer_id: int, snapshot: dict[str, Any]) -> int:
    # Keep it minimal: insert only known keys; unknown keys are ignored.
    columns: list[str] = ["offer_id", "verified_at"]
    values: list[Any] = [offer_id, snapshot["verified_at"]]

    def add(col: str, val: Any) -> None:
        columns.append(col)
        values.append(val)

    add("aer_percent", snapshot.get("aer_percent"))
    add("gross_percent", snapshot.get("gross_percent"))
    add("rate_type", snapshot.get("rate_type"))
    add("is_conditional_rate", _bool_to_int(snapshot.get("is_conditional_rate")))

    add("bonus_percent", snapshot.get("bonus_percent"))
    add("bonus_end_date", snapshot.get("bonus_end_date"))
    add("reversion_aer_percent", snapshot.get("reversion_aer_percent"))

    add("payout_frequency", snapshot.get("payout_frequency"))

    add("min_opening_deposit_gbp", snapshot.get("min_opening_deposit_gbp"))
    add("min_ongoing_balance_gbp", snapshot.get("min_ongoing_balance_gbp"))
    add("max_balance_gbp", snapshot.get("max_balance_gbp"))
    add("funding_window_days", snapshot.get("funding_window_days"))

    add("withdrawals_allowed", _bool_to_int(snapshot.get("withdrawals_allowed")))
    add("notice_days", snapshot.get("notice_days"))
    add("early_closure_allowed", _bool_to_int(snapshot.get("early_closure_allowed")))
    add("penalty_model_text", snapshot.get("penalty_model_text"))

    add(
        "deposits_during_term_allowed",
        _bool_to_int(snapshot.get("deposits_during_term_allowed")),
    )
    add("maturity_handling_text", snapshot.get("maturity_handling_text"))
    add("grace_period_days", snapshot.get("grace_period_days"))

    add("is_flexible_isa", _bool_to_int(snapshot.get("is_flexible_isa")))
    add("transfer_in_supported", _bool_to_int(snapshot.get("transfer_in_supported")))
    add(
        "partial_transfers_allowed",
        _bool_to_int(snapshot.get("partial_transfers_allowed")),
    )
    add("transfer_out_restrictions_text", snapshot.get("transfer_out_restrictions_text"))

    add("uk_residency_required", _bool_to_int(snapshot.get("uk_residency_required")))
    add("min_age_years", snapshot.get("min_age_years"))
    add("max_age_years", snapshot.get("max_age_years"))
    add("new_customer_only", _bool_to_int(snapshot.get("new_customer_only")))
    add("new_money_required", _bool_to_int(snapshot.get("new_money_required")))
    add("eligibility_notes", snapshot.get("eligibility_notes"))

    add("open_method", snapshot.get("open_method"))
    add("managed_via", snapshot.get("managed_via"))

    placeholders = ",".join(["?"] * len(columns))
    cols_sql = ",".join(columns)

    cur.execute(
        f"""
        INSERT INTO offer_snapshot ({cols_sql})
        VALUES ({placeholders})
        ON CONFLICT(offer_id, verified_at) DO UPDATE SET
          aer_percent=excluded.aer_percent,
          gross_percent=excluded.gross_percent,
          rate_type=excluded.rate_type,
          is_conditional_rate=excluded.is_conditional_rate,
          bonus_percent=excluded.bonus_percent,
          bonus_end_date=excluded.bonus_end_date,
          reversion_aer_percent=excluded.reversion_aer_percent,
          payout_frequency=excluded.payout_frequency,
          min_opening_deposit_gbp=excluded.min_opening_deposit_gbp,
          min_ongoing_balance_gbp=excluded.min_ongoing_balance_gbp,
          max_balance_gbp=excluded.max_balance_gbp,
          funding_window_days=excluded.funding_window_days,
          withdrawals_allowed=excluded.withdrawals_allowed,
          notice_days=excluded.notice_days,
          early_closure_allowed=excluded.early_closure_allowed,
          penalty_model_text=excluded.penalty_model_text,
          deposits_during_term_allowed=excluded.deposits_during_term_allowed,
          maturity_handling_text=excluded.maturity_handling_text,
          grace_period_days=excluded.grace_period_days,
          is_flexible_isa=excluded.is_flexible_isa,
          transfer_in_supported=excluded.transfer_in_supported,
          partial_transfers_allowed=excluded.partial_transfers_allowed,
          transfer_out_restrictions_text=excluded.transfer_out_restrictions_text,
          uk_residency_required=excluded.uk_residency_required,
          min_age_years=excluded.min_age_years,
          max_age_years=excluded.max_age_years,
          new_customer_only=excluded.new_customer_only,
          new_money_required=excluded.new_money_required,
          eligibility_notes=excluded.eligibility_notes,
          open_method=excluded.open_method,
          managed_via=excluded.managed_via
        RETURNING snapshot_id;
        """,
        values,
    )
    return int(cur.fetchone()[0])


def _upsert_source(cur, source: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO source (url, source_type)
        VALUES (?, ?)
        ON CONFLICT(url) DO UPDATE SET
          source_type=excluded.source_type
        RETURNING source_id;
        """,
        (source["url"], source.get("source_type", "provider_page")),
    )
    return int(cur.fetchone()[0])


def _link_snapshot_source(cur, snapshot_id: int, source_id: int) -> None:
    cur.execute(
        """
        INSERT OR IGNORE INTO snapshot_source (snapshot_id, source_id)
        VALUES (?, ?);
        """,
        (snapshot_id, source_id),
    )


def seed_from_file(seed_path: Path) -> None:
    settings = get_settings()
    payload = json.loads(seed_path.read_text(encoding="utf-8"))

    providers = payload.get("providers", [])
    if not isinstance(providers, list) or not providers:
        raise SystemExit("Seed file must include non-empty top-level 'providers' array.")

    with connection(settings.db_path) as conn:
        cur = conn.cursor()

        for provider in providers:
            provider_id = _upsert_provider(cur, provider)

            for product in provider.get("products", []):
                product_id = _upsert_product(cur, provider_id, product)

                for offer in product.get("offers", []):
                    offer_id = _upsert_offer(cur, product_id, offer)

                    snapshot = offer.get("snapshot")
                    if not isinstance(snapshot, dict):
                        raise SystemExit(f"Offer missing snapshot: {offer}")

                    snapshot_id = _insert_snapshot(cur, offer_id, snapshot)

                    for src in offer.get("sources", []):
                        source_id = _upsert_source(cur, src)
                        _link_snapshot_source(cur, snapshot_id, source_id)

                    cur.execute(
                        "UPDATE product_offer SET current_snapshot_id=? WHERE offer_id=?;",
                        (snapshot_id, offer_id),
                    )

    print(f"Seeded DB from: {seed_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    default_seed = repo_root / "backend" / "seed" / "sample-uk-rates.json"
    seed_from_file(default_seed)


if __name__ == "__main__":
    main()

