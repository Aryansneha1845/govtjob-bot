import requests
from bs4 import BeautifulSoup
import logging
import hashlib

log = logging.getLogger(__name__)

def scrape_upsc():
    url = "https://upsc.gov.in/whats-new"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    log.info(f"🌐 [UPSC Deep Scraper] Scanning Notice Board: {url}")
    jobs = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return jobs
            
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        
        ignore_keywords = ["active examination", "forthcoming", "lateral recruitment", "online recruitment application", "ora"]
        
        for link in links:
            title_text = link.get_text(strip=True)
            title_lower = title_text.lower()
            
            if len(title_text) > 15 and any(k in title_lower for k in ["exam", "recruitment", "advertisement", "notice", "vacancy"]):
                if not any(ik in title_lower for ik in ignore_keywords):
                    
                    # 🚀 FIX 1: URL Handling ekdum tight kar di
                    notice_page_url = link['href']
                    if not notice_page_url.startswith('http'):
                        if notice_page_url.startswith('/'):
                            notice_page_url = f"https://upsc.gov.in{notice_page_url}"
                        else:
                            notice_page_url = f"https://upsc.gov.in/{notice_page_url}"
                    
                    # DEEP SCRAPING START
                    try:
                        log.info(f"🕵️‍♂️ Deep Scraping Inner Page for: {title_text[:30]}...")
                        inner_res = requests.get(notice_page_url, headers=headers, timeout=10)
                        if inner_res.status_code == 200:
                            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                            inner_links = inner_soup.find_all('a', href=True)
                            
                            final_direct_url = notice_page_url 
                            
                            for il in inner_links:
                                il_text = il.get_text(strip=True).lower()
                                il_href = il['href']
                                
                                if ".pdf" in il_href.lower() or "apply" in il_text or "upsconline" in il_href.lower():
                                    # 🚀 FIX 2: Inner page relative links handling
                                    if not il_href.startswith('http'):
                                        if il_href.startswith('/'):
                                            final_direct_url = f"https://upsc.gov.in{il_href}"
                                        else:
                                            final_direct_url = f"https://upsc.gov.in/{il_href}"
                                    else:
                                        final_direct_url = il_href
                                    break 
                    except Exception as inner_err:
                        log.warning(f"⚠️ Inner page deep scrape failed, using fallback: {inner_err}")
                        final_direct_url = notice_page_url

                    job_id = hashlib.md5(title_text.encode()).hexdigest()[:12]
                    jobs.append({
                        "id": f"upsc_{job_id}",
                        "title": title_text,
                        "url": final_direct_url
                    })
                
    except Exception as e:
        log.error(f"💥 [UPSC Scraper] Error: {e}")
        
    unique_jobs = {j['id']: j for j in jobs}.values()
    return list(unique_jobs)[:5]