from __future__ import annotations

# init_db.py — CLI helper to create the local SQLite database and apply schema.sql
# Usage: python -m backend.app.cli.init_db

from pathlib import Path

from backend.app.db.bootstrap import init_db


def main() -> None:
    # Locate the repo root, then initialize the DB using the checked-in schema.sql.
    # Returns: nothing (prints what it created).
    repo_root = Path(__file__).resolve().parents[3]
    db_path = repo_root / "data" / "app.db"
    schema_path = repo_root / "backend" / "sql" / "schema.sql"

    result = init_db(db_path=db_path, schema_path=schema_path)
    print(f"Initialised SQLite DB: {result.db_path}")
    print(f"Applied schema: {result.schema_path}")


if __name__ == "__main__":
    main()

