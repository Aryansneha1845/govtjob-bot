"""
UPSC scraper - directly scrapes upsc.gov.in via Jina AI
"""
import hashlib
import requests
from bs4 import BeautifulSoup

SOURCE = "UPSC"
JINA_PREFIX = "https://r.jina.ai/"

URLS = [
    "https://upsc.gov.in/examinations/active-examinations",
    "https://upsc.gov.in/releases/active",
]

def scrape_upsc() -> list:
    for url in URLS:
        try:
            # Jina se fetch karo — government sites block nahi hoti
            resp = requests.get(
                f"{JINA_PREFIX}{url}",
                headers={"Accept": "text/plain", "X-No-Cache": "true"},
                timeout=20
            )
            if resp.status_code == 200:
                jobs = _parse_text(resp.text, url)
                if jobs:
                    return jobs
        except Exception:
            continue
    return []


def _parse_text(text: str, base_url: str) -> list:
    jobs = []
    keywords = [
        "recruitment", "vacancy", "notification", "advertisement",
        "exam", "civil services", "cds", "nda", "capf", "ifs",
        "combined", "engineer", "geologist", "medical"
    ]

    seen = set()
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 15:
            continue
        if not any(k in line.lower() for k in keywords):
            continue

        # URL extract karo line se
        import re
        urls_found = re.findall(r'https?://[^\s\)]+', line)
        href = urls_found[0] if urls_found else base_url

        # Clean title
        title = re.sub(r'https?://\S+', '', line).strip()
        title = re.sub(r'[\[\]\(\)]', '', title).strip()
        if len(title) < 10:
            continue

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

    return jobs[:10]
