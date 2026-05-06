from __future__ import annotations

from pydantic import BaseModel, Field


class TableRow(BaseModel):
    offer_id: int
    provider_name: str
    product_name: str
    category: str
    term_months: int | None = None

    aer_percent: float | None = None
    payout_frequency: str | None = None

    min_opening_deposit_gbp: int | None = None
    max_balance_gbp: int | None = None

    withdrawals_allowed: bool | None = None
    early_closure_allowed: bool | None = None

    new_customer_only: bool | None = None
    new_money_required: bool | None = None

    transfer_in_supported: bool | None = None
    partial_transfers_allowed: bool | None = None
    is_flexible_isa: bool | None = None

    verified_at: str = Field(description="Last checked timestamp (ISO).")
    source_url: str | None = None

    badges: list[str] = Field(default_factory=list)


class TableResponse(BaseModel):
    items: list[TableRow]

