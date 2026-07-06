cat > test.py << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
import requests, json
token = os.getenv('TELEGRAM_BOT_TOKEN')
channel = os.getenv('TELEGRAM_CHANNEL_ID')
amazon = 'https://www.amazon.in/s?k=sarkari+exam+books&tag=deshnaukri-21'
buttons = [[{'text': 'Full Details', 'url': 'https://aryansneha1845.github.io/govtjob-bot'}, {'text': 'Apply Now', 'url': 'https://upsc.gov.in'}], [{'text': 'Study Books Amazon', 'url': amazon}]]
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': channel, 'text': 'Test post with Amazon affiliate button!', 'reply_markup': json.dumps({'inline_keyboard': buttons})})
print(r.json())
EOF
python test.py
