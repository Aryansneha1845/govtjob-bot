"""
Database - GitHub pe seen IDs store karta hai permanently.
Railway restart hone pe bhi data safe rehta hai.
"""
import os
import sqlite3
import requests
import base64
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jobs.db")
SEEN_IDS_FILE = "data/seen_ids.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")

_seen_ids = set()


def _load_from_github() -> set:
    """GitHub se seen IDs load karo."""
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return set()
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SEEN_IDS_FILE}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.ok:
            content = base64.b64decode(resp.json()["content"]).decode("utf-8")
            ids = json.loads(content)
            print(f"✅ Loaded {len(ids)} seen IDs from GitHub")
            return set(ids)
    except Exception as e:
        print(f"⚠️ Could not load seen IDs from GitHub: {e}")
    return set()


def _save_to_github(ids: set):
    """GitHub pe seen IDs save karo."""
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{SEEN_IDS_FILE}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        # Get existing SHA
        get_resp = requests.get(url, headers=headers, timeout=10)
        sha = get_resp.json().get("sha") if get_resp.ok else None

        content = json.dumps(list(ids), indent=2)
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": "Auto: Update seen IDs [skip ci]",
            "content": content_b64,
        }
        if sha:
            payload["sha"] = sha

        resp = requests.put(url, json=payload, headers=headers, timeout=10)
        if resp.ok:
            print(f"✅ Saved {len(ids)} seen IDs to GitHub")
        else:
            print(f"⚠️ Could not save seen IDs: {resp.text}")
    except Exception as e:
        print(f"⚠️ GitHub save error: {e}")


class Database:
    def __init__(self):
        global _seen_ids
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._create_table()
        # Pehle local DB se load karo
        self._load_local()
        # Phir GitHub se merge karo
        github_ids = _load_from_github()
        _seen_ids.update(github_ids)
        print(f"📦 Total seen IDs in memory: {len(_seen_ids)}")

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id        TEXT PRIMARY KEY,
                title     TEXT NOT NULL,
                source    TEXT NOT NULL,
                url       TEXT,
                last_date TEXT,
                posted_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _load_local(self):
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
        _seen_ids.add(job["id"])
        # GitHub pe save karo
        _save_to_github(_seen_ids)

    def recent(self, limit: int = 20) -> list:
        cur = self.conn.execute(
            "SELECT * FROM jobs ORDER BY posted_at DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self):
        self.conn.close()
