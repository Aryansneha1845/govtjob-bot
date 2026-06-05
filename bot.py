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

OUTPUT_JOBS_DIR = os.path.join(BASE_DIR, "public_html", "jobs")
os.makedirs(OUTPUT_JOBS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "https://deshnaukri.netlify.app").rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")

from database import Database
from scrapers.ssc import scrape_ssc
from scrapers.upsc import scrape_upsc
from scrapers.rrb import scrape_rrb
from telegram_poster import TelegramPoster
from gemini_extractor import extract_job_details

SCRAPERS = {
    "SSC":  scrape_ssc,
    "UPSC": scrape_upsc,
    "RRB":  scrape_rrb,
}


def commit_page_to_github(file_path: str, html_content: str):
    """Automatically commits generated HTML page to GitHub repo."""
    try:
        if not GITHUB_TOKEN or not GITHUB_REPO:
            log.warning("⚠️ GitHub token or repo not set — skipping commit.")
            return

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Check if file already exists (need SHA for update)
        get_resp = requests.get(api_url, headers=headers)
        sha = get_resp.json().get("sha") if get_resp.ok else None

        content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Auto: Add job page {file_path}",
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
    """
    Website page template ke placeholders ko dynamically fill karta hai.
    Auto commits to GitHub so Netlify publishes it automatically.
    """
    try:
        template_path = os.path.join(BASE_DIR, "templates", "job_template.html")
        if not os.path.exists(template_path):
            log.warning(f"⚠️ Template file missing at: {template_path}!")
            return None

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        placeholders = {
            "job_title":             job_data.get("job_title") or job_data.get("title") or "Government Job Update",
            "organization":          job_data.get("organization") or job_data.get("source") or "Central/State Department",
            "post_name":             job_data.get("post_name") or job_data.get("title") or "Not Specified",
            "total_vacancies":       job_data.get("total_vacancies") or job_data.get("vacancies") or "Check Notification",
            "salary":                job_data.get("salary") or "As per 7th Pay Commission",
            "qualification":         job_data.get("qualification") or job_data.get("eligibility") or "Check notification PDF",
            "age_limit":             job_data.get("age_limit") or "As per recruitment rules",
            "application_fee":       job_data.get("application_fee") or job_data.get("form_fee") or "Check official website",
            "job_profile_description": job_data.get("job_profile_description") or "Poori jaankari official portal par dekhein.",
            "start_date":            job_data.get("start_date") or "Available Now",
            "last_date":             job_data.get("last_date") or "Click official link",
            "exam_date":             job_data.get("exam_date") or "To be notified",
            "official_apply_link":   job_data.get("official_apply_link") or job_data.get("url") or "#",
            "source_url":            job_data.get("url") or "#"
        }

        for key, value in placeholders.items():
            html_content = html_content.replace(f"{{{{ {key} }}}}", str(value))
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        title_for_slug = placeholders["job_title"]
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title_for_slug).lower()
        file_name = clean_title.replace(" ", "-")[:80] + ".html"

        # Save locally on Railway
        output_file_path = os.path.join(OUTPUT_JOBS_DIR, file_name)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Auto commit to GitHub → Netlify will auto-publish
        commit_page_to_github(f"public_html/jobs/{file_name}", html_content)

        full_redirect_url = f"{SITE_DOMAIN}/jobs/{file_name}"
        log.info(f"📂 HTML Page Saved: {output_file_path}")
        log.info(f"🔗 Page URL: {full_redirect_url}")

        return full_redirect_url

    except Exception as e:
        log.error(f"❌ Error creating HTML page: {e}")
        return None


def check_and_post():
    db     = Database()
    poster = TelegramPoster(BOT_TOKEN, CHANNEL_ID)
    log.info("🔍 Starting Scraping Engine Cycle...")

    for source, scraper_fn in SCRAPERS.items():
        try:
            log.info(f"📡 Requesting live data from {source}...")
            jobs = scraper_fn()
            log.info(f"📊 {source} Response: Found {len(jobs)} total link(s) on target page.")

            for job in jobs:
                if not db.exists(job["id"]):
                    log.info(f"⚡ New Link Detected! ID: {job['id']} | Parsing Raw Title: {job['title'][:40]}")
                    job["source"] = source

                    raw_title_lower = str(job.get("title", "")).lower()
                    raw_url_lower   = str(job.get("url", "")).lower()

                    # Junk filter
                    is_junk_portal = any(word in raw_url_lower or word in raw_title_lower for word in [
                        "marksheet", "mark-sheet", "result_system", "archives",
                        "written-result", "marksheet_system", "exam/marksheet"
                    ])
                    if is_junk_portal:
                        log.warning(f"⚠️ Discarding junk link: {job['title'][:40]}")
                        db.save(job)
                        continue

                    # Gemini AI extraction
                    log.info("🧠 Requesting Gemini AI to parse context details...")
                    full_api_context = f"Title: {job['title']} | Direct URL: {job['url']} | Extra Meta: {job.get('raw_context', '')}"
                    details = extract_job_details(full_api_context, job["url"])

                    if details and isinstance(details, dict):
                        job.update(details)

                    if not job.get("job_title"):
                        job["job_title"] = job.get("title", "Government Job Update")

                    parsed_title_lower = str(job.get("job_title", "")).lower()

                    # Menu/structural link filter
                    is_menu_link = any(mk in raw_title_lower for mk in ["active examination", "forthcoming", "recruitment requisition"])
                    has_real_vacancy_signal = any(vk in raw_title_lower or vk in parsed_title_lower for vk in ["posts", "vacancy", "advertisement", "notice", "recruitment"])

                    if len(raw_title_lower) < 5 or (is_menu_link and not has_real_vacancy_signal):
                        log.warning(f"⚠️ Skipping structural page link: {job['title'][:40]}")
                        db.save(job)
                        continue

                    log.info(f"✅ Gemini Parsing Clear! Extracted Title: {job.get('job_title')}")

                    # Generate HTML page + commit to GitHub
                    web_page_url = create_detailed_job_page(job)
                    if web_page_url:
                        job["detailed_page_url"] = web_page_url

                    db.save(job)

                    # Telegram broadcast
                    log.info("📤 Triggering Telegram Broadcast Payload...")
                    success = poster.post(job)
                    if success:
                        log.info(f"🎉 SUCCESS! Clean Alert posted on Telegram for {source}")
                    else:
                        log.error(f"❌ FAILED! Telegram API rejected the post.")

                    # 💤 Safe window delay: Dynamic gap badha kar 30 seconds kar diya hai
                    # Taaki agar consecutive links aayein, toh pichli heavy PDF ka TPM volume cooldown ho jaye.
                    log.info("🏁 Job transaction finished. Sleeping 30 seconds to safeguard tokens basket...")
                    time.sleep(30)

        except Exception as e:
            log.error(f"💥 CRITICAL PIPELINE FAILURE in {source}: {e}")

    log.info("🏁 All channels checked successfully. Entering sleep state.")


def main():
    if not BOT_TOKEN:
        log.error("❌ CRITICAL: TELEGRAM_BOT_TOKEN missing!")
        sys.exit(1)
    if not CHANNEL_ID:
        log.error("❌ CRITICAL: TELEGRAM_CHANNEL_ID missing!")
        sys.exit(1)

    log.info(f"🚀 Bot engine active — Broadcast Targets: {CHANNEL_ID}")

    check_and_post()

    while True:
        log.info("Sleeping 30 minutes before next crawl window...")
        time.sleep(1800)
        check_and_post()


if __name__ == "__main__":
    main()
