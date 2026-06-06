"""
Uses Google Gemini API to extract job details from notification pages.
Uses Jina AI for free web page fetching — no blocks on government sites.
"""

import os
import json
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

# Safe string construction to prevent markdown copy-paste link corruption
protocol = "https://"
gemini_domain = "generativelanguage.googleapis.com"
gemini_endpoint = "/v1beta/models/gemini-2.0-flash-lite:generateContent?key="

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = f"{protocol}{gemini_domain}{gemini_endpoint}{GEMINI_API_KEY}"

def extract_job_details(title_or_context: str, url: str) -> dict:
    """Fetch job page via Jina AI and extract details using Gemini with dynamic backoff."""
    
    # Clean the incoming target URL first
    sanitized_url = _sanitize_url(url)
    page_text = _fetch_page(sanitized_url)
    
    # Reduced to 2000 characters to safeguard Gemini Free-Tier TPM limits and prevent 429 errors
    context_data = page_text[:2000] if page_text else "No explicit page text content found."

    prompt = f"""
You are an expert Indian Government Job Recruitment Analyst. Your absolute priority is to provide EXACT NUMERIC DIGITS, specific qualifications, and clear experience details.

CRITICAL RULE: Generic phrases like 'As per government rules', 'Check notification', or 'Level-10 Pay Matrix' without specific numeric amounts are COMPLETELY BANNED. 
If the exact numeric amounts are not explicitly clear, apply your knowledge of the 7th Pay Commission pay matrix to extrapolate EXACT numeric basic pay.

Input Title/Metadata: {title_or_context}
Scraped Page Content:
{context_data}

Instructions:
- job_title: Clean full recruitment name or specific post category.
- organization: Exact hiring authority (e.g., Union Public Service Commission (UPSC), Staff Selection Commission (SSC)).
- post_name: Specific designation (e.g., Drugs Inspector, Assistant Professor).
- total_vacancies: Exact numeric count (e.g., '20 Posts', '150 Vacancies').
- qualification: Specific degrees (e.g., 'Degree in Pharmacy (B.Pharm)', 'B.E./B.Tech in Computer Science').
- salary: EXACT monthly salary in INR digits (e.g., 'Rs. 56,100 - Rs. 1,77,500' or 'Approx Rs. 65,000/month').
- age_limit: Exact numeric brackets (e.g., '18 - 30 Years').
- application_fee: Exact digits (e.g., 'Rs. 25/- for Gen/OBC; SC/ST/Women: Free').
- job_profile_description: 2-3 line catchy Hindi-English summary. MUST state experience requirement explicitly.
- start_date: Application start date if mentioned.
- last_date: Last date to apply in DD Month YYYY format.
- exam_date: Exam date if mentioned.
- official_apply_link: Direct apply link. If not found, use: {sanitized_url}
- selection_process: e.g. Written Test, Physical Test, Interview
- job_type: Permanent / Contractual / Temporary
- location: Job location or All India

Provide STRICTLY in this JSON format. No markdown, no backticks, just raw JSON:

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
    "official_apply_link": "...",
    "selection_process": "...",
    "job_type": "...",
    "location": "..."
}}
"""

    clean_raw_title = str(title_or_context).split('|')[0].replace("Title:", "").strip()
    
    fallback_upsc = "https://" + "upsc.gov.in"
    fallback_data = {
        "job_title": clean_raw_title if len(clean_raw_title) > 5 else "Government Recruitment Alert",
        "organization": "Central / State Department",
        "post_name": "Specified Officer Cadre",
        "total_vacancies": "Check Notification",
        "qualification": "Graduate Degree / Diploma in relevant stream",
        "salary": "Rs. 44,900 - Rs. 1,42,400 (As per 7th Pay Commission)",
        "age_limit": "18 - 30 Years (Relaxation as per rules)",
        "application_fee": "Gen/OBC: Rs. 25-100 | SC/ST/Women: Free",
        "job_profile_description": "Sarkari naukri ka mauka! Poori eligibility aur experience details official link par dekhein.",
        "start_date": "Available Now",
        "last_date": "Click Official Link",
        "exam_date": "To be notified",
        "official_apply_link": sanitized_url if sanitized_url else fallback_upsc,
        "selection_process": "Written Test / Interview",
        "job_type": "Permanent",
        "location": "All India"
    }

    max_retries = 3
    backoff_delay = 15

    for attempt in range(max_retries):
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 800,
                    "responseMimeType": "application/json"
                }
            }
            
            resp = requests.post(GEMINI_URL, json=payload, timeout=25)
            
            if resp.status_code == 429:
                print(f"⏳ Rate Limit (429) Hit! Attempt {attempt+1}/{max_retries}. Sleeping {backoff_delay}s...")
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
                
            if not resp.ok:
                print(f"⚠️ Gemini HTTP Error: {resp.status_code}")
                return fallback_data
            
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                else:
                    clean_text = clean_text[3:]
                
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            parsed_json = json.loads(clean_text)
            
            invalid_links = ["", "#", "[https://upsc.gov.in](https://upsc.gov.in)", "[https://ssc.gov.in](https://ssc.gov.in)", "[https://upsconline.gov.in](https://upsconline.gov.in)"]
            if not parsed_json.get("official_apply_link") or parsed_json.get("official_apply_link", "").strip() in invalid_links:
                parsed_json["official_apply_link"] = sanitized_url
                
            return parsed_json
        
        except json.JSONDecodeError:
            print("💥 JSON parsing failed due to format corruption. Serving fallback.")
            return fallback_data
        except Exception as e:
            print(f"💥 Attempt {attempt+1} failed with exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    fallback_data["official_apply_link"] = sanitized_url
    return fallback_data


def _sanitize_url(url: str) -> str:
    """Helper to rip out any markdown format artifacts or brackets from the URL string safely."""
    if not url:
        return ""
    
    # Direct absolute hard scrub against markdown bracket artifacts
    clean = str(url).strip()
    clean = re.sub(r'[\[\]\(\)]', '', clean)
    
    # Extract clean absolute http/https link using regex
    found_urls = re.findall(r'https?://[^\s,]+', clean)
    if found_urls:
        return found_urls[-1]
    return clean


def _fetch_page(url: str) -> str:
    """Fetch page content via Jina AI safely without markdown clutter."""
    if not url or url == "#" or "javascript" in url.lower():
        return ""
    try:
        clean_target = _sanitize_url(url)
        
        # Hard code connection strings separately to prevent IDE/Browser copy-paste markdown wrapping
        p1 = "https://"
        p2 = "r.jina.ai/"
        jina_prefix = p1 + p2
        
        if "r.jina.ai" in clean_target:
            jina_url = clean_target
        else:
            jina_url = f"{jina_prefix}{clean_target}"
            
        headers = {
            "Accept": "text/plain",
            "X-No-Cache": "true"
        }
        
        # Final safety scrub to make sure no brackets exist in the final request URL
        jina_url = re.sub(r'[\[\]\(\)]', '', jina_url)
        
        resp = requests.get(jina_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            print(f"✅ Jina fetch success for: {clean_target}")
            return resp.text
        print(f"⚠️ Jina fetch failed. Status: {resp.status_code}")
        return ""
    except Exception as e:
        print(f"💥 Jina fetch exception: {e}")
        return ""
