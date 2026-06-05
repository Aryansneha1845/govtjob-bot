"""
Sends clean, professional job alerts to Telegram.
"""
import re
import requests
import logging
log = logging.getLogger(__name__)

SITE_DOMAIN = "https://deshnaukri.in"

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
        org        = job.get('organization') or job.get('source') or 'Government Department'
        title      = job.get('job_title') or job.get('post_name') or job.get('title') or 'Government Job'
        vacancies  = job.get('total_vacancies') or 'Check Notification'
        eligibility= job.get('qualification') or 'Check Notification PDF'
        last_date  = job.get('last_date') or 'Apply Soon'
        salary     = job.get('salary') or 'As Per Govt Rules'
        age_limit  = job.get('age_limit') or ''
        app_fee    = job.get('application_fee') or ''
        selection  = job.get('selection_process') or ''
        location   = job.get('location') or ''
        description= job.get('job_profile_description') or ''

        apply_link = job.get('official_apply_link') or job.get('url') or '#'
        pdf_link   = job.get('url') or '#'

        # Detail page URL generate karo
        raw_title = job.get('job_title') or job.get('title') or 'job'
        slug = re.sub(r'[^a-z0-9]+', '-', raw_title.lower())[:60].strip('-')
        detail_url = job.get('detailed_page_url') or f"{SITE_DOMAIN}/jobs/{slug}.html"

        lines = [
            f"🎯 <b>{org} — New Recruitment {2026}</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📌 <b>Post:</b> {title}",
            f"🔢 <b>Vacancies:</b> {vacancies}",
            f"🎓 <b>Eligibility:</b> {eligibility}",
        ]

        if age_limit:
            lines.append(f"🎂 <b>Age Limit:</b> {age_limit}")
        if salary:
            lines.append(f"💰 <b>Salary:</b> {salary}")
        if app_fee:
            lines.append(f"📝 <b>Form Fee:</b> {app_fee}")
        if selection:
            lines.append(f"📌 <b>Selection:</b> {selection}")
        if location:
            lines.append(f"📍 <b>Location:</b> {location}")

        lines += [
            f"📅 <b>Last Date:</b> <u>{last_date}</u>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        if description:
            lines += [f"ℹ️ <i>{description}</i>", ""]

        lines += [
            "👇 <b>Important Links:</b>",
            f"📖 <a href='{detail_url}'><b>Full Details — DeshNaukri</b></a> 🌐",
            f"🚀 <a href='{apply_link}'><b>Apply Online</b></a>",
            f"📥 <a href='{pdf_link}'><b>Official Notification PDF</b></a>",
            "",
            "🔔 <i>Sarkari Naukri updates ke liye channel join karein!</i>",
            "",
            "#SarkariNaukri #GovtJobs #JobAlert #DeshNaukri"
        ]

        return "\n".join(lines)
