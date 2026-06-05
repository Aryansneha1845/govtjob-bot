"""
RRB scraper - uses sarkariresult.com (accessible from all IPs)
"""
import hashlib
import requests
from bs4 import BeautifulSoup

SOURCE = "RRB"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = [
    "https://www.sarkariresult.com/latestjob/railway/",
    "https://rojgarresult.com/railway/",
]

def scrape_rrb() -> list:
    for url in URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = _parse(soup, url)
            if jobs:
                return jobs
        except Exception as e:
            continue
    return []

def _parse(soup, base_url) -> list:
    jobs = []
    keywords = ["railway", "rrb", "ntpc", "group d", "technician", "loco pilot",
                "recruitment", "vacancy", "notification", "ald", "rpf"]
    
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href  = a.get("href", "")
        if not title or len(title) < 10:
            continue
        if not any(k in title.lower() for k in keywords):
            continue
        if href and not href.startswith("http"):
            href = "https://www.sarkariresult.com" + href
        job_id = hashlib.md5(f"RRB_{title}".encode()).hexdigest()
        jobs.append({
            "id": job_id,
            "title": title,
            "source": SOURCE,
            "url": href or base_url,
            "last_date": "",
            "posts": "",
        })
    return jobs[:8]
