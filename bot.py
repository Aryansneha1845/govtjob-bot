import os
import sys
import time
import logging
import re
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

OUTPUT_JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(OUTPUT_JOBS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID   = os.getenv("TELEGRAM_CHANNEL_ID", "")
SITE_DOMAIN  = os.getenv("SITE_DOMAIN", "https://aryansneha1845.github.io/govtjob-bot").rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")
TG_API_ID    = int(os.getenv("TELEGRAM_API_ID", "0"))
TG_API_HASH  = os.getenv("TELEGRAM_API_HASH", "")

from database import Database
from scrapers.ssc import scrape_ssc
from scrapers.upsc import scrape_upsc
from scrapers.rrb import scrape_rrb
from scrapers.bpsc import scrape_bpsc
from scrapers.sarkari_result import scrape_sarkari_result
from telegram_poster import TelegramPoster
from gemini_extractor import extract_job_details

JUNK_WORDS = [
    "marksheet", "mark-sheet", "result_system",
    "written-result", "marksheet_system",
    "official website", "all board exams",
    "admit card", "answer key"
]

# Telethon client — global
tg_client = None

def get_tg_client():
    global tg_client
    if tg_client:
        return tg_client
    try:
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        session_str = os.getenv("TELEGRAM_SESSION", "")
        tg_client = TelegramClient(StringSession(session_str), TG_API_ID, TG_API_HASH)
        tg_client.connect()
        log.info("✅ Telethon client started!")
        return tg_client
    except Exception as e:
        log.error(f"❌ Telethon client failed: {e}")
        return None


def commit_page_to_github(file_path: str, html_content: str):
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        get_resp = requests.get(api_url, headers=headers)
        sha = get_resp.json().get("sha") if get_resp.ok else None
        content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Auto: Add job page {file_path} [skip ci]",
            "content": content_b64,
        }
        if sha:
            payload["sha"] = sha
        resp = requests.put(api_url, json=payload, headers=headers)
        if resp.ok:
            log.info(f"✅ GitHub commit success: {file_path}")
        else:
            log.error(f"❌ GitHub commit failed: {resp.text}")
    except Exception as e:
        log.error(f"❌ GitHub commit error: {e}")


def create_detailed_job_page(job_data):
    try:
        template_path = os.path.join(BASE_DIR, "templates", "job_template.html")
        if not os.path.exists(template_path):
            log.warning(f"⚠️ Template missing: {template_path}")
            return None

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        placeholders = {
            "job_title":               job_data.get("job_title") or job_data.get("title") or "Government Job Update",
            "organization":            job_data.get("organization") or job_data.get("source") or "Central/State Department",
            "post_name":               job_data.get("post_name") or job_data.get("title") or "Not Specified",
            "total_vacancies":         job_data.get("total_vacancies") or "Check Notification",
            "salary":                  job_data.get("salary") or "As per 7th Pay Commission",
            "qualification":           job_data.get("qualification") or "Check notification PDF",
            "age_limit":               job_data.get("age_limit") or "As per recruitment rules",
            "application_fee":         job_data.get("application_fee") or "Check official website",
            "job_profile_description": job_data.get("job_profile_description") or "Poori jaankari official portal par dekhein.",
            "start_date":              job_data.get("start_date") or "Available Now",
            "last_date":               job_data.get("last_date") or "Click official link",
            "exam_date":               job_data.get("exam_date") or "To be notified",
            "official_apply_link":     job_data.get("official_apply_link") or job_data.get("url") or "#",
            "source_url":              job_data.get("url") or "#"
        }

        for key, value in placeholders.items():
            html_content = html_content.replace(f"{{{{ {key} }}}}", str(value))
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', placeholders["job_title"]).lower()
        file_name = clean_title.replace(" ", "-")[:80] + ".html"

        output_file_path = os.path.join(OUTPUT_JOBS_DIR, file_name)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        commit_page_to_github(f"jobs/{file_name}", html_content)

        full_url = f"{SITE_DOMAIN}/jobs/{file_name}"
        log.info(f"📂 HTML Page Saved: {output_file_path}")
        log.info(f"🔗 Page URL: {full_url}")
        return full_url

    except Exception as e:
        log.error(f"❌ Error creating HTML page: {e}")
        return None


