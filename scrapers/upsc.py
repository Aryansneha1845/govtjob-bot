"""
UPSC scraper - sarkariresult.com se scrape karta hai, PDF links filter karta hai
"""
import hashlib
import requests
import re
from bs4 import BeautifulSoup

SOURCE = "UPSC"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = [
    "https://www.sarkariresult.com/latestjob/upsc/",
    "https://rojgarresult.com/upsc/",
]

KEYWORDS = [
    "upsc", "ias", "ips", "cds", "nda", "recruitment", "vacancy",
    "notification", "advertisement", "civil services", "capf",
    "combined", "engineer", "geologist", "medical", "forest"
]

SKIP_WORDS = [
    "result", "admit card", "answer key", "syllabus",
    "cut off", "merit list", "official website",
    "exam date", "exam calendar", "pmt", "schedule",
    "document verification", "interview date"
]


def scrape_upsc() -> list:
    for url in URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = _parse(soup, url)
            if jobs:
                return jobs
        except Exception:
            continue
    return []


def _parse(soup, base_url) -> list:
    jobs = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a.get("href", "")

        if not title or len(title) < 10:
            continue

        # Skip words filter
        if any(s in title.lower() for s in SKIP_WORDS):
            continue

        # Must have keyword
        if not any(k in title.lower() for k in KEYWORDS):
            continue

        # PDF links skip karo
        if href.lower().endswith(".pdf"):
            continue

        if href and not href.startswith("http"):
            href = "https://www.sarkariresult.com" + href

        if title in seen:
            continue
        seen.add(title)

        job_id = hashlib.md5(f"UPSC_{title}".encode()).hexdigest()
        jobs.append({
            "id": job_id,
            "title": title,
            "source": SOURCE,
            "url": href,
            "last_date": "",
            "posts": "",
        })

    return jobs[:8]
