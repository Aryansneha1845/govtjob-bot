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
        if not self.token or not self.channel_id:
            log.error("❌ Telegram credentials missing!")
            return False

        org       = self.clean(job_data.get('organization', 'Government Department'))
        title     = self.clean(job_data.get('job_title') or job_data.get('title', 'New Recruitment Alert'))
        post      = self.clean(job_data.get('post_name', ''))
        vac       = self.clean(job_data.get('total_vacancies', 'Check Notification'))
        qual      = self.clean(job_data.get('qualification', ''))
        age       = self.clean(job_data.get('age_limit', ''))
        salary    = self.clean(job_data.get('salary', ''))
        fee       = self.clean(job_data.get('application_fee', ''))
        selection = self.clean(job_data.get('selection_process', ''))
        location  = self.clean(job_data.get('location', ''))
        last_date = self.clean(job_data.get('last_date', 'Apply Soon'))
        desc      = self.clean(job_data.get('job_profile_description', ''))
        state_tag = job_data.get('state_tag', '🌐 CENTRAL GOVT JOB')
        apply_link = job_data.get('official_apply_link') or job_data.get('url', '#')
        detail_url = job_data.get('detailed_page_url', 'https://aryansneha1845.github.io/govtjob-bot')
        pdf_url    = job_data.get('pdf_url', '')

        lines = [
            f"<b>{state_tag}</b>",
            f"🎯 <b>{org} — New Recruitment Alert!</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📌 <b>Post:</b> {post or title}",
            f"🔢 <b>Vacancies:</b> {vac}",
        ]

        if qual:
            lines.append(f"🎓 <b>Eligibility:</b> {qual}")
        if age:
            lines.append(f"🎂 <b>Age Limit:</b> {age}")
        if salary:
            lines.append(f"💰 <b>Salary:</b> {salary}")
        if fee:
            lines.append(f"📝 <b>Form Fee:</b> {fee}")
        if selection:
            lines.append(f"📌 <b>Selection:</b> {selection}")
        if location:
            lines.append(f"📍 <b>Location:</b> {location}")

        lines += [
            f"📅 <b>Last Date:</b> <u>{last_date}</u>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        if desc:
            lines += [f"ℹ️ <i>{desc}</i>", ""]

        lines += [
            "👇 <b>Important Links:</b>",
            f"📖 <a href='{detail_url}'>Full Details — DeshNaukri</a> 🌐",
            f"🚀 <a href='{apply_link}'>Apply Online / Official Notification</a>",
            "",
            "🔔 <i>Sarkari Naukri updates ke liye @DeshNaukri join karein!</i>",
            "#SarkariNaukri #GovtJobs #JobAlert #DeshNaukri"
        ]

        caption = "\n".join(lines)

        # Inline buttons — PDF button bhi add karo agar available ho
        buttons = [
            {"text": "🌐 Full Details", "url": detail_url},
            {"text": "✅ Apply Now", "url": apply_link}
        ]
        if pdf_url:
            buttons.append({"text": "📥 Download PDF", "url": pdf_url})

        inline_keyboard = {"inline_keyboard": [buttons]}

        try:
            resp = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.channel_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(inline_keyboard),
                    "disable_web_page_preview": False
                },
                timeout=20
            )
            res = resp.json()
            if resp.status_code == 200 and res.get("ok"):
                return True
            else:
                log.error(f"❌ Telegram rejected: {res}")
                return False
        except Exception as e:
            log.error(f"💥 Telegram error: {e}")
            return False

    @staticmethod
    def clean(text):
        if not text:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
