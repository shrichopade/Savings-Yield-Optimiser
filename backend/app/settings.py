from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    db_path: Path
    schema_path: Path


def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[2]
    return Settings(
        repo_root=repo_root,
        db_path=repo_root / "data" / "app.db",
        schema_path=repo_root / "backend" / "sql" / "schema.sql",
    )

