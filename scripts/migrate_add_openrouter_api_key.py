"""Add openrouter_api_key column to users table in data.db. Idempotent; safe to run multiple times."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN openrouter_api_key TEXT DEFAULT ''")
        conn.commit()
        print("Migration applied.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column already exists, skip.")
        else:
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
