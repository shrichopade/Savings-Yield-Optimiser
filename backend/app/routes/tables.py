from __future__ import annotations

# tables.py — public API endpoints that return “table rows” for the frontend
# Each endpoint reads from SQLite and returns a list of ranked offers.

from fastapi import APIRouter, Depends, Query

from backend.app.db.connection import connection
from backend.app.repositories.offers import OfferQuery, fetch_table_rows
from backend.app.schemas.api import TableResponse, TableRow
from backend.app.settings import Settings, get_settings

router = APIRouter(prefix="/tables", tags=["tables"])


def _get_settings() -> Settings:
    # Small wrapper so FastAPI can inject Settings into endpoints.
    # Returns: the current Settings loaded from environment variables.
    return get_settings()


@router.get("/fixed-savings", response_model=TableResponse)
def fixed_savings_table(
    term_months: int = Query(
        0,
        ge=0,
        le=120,
        description="Use 0 for all terms, otherwise a specific term in months.",
    ),
    deposit_gbp: int | None = Query(None, ge=0),
    exclude_restricted: bool = Query(False),
    settings: Settings = Depends(_get_settings),
) -> TableResponse:
    # Return fixed savings offers for a term bucket.
    # Inputs:
    # - term_months: 0 = all terms, otherwise a specific fixed term in months
    # - deposit_gbp: optional deposit amount to filter by min/max
    # - exclude_restricted: if true, hide “restricted” deals (e.g., new customers only)
    # Returns: TableResponse(items=[...]) for the frontend table.
    q = OfferQuery(
        category="fixed_savings",
        term_months=None if term_months == 0 else term_months,
        deposit_gbp=deposit_gbp,
        exclude_restricted=exclude_restricted,
    )
    with connection(settings.db_path) as conn:
        items = [TableRow.model_validate(r) for r in fetch_table_rows(conn, q)]
    return TableResponse(items=items)


@router.get("/cash-isa/easy-access", response_model=TableResponse)
def cash_isa_easy_access_table(
    deposit_gbp: int | None = Query(None, ge=0),
    exclude_restricted: bool = Query(False),
    settings: Settings = Depends(_get_settings),
) -> TableResponse:
    # Return easy-access Cash ISA offers (no term selector for this table).
    # Inputs: deposit/eligibility filters.
    # Returns: TableResponse(items=[...]).
    q = OfferQuery(
        category="cash_isa_easy_access",
        term_months=None,
        deposit_gbp=deposit_gbp,
        exclude_restricted=exclude_restricted,
    )
    with connection(settings.db_path) as conn:
        items = [TableRow.model_validate(r) for r in fetch_table_rows(conn, q)]
    return TableResponse(items=items)


@router.get("/cash-isa/fixed", response_model=TableResponse)
def cash_isa_fixed_table(
    term_months: int = Query(
        0,
        ge=0,
        le=120,
        description="Use 0 for all terms, otherwise a specific term in months.",
    ),
    deposit_gbp: int | None = Query(None, ge=0),
    exclude_restricted: bool = Query(False),
    settings: Settings = Depends(_get_settings),
) -> TableResponse:
    # Return fixed-term Cash ISA offers for a term bucket (or all terms).
    # Inputs:
    # - term_months: 0 = all terms, otherwise a specific term in months
    # - deposit_gbp / exclude_restricted: same meaning as other tables
    # Returns: TableResponse(items=[...]).
    q = OfferQuery(
        category="cash_isa_fixed",
        term_months=None if term_months == 0 else term_months,
        deposit_gbp=deposit_gbp,
        exclude_restricted=exclude_restricted,
    )
    with connection(settings.db_path) as conn:
        items = [TableRow.model_validate(r) for r in fetch_table_rows(conn, q)]
    return TableResponse(items=items)

