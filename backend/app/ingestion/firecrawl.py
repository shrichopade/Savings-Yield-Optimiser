from __future__ import annotations

# firecrawl.py — a small client wrapper around the Firecrawl API
# We use Firecrawl to scrape a web page and return structured JSON based on a schema.

import json
from dataclasses import dataclass
from typing import Any

import requests


class FirecrawlError(RuntimeError):
    # Raised when Firecrawl returns an error or an unexpected response shape.
    pass


@dataclass(frozen=True)
class FirecrawlClient:
    api_key: str
    base_url: str = "https://api.firecrawl.dev/v1"
    timeout_s: float = 60.0

    def scrape_json(self, *, url: str, json_schema: dict[str, Any], prompt: str | None = None) -> dict[str, Any]:
        """
        Scrape a URL and ask Firecrawl to extract JSON that conforms to json_schema.
        Returns the extracted JSON object (as a dict).
        """
        # Build the request payload Firecrawl expects.
        payload: dict[str, Any] = {
            "url": url,
            "formats": ["json"],
            "jsonOptions": {
                "schema": json_schema,
            },
        }
        if prompt:
            # The prompt helps Firecrawl understand what fields we want from the page.
            payload["jsonOptions"]["prompt"] = prompt

        # Call Firecrawl over HTTPS.
        resp = requests.post(
            f"{self.base_url}/scrape",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=self.timeout_s,
        )

        if resp.status_code >= 400:
            raise FirecrawlError(f"Firecrawl error {resp.status_code}: {resp.text}")

        # Parse and validate the response structure.
        body = resp.json()
        if not body.get("success"):
            raise FirecrawlError(f"Firecrawl unsuccessful response: {body}")

        data = body.get("data") or {}
        extracted = data.get("json")
        if extracted is None:
            raise FirecrawlError(f"Firecrawl response missing data.json: {body}")
        if not isinstance(extracted, dict):
            raise FirecrawlError(f"Expected data.json to be an object, got: {type(extracted)}")
        return extracted


def build_sample_rate_schema() -> dict[str, Any]:
    """
    Minimal JSON schema for a single savings/ISA rate row.
    """
    # This schema tells Firecrawl what keys we want back in the extracted JSON.
    return {
        "type": "object",
        "properties": {
            "bank_name": {"type": "string"},
            "product_name": {
                "type": "string",
                "description": "Product name/label as displayed (if available).",
            },
            "interest_rate": {
                "type": "string",
                "description": "Interest rate/AER as displayed on the page, e.g. '4.85% AER' or '4.85%'",
            },
            "aer_percent": {
                "type": "number",
                "description": "AER as a numeric percentage (e.g., 4.51). Prefer this if available.",
            },
            "provider_product_url": {
                "type": "string",
                "description": "Provider's official product page URL if present on the page.",
            },
        },
        "required": ["bank_name", "interest_rate"],
        "additionalProperties": True,
    }


def build_rates_list_schema(*, limit: int = 5) -> dict[str, Any]:
    """
    JSON schema for extracting a small list of offer rows from a comparison page.
    """
    # We wrap offers in {"offers":[...]} so the response has a predictable top-level shape.
    return {
        "type": "object",
        "properties": {
            "offers": {
                "type": "array",
                "description": f"Top {limit} offers from the page (best effort).",
                "maxItems": int(limit),
                "items": build_sample_rate_schema(),
            }
        },
        "required": ["offers"],
        "additionalProperties": True,
    }

