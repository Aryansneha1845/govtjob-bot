"""
Uses Google Gemini API to extract job details from notification pages.
Extracts fields strictly mapped with bot.py placeholders.
Forces exact numeric salary ranges, qualifications, and mandatory experience requirements.
"""

import re 
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Gemini API URL
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def extract_job_details(title_or_context: str, url: str) -> dict:
    """Fetch job page and extract pin-point accurate details with exact numeric salary figures using Gemini."""
    
    # Page text source crawl karte hain
    page_text = _fetch_page(url)
    
    # Context buffer optimization
    context_data = page_text[:4000] if page_text else "No explicit page text content found."

    # 🔥 ULTRA STRICT PROMPT: Generic text is completely banned. Forcing exact numeric figures.
    prompt = f"""
You are an expert Indian Government Job Recruitment Analyst. Your absolute priority is to provide EXACT NUMERIC DIGITS, specific qualifications, and clear experience details.

CRITICAL RULE: Generic phrases like 'As per government rules', 'Check notification', or 'Level-10 Pay Matrix' without specific numeric amounts are COMPLETELY BANNED. 
If the exact numeric amounts or experience requirements are not explicitly clear in the text snippet, you MUST apply your knowledge of the 7th Pay Commission pay matrix and standard department cadres to extrapolate the EXACT numeric basic pay and clear experience standards.

Input Title/Metadata from Scraper: {title_or_context}
Scraped Page Content:
{context_data}

Instructions for specific JSON fields:
- job_title: Clean full recruitment name or specific post category.
- organization: Exact hiring authority (e.g., Union Public Service Commission (UPSC), Staff Selection Commission (SSC), Ministry of Health).
- post_name: Specific designation (e.g., Drugs Inspector, Public Prosecutor, Assistant Professor).
- total_vacancies: Extract exact numeric count from text or title (e.g., '20 Posts', '150 Vacancies').
- qualification: Specify clear degrees required (e.g., 'Degree in Pharmacy (B.Pharm)', 'Degree in Law (LLB)', 'B.E./B.Tech in Computer Science'). Be specific, no generic terms.
- salary: Provide the EXACT expected monthly salary figure or exact basic pay range in INR digits (e.g., 'Rs. 56,100 - Rs. 1,77,500 (Basic Pay Matrix)' or 'Approx Rs. 65,000/- Per Month (Consolidated)'). Always include numbers!
- age_limit: Exact numeric brackets (e.g., '18 - 30 Years' or 'Maximum 35 Years').
- application_fee: Exact currency digits (e.g., 'Rs. 25/- for Gen/OBC; SC/ST/Women: Free').
- job_profile_description: A clear 1-line catchy explanation that MUST explicitly state the experience requirement using exact terms like: 'Requires X years of post-qualification experience in relevant field.' OR 'No prior experience required. Freshers can apply.'

Provide the response STRICTLY in this JSON format. No markdown, no backticks, just raw JSON.

{{
    "job_title": "...",
    "organization": "...",
    "post_name": "...",
    "total_vacancies": "...",
    "qualification": "...",
    "salary": "...",
    "age_limit": "...",
    "application_fee": "...",
    "job_profile_description": "...",
    "start_date": "...",
    "last_date": "...",
    "exam_date": "...",
    "official_apply_link": "..."
}}
"""

    # Intelligent Fallback Data Structure with exact high-probability numeric figures
    clean_raw_title = str(title_or_context).split('|')[0].replace("Title:", "").strip()
    fallback_data = {
        "job_title": clean_raw_title if len(clean_raw_title) > 5 else "Government Recruitment Alert",
        "organization": "Central / State Department",
        "post_name": "Specified Officer Cadre",
        "total_vacancies": "Check Post Split-up",
        "qualification": "Graduate Degree / Diploma in relevant stream",
        "salary": "Rs. 44,900 - Rs. 1,42,400 (Expected Basic Pay)",
        "age_limit": "18 - 30 Years standard (Relaxation as per rules)",
        "application_fee": "Gen/OBC: Rs. 25-100 | SC/ST/Women: Free",
        "job_profile_description": "Core eligibility and exact experience requirements vary by department cadre. Open the official link below to view the eligibility dashboard.",
        "start_date": "Available Now",
        "last_date": "Click Official Link",
        "exam_date": "To be notified",
        "official_apply_link": url if url and url != "#" else "https://upsc.gov.in"
    }

    max_retries = 3
    backoff_delay = 6  # Kept at 6s for free tier safety

    for attempt in range(max_retries):
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,  # Lower temp guarantees strict rule-following
                    "maxOutputTokens": 1000,
                    "responseMimeType": "application/json"
                }
            }
            
            resp = requests.post(GEMINI_URL, json=payload, timeout=25)
            
            # Handle Rate Limiting (HTTP 429) - Exponential Backoff
            if resp.status_code == 429:
                print(f"⏳ Rate Limit (429) Hit! Attempt {attempt+1}/{max_retries}. Sleeping {backoff_delay}s before retry...")
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
                
            if not resp.ok:
                print(f"⚠️ Gemini HTTP Error: {resp.status_code} - {resp.text}")
                return fallback_data
            
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Safe JSON extraction
            parsed_json = json.loads(text)
            
            # 🔥 CRITICAL REDIRECTION FIX:
            # Agar Gemini proper apply link scrape nahi kar paya ya usne garbage/generic landing domain diya,
            # toh use forcibly overwrite karke wahi direct target URL de do jahan se scraper notification laya tha.
            invalid_links = ["", "#", "https://upsc.gov.in", "https://ssc.gov.in", "https://upsconline.gov.in"]
            if parsed_json.get("official_apply_link") is None or parsed_json.get("official_apply_link").strip() in invalid_links:
                print("🔗 [Redirection Sync] Gemini links fallback or empty. Forcing original scraper source URL.")
                parsed_json["official_apply_link"] = url
                
            return parsed_json
        
        except json.JSONDecodeError:
            print("💥 JSON parsing failed from Gemini output. Serving fallback data.")
            return fallback_data
        except Exception as e:
            print(f"💥 Attempt {attempt+1} failed due to connection error: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)

    print("🚨 All Gemini retries exhausted or rate-limited. Serving fallback.")
    if fallback_data["official_apply_link"] in ["#", "https://upsc.gov.in"]:
        fallback_data["official_apply_link"] = url
    return fallback_data

def _fetch_page(url: str) -> str:
    """Fetch webpage text content safely with advanced anti-bot bypass headers."""
    if not url or url == "#" or "javascript" in url.lower():
        return ""
    try:
        # Advanced desktop browser footprint to prevent bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Using Session layer to handle temporary tokens and redirection tracks
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        if resp.status_code != 200:
            print(f"⚠️ Web scraping blocked by portal node. Status Code: {resp.status_code}")
            return ""
        
        from bs4 import BeautifulSoup
        # Handle explicit response text encoding errors
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Decomposing non-informational nodes
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "meta", "link"]):
            tag.decompose()
        
        # Regular Expression to strip down duplicate white-spaces and single-line elements
        clean_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))
        return clean_text
        
    except Exception as e:
        print(f"💥 Portal scraping exception: {e}")
        return ""