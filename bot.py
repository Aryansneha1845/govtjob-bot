import os
import sys
import time
import logging
import re
from dotenv import load_dotenv

load_dotenv()

# Setup system directory paths safely using absolute tracking base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# Main target output injection route configuration
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

# 🔥 DYNAMIC ROUTING CONFIGURATION: 
# Agar local testing kar rahe ho toh .env me SITE_DOMAIN=http://127.0.0.1:5500 set karo, warna production link automatically pick ho jayegi.
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "https://deshnaukri.in").rstrip("/")

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

def create_detailed_job_page(job_data):
    """
    Website page template ke placeholders ko dynamically fill karta hai.
    Saves generation logs using absolute cross-platform directories.
    """
    try:
        template_path = os.path.join(BASE_DIR, "templates", "job_template.html")
        if not os.path.exists(template_path):
            log.warning(f"⚠️ Template file missing at exact structure path: {template_path}!")
            return None

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        placeholders = {
            "job_title": job_data.get("job_title") or job_data.get("title") or "Government Job Update",
            "organization": job_data.get("organization") or job_data.get("source") or "Central/State Department",
            "post_name": job_data.get("post_name") or job_data.get("title") or "Not Specified",
            "total_vacancies": job_data.get("total_vacancies") or job_data.get("vacancies") or "Check Notification",
            "salary": job_data.get("salary") or "As per government rules",
            "qualification": job_data.get("qualification") or job_data.get("eligibility") or "Detailed qualification inside notification",
            "age_limit": job_data.get("age_limit") or "As per recruitment rules",
            "application_fee": job_data.get("application_fee") or job_data.get("form_fee") or "Check website",
            "job_profile_description": job_data.get("job_profile_description") or "Is naukri ke baare me poori jaankari niche official portal par dekhein.",
            "start_date": job_data.get("start_date") or "Started",
            "last_date": job_data.get("last_date") or "Click official link",
            "exam_date": job_data.get("exam_date") or "To be notified",
            "official_apply_link": job_data.get("official_apply_link") or job_data.get("url") or "#",
            "source_url": job_data.get("url") or "#"
        }

        for key, value in placeholders.items():
            html_content = html_content.replace(f"{{{{ {key} }}}}", str(value))
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
            
        title_for_slug = placeholders["job_title"]
        clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title_for_slug).lower()
        file_name = clean_title.replace(" ", "-") + ".html"
        
        # Absolute runtime output writing
        output_file_path = os.path.join(OUTPUT_JOBS_DIR, file_name)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # Clear clean slashed trailing redirection layout extraction
        full_redirect_url = f"{SITE_DOMAIN}/jobs/{file_name}"
        log.info(f"📂 HTML Page Saved Safely: {output_file_path}")
        log.info(f"🔗 Target Redirect Generated: {full_redirect_url}")
        
        return full_redirect_url
    except Exception as e:
        log.error(f"❌ Error while creating HTML Page: {e}")
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
                    
                    # Raw title aur URLs ko standard check ke liye convert karte hain
                    raw_title_lower = str(job.get("title", "")).lower()
                    raw_url_lower = str(job.get("url", "")).lower()

                    # 🚨 100% BULLETPROOF PORTAL SECURITY FILTER
                    # Agar link ya title ke andar marksheets, verification links, ya old results hain, unhe direct ban karo.
                    is_junk_portal = any(word in raw_url_lower or word in raw_title_lower for word in [
                        "marksheet", "mark-sheet", "result_system", "archives", 
                        "written-result", "marksheet_system", "exam/marksheet"
                    ])
                    
                    if is_junk_portal:
                        log.warning(f"⚠️ [Security Bypass] Discarding junk marksheet/result portal link: {job['title'][:40]}")
                        db.save(job) # DB mein track kar lo taaki agli cycle mein dobara hit na ho
                        continue

                    # 🚀 Gemini Content Mapping with Full Deep Context
                    log.info("🧠 Requesting Gemini AI to parse context details...")
                    full_api_context = f"Title: {job['title']} | Direct URL: {job['url']} | Extra Meta: {job.get('raw_context', '')}"
                    details = extract_job_details(full_api_context, job["url"])
                    
                    # Safe dict verification layer
                    if details and isinstance(details, dict):
                        job.update(details)
                    
                    # 🔥 ULTRA FALLBACK: Ensuring validation check passes smoothly
                    if not job.get("job_title"):
                        job["job_title"] = job.get("title", "Government Job Update")
                    
                    parsed_title_lower = str(job.get("job_title", "")).lower()

                    # 🚨 REFINED INTELLIGENT FILTER BLOCK (Structural Link Filters)
                    is_menu_link = any(mk in raw_title_lower for mk in ["active examination", "forthcoming", "recruitment requisition"])
                    has_real_vacancy_signal = any(vk in raw_title_lower or vk in parsed_title_lower for vk in ["posts", "vacancy", "advertisement", "notice", "recruitment"])
                    
                    if len(raw_title_lower) < 5 or (is_menu_link and not has_real_vacancy_signal):
                        log.warning(f"⚠️ Skipping internal structural page link: {job['title'][:40]}")
                        db.save(job) # DB me save taaki tokens bachein
                        continue
                    
                    log.info(f"✅ Gemini Parsing Clear! Extracted Title: {job.get('job_title')}")
                    
                    # HTML Page Generation for local rendering
                    web_page_url = create_detailed_job_page(job)
                    if web_page_url:
                        job["detailed_page_url"] = web_page_url
                    
                    db.save(job)
                    
                    # Broadcast to Telegram Channel directly
                    log.info("📤 Triggering Telegram Broadcast Payload...")
                    success = poster.post(job)
                    if success:
                        log.info(f"🎉 SUCCESS! Clean Alert posted on Telegram for {source}")
                    else:
                        log.error(f"❌ FAILED! Telegram API rejected the post request.")
                    
                    # Fix Kept at 6s for strict standard Free tier secure API mapping delay loop
                    time.sleep(6)
                else:
                    # Log mapping to skip terminal cluttering
                    pass
        except Exception as e:
            log.error(f"💥 CRITICAL PIPELINE FAILURE in {source} execution loop: {e}")
            
    log.info("🏁 All channels checked successfully. Entering sleep state.")

def main():
    if not BOT_TOKEN:
        log.error("❌ CRITICAL: TELEGRAM_BOT_TOKEN missing in configuration files!")
        sys.exit(1)
    if not CHANNEL_ID:
        log.error("❌ CRITICAL: TELEGRAM_CHANNEL_ID missing in configuration files!")
        sys.exit(1)

    log.info(f"🚀 Bot engine active — Broadcast Targets: {CHANNEL_ID}")
    
    # Run immediate check sequence on execution start
    check_and_post()

    while True:
        log.info("Sleeping 30 minutes before next crawl window...")
        time.sleep(1800)
        check_and_post()

if __name__ == "__main__":
    main()