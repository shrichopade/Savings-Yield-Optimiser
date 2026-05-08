from __future__ import annotations

# bootstrap.py — creates the SQLite database file and applies the schema.sql
# This is used by CLI tools to “initialize” the local database.

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from backend.app.db.connection import apply_sqlite_pragmas


@dataclass(frozen=True)
class BootstrapResult:
    db_path: Path
    schema_path: Path


def init_db(db_path: Path, schema_path: Path) -> BootstrapResult:
    # Create the DB file (if missing) and apply the schema DDL.
    # Inputs: db_path (where the sqlite file lives), schema_path (the .sql schema file).
    # Returns: BootstrapResult with the paths that were used.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        # Apply PRAGMA settings and then run the schema.sql as one script.
        apply_sqlite_pragmas(conn)
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    return BootstrapResult(db_path=db_path, schema_path=schema_path)

