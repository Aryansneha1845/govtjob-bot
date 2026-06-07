import requests
import hashlib
import re
from bs4 import BeautifulSoup

SOURCE = "BPSC"
JINA_PREFIX = "https://r.jina.ai/"
HEADERS = {"Accept": "text/plain", "X-No-Cache": "true"}

URLS = [
    "https://www.indgovtjobs.in/search/label/BPSC",
    "https://www.bpsc.bih.nic.in/Notices.aspx",
]

KEYWORDS = [
    "bpsc", "bihar", "recruitment", "vacancy", "notification",
    "advertisement", "exam", "posts", "combined", "teacher"
]

SKIP_WORDS = [
    "result", "admit card", "answer key", "syllabus",
    "cut off", "merit list", "schedule", "exam date"
]


def scrape_bpsc() -> list:
    for url in URLS:
        try:
            resp = requests.get(
                f"{JINA_PREFIX}{url}",
                headers=HEADERS,
                timeout=20
            )
            if resp.status_code == 200 and len(resp.text) > 500:
                jobs = _parse_text(resp.text, url)
                if jobs:
                    return jobs
        except Exception:
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
        title = re.sub(r'[\[\]\(\)\*]', '', title).strip()
        title = re.sub(r'^\s*[-•·]\s*', '', title).strip()
        title = title.strip('- ').strip()

        if len(title) < 10 or title in seen:
            continue
        seen.add(title)

        job_id = "bpsc_" + hashlib.md5(title.encode()).hexdigest()[:12]
        jobs.append({
            "id": job_id,
            "title": title,
            "url": href if not href.lower().endswith(".pdf") else base_url,
            "source": SOURCE,
            "location": "Bihar",
            "last_date": "",
            "posts": "",
        })

    return jobs[:6]
