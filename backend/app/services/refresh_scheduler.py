from __future__ import annotations

# refresh_scheduler.py — runs automated rate refresh jobs (scheduler + manual)
# This file scrapes target pages (via Firecrawl) and upserts results into SQLite.

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.ingestion.firecrawl import FirecrawlClient, build_rates_list_schema
from backend.app.services.scraped_rate_ingestion import ScrapedRate, upsert_scraped_rate
from backend.app.db.connection import connection
from backend.app.settings import Settings

logger = logging.getLogger(__name__)

_YEAR_TERM_RE = re.compile(r"(?P<n>\d+)[-_ ]year", re.IGNORECASE)

def _infer_term_months(scraped: ScrapedRate) -> int:
    # Try to guess the fixed term from the scraped text/URL (e.g., "1-year" → 12 months).
    # Inputs: a ScrapedRate (product name + provider URL).
    # Returns: term length in months, or -1 if unknown.
    text = f"{scraped.product_name or ''} {scraped.provider_product_url or ''}"
    m = _YEAR_TERM_RE.search(text)
    if m:
        return int(m.group("n")) * 12
    return -1


def _now_iso_z() -> str:
    # Create an ISO timestamp string in UTC (ending with "Z").
    # Returns: string timestamp for DB writes and logs.
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class RefreshTarget:
    url: str
    kind: str  # informational (e.g. cash_isa_easy_access, fixed_savings)
    category: str
    term_months: int
    isa_subtype: str
    limit: int = 10


def _route_offer_for_target(*, target: RefreshTarget, scraped: ScrapedRate) -> tuple[str, int, str] | None:
    """
    Return (category, term_months, isa_subtype) or None to skip ingestion.
    """
    if target.kind == "santander_savings_and_isas":
        name = (scraped.product_name or "").lower()

        # Skip non-MVP ISA products that don't belong in our tables yet.
        if "junior isa" in name or "inheritance isa" in name or "lifetime isa" in name:
            return None

        if "easy access isa" in name:
            return ("cash_isa_easy_access", -1, "easy_access")

        if "fixed rate isa" in name:
            term_months = -1
            if scraped.provider_product_url:
                m = _YEAR_TERM_RE.search(scraped.provider_product_url)
                if m:
                    term_months = int(m.group("n")) * 12
            return ("cash_isa_fixed", term_months, "fixed")

        return ("fixed_savings", -1, "fixed")

    term_months = target.term_months
    if target.category == "cash_isa_fixed" and term_months in (0, -1):
        term_months = _infer_term_months(scraped)

    return (target.category, term_months, target.isa_subtype)


def _default_targets() -> list[RefreshTarget]:
    # Default scrape targets for the MVP.
    # Returns: list of RefreshTarget objects the refresh job will iterate through.
    return [
        RefreshTarget(
            url="https://www.moneysupermarket.com/savings/cash-isas/",
            kind="cash_isa_easy_access",
            category="cash_isa_easy_access",
            term_months=-1,
            isa_subtype="easy_access",
            limit=10,
        ),
        RefreshTarget(
            url="https://www.moneysupermarket.com/savings/1-year-fixed-rate-bonds/",
            kind="fixed_savings_12m",
            category="fixed_savings",
            term_months=12,
            isa_subtype="fixed",
            limit=10,
        ),
        RefreshTarget(
            url="https://www.moneysavingexpert.com/savings/",
            kind="mse_savings",
            category="fixed_savings",
            term_months=-1,
            isa_subtype="fixed",
            limit=10,
        ),
        RefreshTarget(
            url="https://www.santander.co.uk/personal/savings-and-isas",
            kind="santander_savings_and_isas",
            # This page mixes ISAs + savings; in MVP we ingest into a single category with unknown term.
            # If you want strict separation later, split this into multiple targets with category-specific prompts.
            category="fixed_savings",
            term_months=-1,
            isa_subtype="fixed",
            limit=10,
        ),
        RefreshTarget(
            url="http://www.santander.co.uk/personal/savings-and-investments/isas/2-year-fixed-rate-isa",
            kind="santander_fixed_rate_isa_list",
            category="cash_isa_fixed",
            term_months=0,  # server-side meaning: all terms; ingestion will infer per-offer term
            isa_subtype="fixed",
            limit=10,
        ),
    ]


def load_targets(settings: Settings) -> list[RefreshTarget]:
    # Load scrape targets from REFRESH_TARGETS_JSON (if provided), otherwise use defaults.
    # Inputs: Settings (contains refresh_targets_json).
    # Returns: list of RefreshTarget objects.
    if not settings.refresh_targets_json:
        return _default_targets()

    try:
        raw = json.loads(settings.refresh_targets_json)
        if not isinstance(raw, list):
            raise ValueError("REFRESH_TARGETS_JSON must be a JSON array.")
        targets: list[RefreshTarget] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            targets.append(
                RefreshTarget(
                    url=str(item["url"]),
                    kind=str(item.get("kind", "custom")),
                    category=str(item["category"]),
                    term_months=int(item.get("term_months", -1)),
                    isa_subtype=str(item.get("isa_subtype", "")),
                    limit=int(item.get("limit", 10)),
                )
            )
        return targets
    except Exception:
        logger.exception("Failed to parse REFRESH_TARGETS_JSON; falling back to defaults.")
        return _default_targets()


