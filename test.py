import os
from dotenv import load_dotenv
load_dotenv()
import requests
token = os.getenv('TELEGRAM_BOT_TOKEN')
channel = os.getenv('TELEGRAM_CHANNEL_ID')
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': channel, 'text': 'Bot test message! DeshNaukri Bot is LIVE!'})
print(r.json())