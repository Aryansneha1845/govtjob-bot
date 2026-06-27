"""
SarkariResult Telegram Channel Monitor
Telethon se @SarkariResult channel monitor karta hai
"""
import hashlib
import re

SOURCE = "SarkariResult"
CHANNEL = "SarkariResult"

KEYWORDS = [
    "recruitment", "vacancy", "notification", "advertisement",
    "form", "apply", "posts", "bharti", "jobs", "sarkari"
]

SKIP_WORDS = [
    "result", "admit card", "answer key", "cut off",
    "merit list", "syllabus", "exam date", "schedule"
]


def scrape_sarkari_result(client) -> list:
    """Telethon client se SarkariResult channel ke latest messages fetch karo."""
    jobs = []
    seen = set()

    try:
        # Synchronous approach — no new event loop
        messages = client.get_messages(CHANNEL, limit=20)

        for message in messages:
            if not message.text:
                continue

            text = message.text.strip()

            if not any(k in text.lower() for k in KEYWORDS):
                continue

            if any(s in text.lower() for s in SKIP_WORDS):
                continue

            urls = re.findall(r'https?://[^\s]+', text)
            url = urls[0] if urls else f"https://t.me/SarkariResult/{message.id}"

            title = text.split('\n')[0].strip()[:100]
            if len(title) < 10:
                continue

            if title in seen:
                continue
            seen.add(title)

            job_id = "sr_" + hashlib.md5(f"{message.id}_{title}".encode()).hexdigest()[:12]
            jobs.append({
                "id": job_id,
                "title": title,
                "url": url,
                "source": SOURCE,
                "raw_context": text[:500],
                "last_date": "",
                "posts": "",
            })

    except Exception as e:
        print(f"💥 SarkariResult scrape failed: {e}")

    return jobs[:8]
