from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.app.db.connection import connection
from backend.app.repositories.offers import OfferQuery, fetch_table_rows
from backend.app.schemas.api import TableResponse, TableRow
from backend.app.settings import Settings, get_settings

router = APIRouter(prefix="/tables", tags=["tables"])


def _get_settings() -> Settings:
    return get_settings()


@router.get("/fixed-savings", response_model=TableResponse)
def fixed_savings_table(
    term_months: int = Query(..., ge=1, le=120),
    deposit_gbp: int | None = Query(None, ge=0),
    exclude_restricted: bool = Query(False),
    settings: Settings = Depends(_get_settings),
) -> TableResponse:
    q = OfferQuery(
        category="fixed_savings",
        term_months=term_months,
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
    term_months: int = Query(..., ge=1, le=120),
    deposit_gbp: int | None = Query(None, ge=0),
    exclude_restricted: bool = Query(False),
    settings: Settings = Depends(_get_settings),
) -> TableResponse:
    q = OfferQuery(
        category="cash_isa_fixed",
        term_months=term_months,
        deposit_gbp=deposit_gbp,
        exclude_restricted=exclude_restricted,
    )
    with connection(settings.db_path) as conn:
        items = [TableRow.model_validate(r) for r in fetch_table_rows(conn, q)]
    return TableResponse(items=items)

