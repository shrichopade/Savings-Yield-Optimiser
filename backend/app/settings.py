from __future__ import annotations

# settings.py — loads environment config (paths, tokens, refresh cadence)
# This keeps configuration in one place so other code can stay simple.

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    db_path: Path
    schema_path: Path
    firecrawl_api_key: str | None
    refresh_scheduler_enabled: bool
    refresh_interval_hours: int
    refresh_targets_json: str | None
    admin_token: str | None


def get_settings() -> Settings:
    # Read environment variables and compute important filesystem paths.
    # Returns: a Settings object (immutable) used across the backend.
    repo_root = Path(__file__).resolve().parents[2]
    # Load {repo_root}/.env if present, without overriding real env vars.
    load_dotenv(repo_root / ".env", override=False)
    return Settings(
        repo_root=repo_root,
        db_path=repo_root / "data" / "app.db",
        schema_path=repo_root / "backend" / "sql" / "schema.sql",
        firecrawl_api_key=os.environ.get("FIRECRAWL_API_KEY"),
        refresh_scheduler_enabled=os.environ.get("REFRESH_SCHEDULER_ENABLED", "0") == "1",
        refresh_interval_hours=int(os.environ.get("REFRESH_INTERVAL_HOURS", "6")),
        refresh_targets_json=os.environ.get("REFRESH_TARGETS_JSON"),
        admin_token=os.environ.get("ADMIN_TOKEN"),
    )

