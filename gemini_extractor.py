"""
Uses Groq API (free, fast) to extract job details from notification pages.
Uses Jina AI for free web page fetching.
"""

import os
import json
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def extract_job_details(title_or_context: str, url: str) -> dict:
    sanitized_url = _sanitize_url(url)
    page_text = _fetch_page(sanitized_url)
    context_data = page_text[:2000] if page_text else "No page content found."

    prompt = f"""You are an expert Indian Government Job Recruitment Analyst.

Input Title: {title_or_context}
URL: {sanitized_url}
Page Content: {context_data}

Extract job details and return ONLY a JSON object, no markdown, no extra text:

{{
    "job_title": "full recruitment name",
    "organization": "exact hiring authority",
    "post_name": "specific designation",
    "total_vacancies": "exact count e.g. 500 Posts",
    "qualification": "specific degree required",
    "salary": "exact salary in INR e.g. Rs. 56100-177500",
    "age_limit": "e.g. 18-30 Years",
    "application_fee": "e.g. Gen/OBC: Rs.100, SC/ST: Free",
    "job_profile_description": "2-3 line Hindi-English summary",
    "start_date": "application start date",
    "last_date": "last date in DD Month YYYY",
    "exam_date": "exam date if mentioned",
    "official_apply_link": "direct apply link or {sanitized_url}",
    "selection_process": "e.g. Written Test, Interview",
    "job_type": "Permanent/Contractual/Temporary",
    "location": "job location or All India"
}}

Rules:
- Use EXACT numbers, no generic phrases
- If not found, use empty string
- Return ONLY the JSON object"""

    clean_raw_title = str(title_or_context).split('|')[0].replace("Title:", "").strip()
    fallback_data = {
        "job_title": clean_raw_title if len(clean_raw_title) > 5 else "Government Recruitment Alert",
        "organization": "Central / State Department",
        "post_name": clean_raw_title,
        "total_vacancies": "Check Notification",
        "qualification": "Graduate Degree / Diploma",
        "salary": "Rs. 44,900 - Rs. 1,42,400 (7th Pay Commission)",
        "age_limit": "18-30 Years (Relaxation as per rules)",
        "application_fee": "Gen/OBC: Rs. 25-100 | SC/ST/Women: Free",
        "job_profile_description": "Sarkari naukri ka mauka! Details official link par dekhein.",
        "start_date": "Available Now",
        "last_date": "Check Official Link",
        "exam_date": "",
        "official_apply_link": sanitized_url or "https://upsc.gov.in",
        "selection_process": "Written Test / Interview",
        "job_type": "Permanent",
        "location": "All India"
    }

    if not GROQ_API_KEY:
        return fallback_data

    for attempt in range(3):
        try:
            resp = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 800
                },
                timeout=25
            )

            if resp.status_code == 429:
                wait = (attempt + 1) * 10
                print(f"⏳ Groq Rate Limit. Waiting {wait}s...")
                time.sleep(wait)
                continue

            if not resp.ok:
                print(f"⚠️ Groq Error: {resp.status_code} — {resp.text}")
                return fallback_data

            text = resp.json()["choices"][0]["message"]["content"].strip()

            # Clean markdown if present
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            parsed = json.loads(text)

            # Force correct apply link
            bad_links = ["", "#", "https://upsc.gov.in", "https://ssc.gov.in"]
            if not parsed.get("official_apply_link") or parsed.get("official_apply_link") in bad_links:
                parsed["official_apply_link"] = sanitized_url

            print(f"✅ Groq extraction success!")
            return parsed

        except json.JSONDecodeError:
            print("💥 JSON parse failed. Using fallback.")
            return fallback_data
        except Exception as e:
            print(f"💥 Attempt {attempt+1} failed: {e}")
            time.sleep(5)

    return fallback_data


def _sanitize_url(url: str) -> str:
    if not url:
        return ""
    clean = str(url).strip()
    clean = re.sub(r'[\[\]\(\)]', '', clean)
    found = re.findall(r'https?://[^\s,]+', clean)
    if found:
        return found[-1]
    return clean


def _fetch_page(url: str) -> str:
    if not url or url == "#" or "javascript" in url.lower() or url.lower().endswith(".pdf"):
        return ""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, headers={"Accept": "text/plain", "X-No-Cache": "true"}, timeout=20)
        if resp.status_code == 200:
            print(f"✅ Jina fetch success: {url}")
            return resp.text[:2000]
        return ""
    except Exception as e:
        print(f"💥 Jina fetch failed: {e}")
        return ""
