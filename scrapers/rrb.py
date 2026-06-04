import requests
from bs4 import BeautifulSoup
import logging
import hashlib

log = logging.getLogger(__name__)

def scrape_rrb():
    # Indian Railways Recruitment active notification portal
    url = "https://indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,1,304,366,1452"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    log.info(f"🌐 [RRB Deep Scraper] Scanning Railway Board: {url}")
    jobs = []
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Railway board tables ke andar anchor tags hote hain
            table_rows = soup.find_all('tr')
            
            for row in table_rows[:15]: # Top 15 rows check karenge
                links = row.find_all('a', href=True)
                if links:
                    link = links[0]
                    title_text = row.get_text(strip=True)
                    title_lower = title_text.lower()
                    
                    if any(k in title_lower for k in ["vacancy", "circular", "recruitment", "irms", "paramedical", "ntpc", "group"]):
                        href = link['href']
                        final_url = href if href.startswith('http') else f"https://indianrailways.gov.in/railwayboard/{href}"
                        
                        job_id = hashlib.md5(title_text.encode()).hexdigest()[:12]
                        
                        # Row ke andar jo extra text hai (dates, subject), use raw context bana kar bhejenge
                        jobs.append({
                            "id": f"rrb_{job_id}",
                            "title": title_text,
                            "url": final_url,
                            "raw_context": f"Railway Recruitment Board Live Circular. Metadata Text: {title_text}. Official Attachment Link: {final_url}"
                        })
    except Exception as e:
        log.error(f"💥 [RRB Scraper] Failure: {e}")
        
    unique_jobs = {j['id']: j for j in jobs}.values()
    return list(unique_jobs)[:5]