def run_refresh_once(*, settings: Settings) -> None:
    # Run one full refresh cycle: scrape each target URL and upsert offers into SQLite.
    # Inputs: Settings (needs FIRECRAWL_API_KEY and db_path).
    # Returns: nothing (writes to SQLite and logs progress).
    if not settings.firecrawl_api_key:
        logger.warning("Refresh skipped: FIRECRAWL_API_KEY is not set.")
        return

    # Create a job id so we can track this refresh run in SQLite.
    job_run_id = uuid.uuid4().hex
    with connection(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO ingestion_job_run(job_run_id, job_type, status, started_at)
            VALUES (?, ?, ?, ?);
            """,
            (job_run_id, "scheduler", "running", _now_iso_z()),
        )

    targets = load_targets(settings)
    verified_at = _now_iso_z()
    logger.info("Refresh started at %s for %d targets", verified_at, len(targets))

    # Firecrawl client is the “web scraping” tool we use to pull structured JSON from a URL.
    client = FirecrawlClient(api_key=settings.firecrawl_api_key)

    try:
        for t in targets:
            try:
                # Ask Firecrawl to extract the top N offers from the page.
                logger.info("Scraping target kind=%s url=%s limit=%d", t.kind, t.url, t.limit)
                extracted = client.scrape_json(
                    url=t.url,
                    json_schema=build_rates_list_schema(limit=t.limit),
                    prompt=(
                        f"Extract the first/top {t.limit} offers from this page. "
                        "For each offer return: bank_name, product_name, interest_rate (as shown), "
                        "aer_percent (numeric), and provider_product_url if present."
                    ),
                )
                offers = extracted.get("offers") if isinstance(extracted, dict) else None
                if not isinstance(offers, list) or not offers:
                    logger.warning("No offers extracted for url=%s", t.url)
                    continue

                for idx, item in enumerate(offers, start=1):
                    try:
                        # Normalize raw JSON into our internal ScrapedRate shape.
                        scraped = ScrapedRate(
                            bank_name=str(item["bank_name"]),
                            product_name=str(item["product_name"]) if item.get("product_name") else None,
                            interest_rate=str(item["interest_rate"]),
                            aer_percent=float(item["aer_percent"])
                            if item.get("aer_percent") is not None
                            else None,
                            provider_product_url=str(item["provider_product_url"])
                            if item.get("provider_product_url")
                            else None,
                        )

                        routed = _route_offer_for_target(target=t, scraped=scraped)
                        if routed is None:
                            continue
                        category, term_months, isa_subtype = routed

                        # Upsert into SQLite (idempotent “update or insert” behavior).
                        res: dict[str, Any] = upsert_scraped_rate(
                            scraped=scraped,
                            source_url=t.url,
                            verified_at=verified_at,
                            category=category,
                            term_months=term_months,
                            isa_subtype=isa_subtype,
                        )

                        logger.info(
                            "Upserted [%s %d/%d] provider_id=%s offer_id=%s aer=%s",
                            t.kind,
                            idx,
                            len(offers),
                            res.get("provider_id"),
                            res.get("offer_id"),
                            res.get("aer_percent"),
                        )
                    except Exception:
                        # If one offer fails, keep going so the refresh still completes for other offers.
                        logger.exception("Failed to upsert offer idx=%d for url=%s", idx, t.url)
            except Exception:
                # If one target fails, keep going so other target pages still refresh.
                logger.exception("Failed refresh target kind=%s url=%s", t.kind, t.url)

        logger.info("Refresh finished at %s", _now_iso_z())
        with connection(settings.db_path) as conn:
            conn.execute(
                """
                UPDATE ingestion_job_run
                SET status=?, finished_at=?
                WHERE job_run_id=?;
                """,
                ("succeeded", _now_iso_z(), job_run_id),
            )
    except Exception as e:
        logger.exception("Refresh run failed job_run_id=%s", job_run_id)
        with connection(settings.db_path) as conn:
            conn.execute(
                """
                UPDATE ingestion_job_run
                SET status=?, finished_at=?, error=?
                WHERE job_run_id=?;
                """,
                ("failed", _now_iso_z(), str(e), job_run_id),
            )
        raise


def start_scheduler(*, settings: Settings) -> BackgroundScheduler | None:
    # Start an in-process background scheduler that runs refresh every N hours.
    # Inputs: Settings (controls if enabled + interval).
    # Returns: BackgroundScheduler instance, or None if disabled.
    if not settings.refresh_scheduler_enabled:
        logger.info("Refresh scheduler disabled (set REFRESH_SCHEDULER_ENABLED=1 to enable).")
        return None

    interval_h = max(1, int(settings.refresh_interval_hours))
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        run_refresh_once,
        "interval",
        hours=interval_h,
        kwargs={"settings": settings},
        id="refresh_rates",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60 * 30,
    )
    scheduler.start()

    logger.info("Refresh scheduler started (interval=%dh).", interval_h)
    return scheduler

