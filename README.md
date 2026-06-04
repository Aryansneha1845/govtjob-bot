# 🏛 Government Job Alert Bot

Telegram bot that monitors **SSC, UPSC, RRB** and automatically posts new job notifications to your channel.

---

## 📁 Project Structure

```
govtjob-bot/
├── bot.py              ← Main entry point
├── database.py         ← SQLite (stores seen jobs)
├── telegram_poster.py  ← Formats & sends Telegram messages
├── scrapers/
│   ├── ssc.py          ← SSC scraper
│   ├── upsc.py         ← UPSC scraper
│   └── rrb.py          ← RRB scraper
├── data/               ← Auto-created (jobs.db stored here)
├── logs/               ← Auto-created (bot.log stored here)
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup (Step by Step)

### Step 1 — Create a Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `GovtJobAlertBot`)
4. Copy the **Bot Token** it gives you

### Step 2 — Create a Telegram Channel

1. Create a new Telegram channel (e.g. `@govtjobalerts2026`)
2. Add your bot as **Admin** to the channel
3. Note down the channel username (e.g. `@govtjobalerts2026`)

### Step 3 — Clone & Install

```bash
# Clone or copy the project folder
cd govtjob-bot

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 4 — Configure .env

```bash
# Copy the example file
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
```

Open `.env` and fill in:
```
TELEGRAM_BOT_TOKEN=your_actual_bot_token
TELEGRAM_CHANNEL_ID=@your_channel_username
```

### Step 5 — Run the Bot

```bash
python bot.py
```

You'll see:
```
2026-06-04 10:00:00 [INFO] 🚀 GovtJob Alert Bot started
2026-06-04 10:00:00 [INFO]    Channel  : @govtjobalerts2026
2026-06-04 10:00:00 [INFO]    Interval : every 30 min
2026-06-04 10:00:00 [INFO] 🔍 Checking all sources...
2026-06-04 10:00:02 [INFO]   SSC: 3 job(s) found
2026-06-04 10:00:02 [INFO]   ✅ Posted: SSC CGL 2026 Notification
```

---

## 🚀 Keep Bot Running 24/7

### Option A — Windows (Task Scheduler)
- Search "Task Scheduler" → Create Basic Task
- Action: Start a program → `python bot.py`
- Trigger: At startup

### Option B — Linux/VPS (systemd)
```bash
sudo nano /etc/systemd/system/govtjobbot.service
```
Paste:
```ini
[Unit]
Description=Govt Job Alert Bot
After=network.target

[Service]
WorkingDirectory=/path/to/govtjob-bot
ExecStart=/path/to/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl enable govtjobbot
sudo systemctl start govtjobbot
```

### Option C — Free Cloud (Railway.app)
1. Push code to GitHub (don't include `.env`!)
2. Go to railway.app → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard
4. Done — runs 24/7 for free

---

## ➕ Adding More Sources

1. Create a new file in `scrapers/` (e.g. `scrapers/ibps.py`)
2. Add a `scrape_ibps()` function that returns a list of job dicts
3. Register it in `bot.py`:
```python
from scrapers.ibps import scrape_ibps

SCRAPERS = {
    "SSC":  scrape_ssc,
    "UPSC": scrape_upsc,
    "RRB":  scrape_rrb,
    "IBPS": scrape_ibps,   # ← add here
}
```

### Job dict format:
```python
{
    "id":        "unique_string",   # md5 hash recommended
    "title":     "Job Title",
    "source":    "IBPS",
    "url":       "https://...",
    "last_date": "15 July 2026",
    "posts":     "5000",            # optional
}
```

---

## 📢 Telegram Post Preview

```
🚨 New Government Job Alert!

🏛  Organization: SSC
📋 Post: CGL 2026 Notification Released
📊 Vacancies: 14582
📅 Last Date: 15 July 2026

🔗 Official Notification

#GovtJobs #Sarkari #Recruitment
```

---

## ⚠️ Notes

- If a website redesigns, the scraper selectors may need updating
- Check `logs/bot.log` for errors
- Bot token & channel ID ko **kabhi GitHub par push mat karo**