def process_jobs(jobs, source, db, poster):
    for job in jobs:
        if not db.exists(job["id"]):
            log.info(f"⚡ New: {job['title'][:40]} [{source}]")
            job["source"] = source

            raw_title_lower = str(job.get("title", "")).lower()
            raw_url_lower   = str(job.get("url", "")).lower()

            is_junk = any(w in raw_title_lower or w in raw_url_lower for w in JUNK_WORDS)
            if is_junk:
                log.warning(f"⚠️ Junk skipped: {job['title'][:40]}")
                db.save(job)
                continue

            log.info("🧠 AI extraction...")
            context = f"Title: {job['title']} | URL: {job['url']}"
            details = extract_job_details(context, job["url"])

            if details and isinstance(details, dict):
                job.update(details)

            if not job.get("job_title"):
                job["job_title"] = job.get("title", "Government Job Update")

            parsed_title_lower = str(job.get("job_title", "")).lower()

            if job.get("location") == "Bihar" or source == "BPSC":
                job["state_tag"] = "📍 BIHAR GOVT JOB"
            else:
                job["state_tag"] = "🌐 CENTRAL GOVT JOB"

            is_menu = any(mk in raw_title_lower for mk in [
                "active examination", "forthcoming", "recruitment requisition"
            ])
            has_vacancy_signal = any(vk in raw_title_lower or vk in parsed_title_lower for vk in [
                "posts", "vacancy", "advertisement", "notice", "recruitment", "form", "result"
            ])

            if len(raw_title_lower) < 5 or (is_menu and not has_vacancy_signal):
                log.warning(f"⚠️ Structural link skipped: {job['title'][:40]}")
                db.save(job)
                continue

            web_url = create_detailed_job_page(job)
            if web_url:
                job["detailed_page_url"] = web_url

            db.save(job)

            log.info("📤 Posting to Telegram...")
            success = poster.post(job)
            if success:
                log.info(f"🎉 Posted: {job.get('job_title')} [{source}]")
            else:
                log.error(f"❌ Telegram post failed.")

            time.sleep(30)


def check_and_post():
    db     = Database()
    poster = TelegramPoster(BOT_TOKEN, CHANNEL_ID)
    log.info("🔍 Starting Scraping Engine Cycle...")

    # Normal scrapers
    SCRAPERS = {
        "SSC":  scrape_ssc,
        "UPSC": scrape_upsc,
        "RRB":  scrape_rrb,
        "BPSC": scrape_bpsc,
    }

    for source, scraper_fn in SCRAPERS.items():
        try:
            log.info(f"📡 Requesting live data from {source}...")
            jobs = scraper_fn()
            log.info(f"📊 {source}: Found {len(jobs)} link(s).")
            process_jobs(jobs, source, db, poster)
        except Exception as e:
            log.error(f"💥 PIPELINE FAILURE in {source}: {e}")

    # SarkariResult Telegram channel
    try:
        if TG_API_ID and TG_API_HASH:
            log.info("📡 Requesting live data from SarkariResult TG...")
            client = get_tg_client()
            if client:
                jobs = scrape_sarkari_result(client)
                log.info(f"📊 SarkariResult: Found {len(jobs)} link(s).")
                process_jobs(jobs, "SarkariResult", db, poster)
    except Exception as e:
        log.error(f"💥 SarkariResult failed: {e}")

    log.info("🏁 Cycle complete. Entering sleep state.")


def main():
    if not BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN missing!")
        sys.exit(1)
    if not CHANNEL_ID:
        log.error("❌ TELEGRAM_CHANNEL_ID missing!")
        sys.exit(1)

    log.info(f"🚀 Bot engine active — Broadcast Targets: {CHANNEL_ID}")
    check_and_post()

    while True:
        log.info("Sleeping 30 minutes...")
        time.sleep(1800)
        check_and_post()


if __name__ == "__main__":
    main()
