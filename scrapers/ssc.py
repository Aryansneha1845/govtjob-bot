import requests
from bs4 import BeautifulSoup
import logging
import hashlib

log = logging.getLogger(__name__)

def scrape_ssc():
    # SSC ka standard live notice board archival board URL
    url = "https://ssc.gov.in" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    log.info(f"🌐 [SSC Deep Scraper] Scanning Portal: {url}")
    jobs = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                title_text = link.get_text(strip=True)
                title_lower = title_text.lower()
                
                # Sirf real notification keywords target karenge
                if len(title_text) > 20 and any(k in title_lower for k in ["notice", "cgl", "chsl", "gd", "mts", "recruitment", "examination"]):
                    if not any(sk in title_lower for sk in ["archive", "calendar", "tentative"]):
                        
                        href = link['href']
                        final_url = href if href.startswith('http') else f"https://ssc.gov.in{href}"
                        
                        # 🚀 SSC DEEP DETAILS CONTEXT PRE-PARSING:
                        # Hum title ke andar se hi thoda intelligence context nikal kar Gemini ko pass karenge
                        job_id = hashlib.md5(title_text.encode()).hexdigest()[:12]
                        
                        jobs.append({
                            "id": f"ssc_{job_id}",
                            "title": title_text,
                            "url": final_url,
                            "raw_context": f"This is an official SSC Recruitment Notification titled: {title_text}. Direct Link: {final_url}"
                        })
    except Exception as e:
        log.error(f"💥 [SSC Scraper] Failure: {e}")
        
    unique_jobs = {j['id']: j for j in jobs}.values()
    return list(unique_jobs)[:5]