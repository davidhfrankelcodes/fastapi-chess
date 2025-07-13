# app/db.py
import sqlite3
from contextlib import contextmanager

DB_FILE = "games.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.commit()
    conn.close()

def init_db():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            white_token TEXT NOT NULL,
            black_token TEXT NOT NULL
        );
        """)
