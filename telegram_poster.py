"""
Sends clean, professional job alerts to Telegram.
Only uses pure scraped data.
"""

import requests
import logging

log = logging.getLogger(__name__)


class TelegramPoster:
    API = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, token: str, channel_id: str):
        self.token      = token
        self.channel_id = channel_id

    def post(self, job: dict):
        text = self._format(job)
        url  = self.API.format(token=self.token, method="sendMessage")

        resp = requests.post(url, json={
            "chat_id":                  self.channel_id,
            "text":                     text,
            "parse_mode":               "HTML",
            "disable_web_page_preview": True, 
        }, timeout=10)

        if not resp.ok:
            log.error(f"Telegram error: {resp.text}")
        return resp.ok

    @staticmethod
    def _format(job: dict) -> str:
        org = job.get('organization') or job.get('source') or 'Government Department'
        title = job.get('job_title') or job.get('post_name') or job.get('title')
        
        vacancies = job.get('total_vacancies') or 'Notification Check Karein'
        eligibility = job.get('qualification') or 'Check Notification PDF'
        last_date = job.get('last_date') or 'Apply Soon'
        salary = job.get('salary') or 'As Per Govt Rules'
        
        apply_link = job.get('official_apply_link') or job.get('url') or 'https://google.com'
        pdf_link = job.get('url') or 'https://google.com'

        lines = [
            f"🎯 <b>{org} New Recruitment Update</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📌 <b>Post Name:</b> {title}",
            f"🔢 <b>Total Vacancy:</b> {vacancies}",
            f"🎓 <b>Eligibility:</b> {eligibility}",
            f"💰 <b>Salary:</b> {salary}",
            f"📅 <b>Last Date to Apply:</b> <u>{last_date}</u>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "👇 <b>Important Official Links:</b>",
            f"👉 <a href='{apply_link}'><b>Click Here to Apply Online Form</b></a> 🚀",
            f"👉 <a href='{pdf_link}'><b>Download Official Notification PDF</b></a> 📥",
            "",
            "🔔 <i>Sarkari Naukri updates ke liye channel se jude rahein!</i>",
            "",
            "#SarkariNaukri #GovtJobs #JobAlert #DeshNaukri"
        ]

        return "\n".join(lines)