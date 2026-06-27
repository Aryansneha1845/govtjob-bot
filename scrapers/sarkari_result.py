"""
SarkariResult Telegram Channel Monitor
Telethon se @SarkariResult channel monitor karta hai
"""
import os
import hashlib

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
        from telethon.sync import TelegramClient
        import asyncio

        async def fetch():
            messages = []
            async for message in client.iter_messages(CHANNEL, limit=20):
                if not message.text:
                    continue

                text = message.text.strip()

                # Keyword check
                if not any(k in text.lower() for k in KEYWORDS):
                    continue

                # Skip words check
                if any(s in text.lower() for s in SKIP_WORDS):
                    continue

                # URL extract karo
                import re
                urls = re.findall(r'https?://[^\s]+', text)
                url = urls[0] if urls else f"https://t.me/SarkariResult/{message.id}"

                # Title — pehli line
                title = text.split('\n')[0].strip()[:100]
                if len(title) < 10:
                    continue

                if title in seen:
                    continue
                seen.add(title)

                job_id = "sr_" + hashlib.md5(f"{message.id}_{title}".encode()).hexdigest()[:12]
                messages.append({
                    "id": job_id,
                    "title": title,
                    "url": url,
                    "source": SOURCE,
                    "raw_context": text[:500],
                    "last_date": "",
                    "posts": "",
                })

            return messages

        loop = asyncio.new_event_loop()
        jobs = loop.run_until_complete(fetch())
        loop.close()

    except Exception as e:
        print(f"💥 SarkariResult scrape failed: {e}")

    return jobs[:8]
