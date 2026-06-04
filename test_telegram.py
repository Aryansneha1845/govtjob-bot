import os
import sys
import time
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# Main components import kar rahe hain accuracy test ke liye
from scrapers.upsc import scrape_upsc
from scrapers.rrb import scrape_rrb
from gemini_extractor import extract_job_details
from telegram_poster import TelegramPoster

def run_live_accuracy_test():
    if not BOT_TOKEN or not CHANNEL_ID:
        log.error("❌ Error: .env configuration incomplete!")
        sys.exit(1)
        
    poster = TelegramPoster(BOT_TOKEN, CHANNEL_ID)
    
    log.info("📡 Step 1: Fetching LIVE links from UPSC website...")
    upsc_jobs = scrape_upsc()
    
    if not upsc_jobs:
        log.warning("⚠️ Live UPSC page par abhi koi active links nahi mile. RRB check karte hain...")
        log.info("📡 Step 1.5: Fetching LIVE links from RRB website...")
        live_jobs = scrape_rrb()
        source_name = "RRB"
    else:
        live_jobs = upsc_jobs
        source_name = "UPSC"
        
    if not live_jobs:
        log.error("❌ Dono websites par koi raw links nahi mile. Check your internet or scrapers.")
        return

    # Pehla real raw link uthate hain test karne ke liye
    test_target = live_jobs[0]
    log.info(f"🎯 Target Found from {source_name}!")
    log.info(f"🔗 Raw Title: {test_target['title']}")
    log.info(f"🌐 Raw URL: {test_target['url']}")
    
    log.info("🧠 Step 2: Sending this live link to Gemini AI for structural extraction...")
    log.info("Wait... Gemini pure page ko analyze karke actual accurate table ready kar raha hai...")
    
    # Real AI Extraction check
    extracted_details = extract_job_details(test_target["title"], test_target["url"])
    
    # Merge extracted details with source data
    test_target.update(extracted_details)
    test_target["source"] = source_name
    test_target["detailed_page_url"] = test_target["url"] # Testing ke liye direct portal link use karenge
    
    log.info("📊 --- EXTRACTION ACCURACY PREVIEW ---")
    log.info(f"🔹 Extracted Job Title: {test_target.get('job_title')}")
    log.info(f"🔹 Total Vacancies: {test_target.get('total_vacancies')}")
    log.info(f"🔹 Qualification Needed: {test_target.get('qualification')}")
    log.info(f"🔹 Last Date parsed: {test_target.get('last_date')}")
    log.info(f"🔹 Application Fee: {test_target.get('application_fee')}")
    log.info("---------------------------------------")
    
    log.info("📤 Step 3: Broadcasting this LIVE parsed data to Telegram...")
    success = poster.post(test_target)
    
    if success:
        log.info("🎉 SUCCESS! Live test alert successfully pushed to Telegram channel!")
        log.info("Abhi channel par jaao aur check karo ki details accurate hain ya nahi!")
    else:
        log.error("❌ Telegram broadcast failed.")

if __name__ == "__main__":
    run_live_accuracy_test()