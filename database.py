"""
SQLite database - uses in-memory set for fast duplicate detection.
Persists to file when possible.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jobs.db")

# In-memory set for fast duplicate detection even after DB issues
_seen_ids = set()

class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._create_table()
        self._load_seen_ids()

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

    def _load_seen_ids(self):
        """Load all seen IDs into memory on startup."""
        global _seen_ids
        try:
            cur = self.conn.execute("SELECT id FROM jobs")
            _seen_ids = set(row[0] for row in cur.fetchall())
        except:
            _seen_ids = set()

    def exists(self, job_id: str) -> bool:
        return job_id in _seen_ids

    def save(self, job: dict):
        global _seen_ids
        from datetime import datetime
        try:
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
        except:
            pass
        # Always add to memory set
        _seen_ids.add(job["id"])

    def recent(self, limit: int = 20) -> list:
        cur = self.conn.execute(
            "SELECT * FROM jobs ORDER BY posted_at DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self):
        self.conn.close()
