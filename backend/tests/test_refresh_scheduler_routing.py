"""
test_refresh_scheduler_routing.py — small regression tests for refresh routing logic

These tests protect the “category/term inference” rules so a future refactor does not
silently break which table an offer appears in.
"""

from backend.app.services.refresh_scheduler import RefreshTarget, _infer_term_months, _route_offer_for_target
from backend.app.services.scraped_rate_ingestion import ScrapedRate


def test_infer_term_months_from_url_year() -> None:
    # If a provider URL contains "1-year", we should infer 12 months.
    scraped = ScrapedRate(
        bank_name="Santander",
        product_name="Fixed Rate Cash ISA",
        interest_rate="4.10%",
        aer_percent=4.10,
        provider_product_url="https://www.santander.co.uk/savings/1-year-fixed-rate-isa",
    )
    assert _infer_term_months(scraped) == 12


def test_route_santander_mixed_page_fixed_rate_isa_infers_term() -> None:
    # Santander’s mixed page should route “Fixed Rate ISA” offers into the fixed ISA category.
    target = RefreshTarget(
        url="https://www.santander.co.uk/personal/savings-and-isas",
        kind="santander_savings_and_isas",
        category="fixed_savings",
        term_months=-1,
        isa_subtype="fixed",
        limit=10,
    )
    scraped = ScrapedRate(
        bank_name="Santander",
        product_name="2 Year Fixed Rate ISA",
        interest_rate="4.00%",
        aer_percent=4.0,
        provider_product_url="https://www.santander.co.uk/isas/2-year-fixed-rate-isa",
    )
    assert _route_offer_for_target(target=target, scraped=scraped) == ("cash_isa_fixed", 24, "fixed")


def test_route_santander_mixed_page_easy_access_isa() -> None:
    # Santander’s mixed page should route “Easy Access ISA” offers into the easy-access ISA category.
    target = RefreshTarget(
        url="https://www.santander.co.uk/personal/savings-and-isas",
        kind="santander_savings_and_isas",
        category="fixed_savings",
        term_months=-1,
        isa_subtype="fixed",
        limit=10,
    )
    scraped = ScrapedRate(
        bank_name="Santander",
        product_name="Easy Access ISA",
        interest_rate="3.50%",
        aer_percent=3.5,
        provider_product_url="https://www.santander.co.uk/isas/easy-access-isa",
    )
    assert _route_offer_for_target(target=target, scraped=scraped) == ("cash_isa_easy_access", -1, "easy_access")


def test_route_santander_mixed_page_skips_junior_isa() -> None:
    # We intentionally skip Junior ISA products in MVP tables.
    target = RefreshTarget(
        url="https://www.santander.co.uk/personal/savings-and-isas",
        kind="santander_savings_and_isas",
        category="fixed_savings",
        term_months=-1,
        isa_subtype="fixed",
        limit=10,
    )
    scraped = ScrapedRate(
        bank_name="Santander",
        product_name="Junior ISA",
        interest_rate="4.50%",
        aer_percent=4.5,
        provider_product_url="https://www.santander.co.uk/isas/junior-isa",
    )
    assert _route_offer_for_target(target=target, scraped=scraped) is None


def test_route_non_santander_cash_isa_fixed_infers_term_when_unknown() -> None:
    # For generic fixed ISA targets where term_months is unknown, infer from product name/URL.
    target = RefreshTarget(
        url="https://example.com/isas/fixed",
        kind="custom_cash_isa_fixed",
        category="cash_isa_fixed",
        term_months=0,
        isa_subtype="fixed",
        limit=10,
    )
    scraped = ScrapedRate(
        bank_name="Example Bank",
        product_name="1 year fixed rate cash ISA",
        interest_rate="4.20%",
        aer_percent=4.2,
        provider_product_url="https://example.com/isas/1-year-fixed-rate-cash-isa",
    )
    assert _route_offer_for_target(target=target, scraped=scraped) == ("cash_isa_fixed", 12, "fixed")

