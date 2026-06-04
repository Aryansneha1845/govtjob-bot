"""
SQLite database for storing seen job notifications.
Prevents duplicate posts to Telegram.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jobs.db")


class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                source      TEXT NOT NULL,
                url         TEXT,
                last_date   TEXT,
                posted_at   TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def exists(self, job_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM jobs WHERE id = ?", (job_id,)
        )
        return cur.fetchone() is not None

    def save(self, job: dict):
        from datetime import datetime
        self.conn.execute(
            """INSERT OR IGNORE INTO jobs
               (id, title, source, url, last_date, posted_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                job["id"],
                job["title"],
                job.get("source", ""),
                job.get("url", ""),
                job.get("last_date", ""),
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()

    def recent(self, limit: int = 20) -> list:
        cur = self.conn.execute(
            "SELECT * FROM jobs ORDER BY posted_at DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self):
        self.conn.close()
