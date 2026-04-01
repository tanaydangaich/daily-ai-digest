import time
import requests
from bot.config import DISCORD_WEBHOOK_URL

WEBHOOK_POST_URL = DISCORD_WEBHOOK_URL + "?wait=true"


def post_to_discord(content):
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    message_ids = []

    for i, chunk in enumerate(chunks):
        payload = {"content": f"🤖 **Weekly AI News Digest** — Top 10 Stories\n\n{chunk}" if i == 0 else chunk}
        r = requests.post(WEBHOOK_POST_URL, json=payload)
        if r.status_code not in (200, 204):
            print(f"Discord error: {r.status_code} {r.text}")
            return None
        if r.status_code == 200:
            data = r.json()
            message_ids.append(data.get("id"))
        time.sleep(1)

    return message_ids
