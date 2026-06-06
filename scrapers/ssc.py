import requests
from bs4 import BeautifulSoup
import logging
import hashlib
import re

log = logging.getLogger(__name__)

JINA_PREFIX = "https://r.jina.ai/"
HEADERS = {"Accept": "text/plain", "X-No-Cache": "true"}

URLS = [
    "https://ssc.gov.in/portal/latestNews",
    "https://www.sarkariresult.com/latestjob/ssc/",
]

KEYWORDS = ["cgl", "chsl", "gd", "mts", "cpo", "steno", "je", "recruitment",
            "examination", "notice", "vacancy", "notification", "selection post"]

SKIP_WORDS = ["archive", "calendar", "tentative", "result", "admit card",
              "answer key", "cut off", "syllabus", "schedule"]


def scrape_ssc() -> list:
    # Pehle Jina se ssc.gov.in try karo
    for url in URLS:
        try:
            if "ssc.gov.in" in url:
                resp = requests.get(f"{JINA_PREFIX}{url}", headers=HEADERS, timeout=20)
                if resp.status_code == 200 and len(resp.text) > 500:
                    jobs = _parse_text(resp.text, url)
                    if jobs:
                        log.info(f"✅ SSC: {len(jobs)} jobs found via Jina")
                        return jobs
            else:
                # sarkariresult.com direct fetch
                resp = requests.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    jobs = _parse_html(soup, url)
                    if jobs:
                        log.info(f"✅ SSC: {len(jobs)} jobs found via sarkariresult")
                        return jobs
        except Exception as e:
            log.error(f"SSC scrape failed for {url}: {e}")
            continue
    return []


def _parse_text(text: str, base_url: str) -> list:
    jobs = []
    seen = set()

    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 15:
            continue
        if not any(k in line.lower() for k in KEYWORDS):
            continue
        if any(s in line.lower() for s in SKIP_WORDS):
            continue

        urls_found = re.findall(r'https?://[^\s\)]+', line)
        href = urls_found[0] if urls_found else base_url

        title = re.sub(r'https?://\S+', '', line).strip()
        title = re.sub(r'[\[\]\(\)]', '', title).strip()

        if len(title) < 10 or title in seen:
            continue
        seen.add(title)

        job_id = "ssc_" + hashlib.md5(title.encode()).hexdigest()[:12]
        jobs.append({
            "id": job_id,
            "title": title,
            "url": href if not href.lower().endswith(".pdf") else base_url,
            "source": "SSC",
            "last_date": "",
            "posts": "",
        })

    return jobs[:6]


def _parse_html(soup, base_url: str) -> list:
    jobs = []
    seen = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a.get("href", "")

        if len(title) < 10:
            continue
        if not any(k in title.lower() for k in KEYWORDS):
            continue
        if any(s in title.lower() for s in SKIP_WORDS):
            continue
        if href.lower().endswith(".pdf"):
            continue

        if href and not href.startswith("http"):
            href = "https://www.sarkariresult.com" + href

        if title in seen:
            continue
        seen.add(title)

        job_id = "ssc_" + hashlib.md5(title.encode()).hexdigest()[:12]
        jobs.append({
            "id": job_id,
            "title": title,
            "url": href,
            "source": "SSC",
            "last_date": "",
            "posts": "",
        })

    return jobs[:6]
