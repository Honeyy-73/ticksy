"""
database.py
Handles the SQLite connection and creates the tables for the
Ticksy - Daily Task and Schedule Management application.
"""

import os
import sqlite3


class Database:
    """Wraps all SQLite operations so other classes never touch sqlite3 directly."""

    def __init__(self, db_name="ticksy.db"):
        base_folder = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_folder, db_name)
        self.create_tables()

    def connect(self):
        """Open a new connection. Rows can be read like dictionaries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_tables(self):
        """Create users, tasks, and schedules tables if they do not exist yet."""
        conn = self.connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT NOT NULL UNIQUE,
                    full_name     TEXT NOT NULL,
                    salt          TEXT NOT NULL,
                    password_hash TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT,
                    date        TEXT NOT NULL,
                    time        TEXT NOT NULL,
                    category    TEXT NOT NULL DEFAULT 'Personal',
                    completed   INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    title       TEXT NOT NULL,
                    description TEXT,
                    date        TEXT NOT NULL,
                    time        TEXT NOT NULL,
                    category    TEXT NOT NULL DEFAULT 'Personal',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def execute(self, query, params=()):
        """Run INSERT / UPDATE / DELETE. Returns the last inserted row id."""
        conn = self.connect()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def fetch_all(self, query, params=()):
        """Run a SELECT and return a list of rows."""
        conn = self.connect()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        """Run a SELECT and return a single row (or None)."""
        conn = self.connect()
        try:
            return conn.execute(query, params).fetchone()
        finally:
            conn.close()


# Quick self-test: run this file directly
if __name__ == "__main__":
    db = Database("test_db_check.db")
    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    print("Tables created:", [row["name"] for row in tables])
    for table in ("tasks", "schedules"):
        columns = [r["name"] for r in db.fetch_all(f"PRAGMA table_info({table})")]
        print(f"  {table}:", columns)
    os.remove(db.db_path)
    print("Database OK - test database removed.")