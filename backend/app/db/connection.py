from __future__ import annotations

# connection.py — tiny helpers for opening SQLite connections safely
# We set SQLite “PRAGMA” settings to improve local reliability and performance.

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator


def apply_sqlite_pragmas(conn: sqlite3.Connection) -> None:
    # Configure SQLite for this app.
    # Inputs: an open sqlite3 connection.
    # Returns: nothing (mutates connection settings).
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")


def connect(db_path: Path) -> sqlite3.Connection:
    # Open a SQLite connection and apply our standard settings.
    # Inputs: db_path where the .db file lives.
    # Returns: an open sqlite3.Connection with row dictionaries enabled.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    apply_sqlite_pragmas(conn)
    return conn


@contextmanager
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    # Context manager that opens a DB connection and auto-commits on success.
    # Inputs: db_path.
    # Returns: yields an open connection; commits and closes automatically.
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

