from __future__ import annotations

from pathlib import Path

from backend.app.db.bootstrap import init_db


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    db_path = repo_root / "data" / "app.db"
    schema_path = repo_root / "backend" / "sql" / "schema.sql"

    result = init_db(db_path=db_path, schema_path=schema_path)
    print(f"Initialised SQLite DB: {result.db_path}")
    print(f"Applied schema: {result.schema_path}")


if __name__ == "__main__":
    main()

