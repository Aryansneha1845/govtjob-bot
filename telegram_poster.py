import requests
import json
import logging

log = logging.getLogger(__name__)

class TelegramPoster:
    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.api_url = f"https://api.telegram.org/bot{token}"

    def post(self, job_data):
        """
        Sends job alert to Telegram using robust HTML parse mode.
        HTML mode is highly stable and never crashes on brackets, slashes, or dashes.
        """
        if not self.token or not self.channel_id:
            log.error("❌ Telegram posting credentials missing in environment.")
            return False

        # Extract values safely
        org = self.clean_html(job_data.get('organization', 'Government Department'))
        title = self.clean_html(job_data.get('job_title', 'New Notification Alert'))
        vacancies = self.clean_html(job_data.get('total_vacancies', 'Check Official Link'))
        last_date = self.clean_html(job_data.get('last_date', 'Apply Soon'))
        detailed_url = job_data.get('detailed_page_url', 'https://deshnaukri.netlify.app')

        # 🎯 High engagement HTML captioned format
        caption = (
            f"🎯 <b>New Job Recruitment Alert!</b>\n\n"
            f"🏢 <b>Organization:</b> {org}\n"
            f"💼 <b>Post Name:</b> {title}\n"
            f"📊 <b>Vacancies:</b> {vacancies}\n"
            f"⏳ <b>Last Date:</b> {last_date}\n\n"
            f"📝 <b>Syllabus & Details:</b> <a href='{detailed_url}'>Click Here to Read Full Details</a>\n\n"
            f"📢 <b>Join:</b> @DeshNaukri"
        )

        # Interactive Inline Keyboard Link
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔗 View Details & Apply", "url": detailed_url}
                ]
            ]
        }

        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.channel_id,
                "text": caption,
                "parse_mode": "HTML",  # 🔥 Using HTML instead of Markdown to prevent character crashes
                "reply_markup": json.dumps(inline_keyboard),
                "disable_web_page_preview": False
            }
            
            response = requests.post(url, json=payload, timeout=20)
            res_json = response.json()
            
            if response.status_code == 200 and res_json.get("ok"):
                return True
            else:
                log.error(f"❌ Telegram API Rejected payload: {res_json}")
                return False
                
        except Exception as e:
            log.error(f"💥 Failed sending payload to Telegram API: {e}")
            return False

    def clean_html(self, text):
        """Helper to escape HTML tags to avoid parsing errors."""
        if not text:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```
eof

---
