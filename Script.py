import time
import requests
import json
import ping3
import os
from datetime import datetime
from requests.exceptions import RequestException, Timeout

# Choose notification method: 'discord', 'telegram', or 'both'
NOTIFICATION_METHOD = os.getenv('NOTIFICATION_METHOD', 'both').lower()

# Discord webhooks DDoS alert/logs
DISCORD_WEBHOOK_ALERT = os.getenv('DISCORD_WEBHOOK_ALERT')
DISCORD_WEBHOOK_LOGS = os.getenv('DISCORD_WEBHOOK_LOGS')

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID_ALERT = os.getenv('TELEGRAM_CHAT_ID_ALERT')
TELEGRAM_CHAT_ID_LOGS = os.getenv('TELEGRAM_CHAT_ID_LOGS')

# Cloudflare APIs
API_URL_JS_CHALLENGE = os.getenv('API_URL_JS_CHALLENGE')
API_URL_MANAGED_CHALLENGE = os.getenv('API_URL_MANAGED_CHALLENGE')

# Cloudflare credentials
API_EMAIL = os.getenv('CLOUDFLARE_ACCOUNT_EMAIL')
API_KEY = os.getenv('CLOUDFLARE_GLOBAL_KEY')

URL = os.getenv('WEBSITE_URL')
IP_SERVER = os.getenv('WEBSITE_SERVER_IP')
TIMEOUT = 5
BREAK_TIME = 3600
DELAY_TIME = 1

cloudflare_headers = {
    'X-Auth-Email': API_EMAIL,
    'X-Auth-Key': API_KEY,
    'Content-Type': 'application/json'
}

bypass_key_headers = {
    "User-Agent": 'secret-user-agent',
}

def send_discord_webhook(webhook_url, content):
    if NOTIFICATION_METHOD in ['discord', 'both']:
        try:
            data = {'content': content}
            response = requests.post(webhook_url, json=data)
            response.raise_for_status()
        except RequestException as e:
            print(f"Failed to send Discord webhook: {str(e)}")

def send_telegram_message(chat_id, message):
    if NOTIFICATION_METHOD in ['telegram', 'both']:
        try:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            response = requests.post(telegram_url, json=payload)
            response.raise_for_status()
        except RequestException as e:
            print(f"Failed to send Telegram message: {str(e)}")

def send_alert(message):
    send_discord_webhook(DISCORD_WEBHOOK_ALERT, message)
    send_telegram_message(TELEGRAM_CHAT_ID_ALERT, message)

def send_log(message):
    send_discord_webhook(DISCORD_WEBHOOK_LOGS, message)
    send_telegram_message(TELEGRAM_CHAT_ID_LOGS, message)

def send_request():
    while True:
        try:
            time.sleep(DELAY_TIME)
            start_time = time.time()
            response = requests.get(URL, timeout=TIMEOUT, headers=bypass_key_headers)
            response.raise_for_status()
            current_time = datetime.now().strftime('%m-%d %H:%M:%S')
            response_time = time.time() - start_time
            response_time_formatted = '{:.3f}'.format(response_time)
            
            send_log(f'🏓 Response time: {response_time_formatted} seconds, date: {current_time}')

        except Timeout:
            send_log('⚠️ Request timed out!')
            ddos()
            time.sleep(BREAK_TIME)

        except RequestException as e:
            send_log(f'⚠️ Request failed: {str(e)}')
            ddos()
            time.sleep(BREAK_TIME)

def ddos():
    try:
        ping = ping3.ping(IP_SERVER)
        if ping is None:
            raise Exception("Server is not responding to ping")
    except Exception:
        send_log('😥 VPS is just down! **Taking a break for 60 minutes**')
        time.sleep(BREAK_TIME)
        return

    send_alert('🔥 Seems like forum is under DDoS, confirmation from another source!')
    send_log('🔥🧱 Requesting update to turn **ON** Cloudflare WAF')
    turn_on_cloudflare_rule_managed_challenge()
    turn_on_cloudflare_rule_js_challenge()
    send_alert_message()
    send_log('⏱️ **Taking a break for 60 minutes**')
    time.sleep(BREAK_TIME)
    send_log('🔥🧱 Requesting update to turn **OFF** Cloudflare WAF')
    turn_off_cloudflare_rule_managed_challenge()
    turn_off_cloudflare_rule_js_challenge()
    send_log('🟢 **Starting monitoring again**')

def update_cloudflare_rule(url, payload):
    try:
        response = requests.patch(url, json=payload, headers=cloudflare_headers)
        response.raise_for_status()
        send_log(f'🆙 WAF was updated **{payload["description"]}**, status code: {response.status_code}')
    except RequestException as e:
        send_log(f'❌ Failed to update WAF rule **{payload["description"]}**: {str(e)}')

def turn_on_cloudflare_rule_js_challenge():
    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",
        "expression": "(http.host contains \"example.com\" )"
    }
    update_cloudflare_rule(API_URL_JS_CHALLENGE, payload)

def turn_on_cloudflare_rule_managed_challenge():
    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge",
        "expression": "(http.host contains \"example.com\" )"
    }
    update_cloudflare_rule(API_URL_MANAGED_CHALLENGE, payload)

def turn_off_cloudflare_rule_js_challenge():
    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",
        "expression": "(ip.src eq 255.255.255.255)"
    }
    update_cloudflare_rule(API_URL_JS_CHALLENGE, payload)

def turn_off_cloudflare_rule_managed_challenge():
    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge",
        "expression": "(ip.src eq 255.255.255.255)"
    }
    update_cloudflare_rule(API_URL_MANAGED_CHALLENGE, payload)

def send_alert_message():
    discord_message = {
        "embeds": [
            {
                "description": "Access to website might be limited, If you can't connect, try again in a few minutes! We apologize for any inconvenience...",
                "author": {
                    "name": "DDoS Attack Alert for example.com"
                },
                "url": "https://status.example.com/",
                "title": "🟢 Up-Time Status Page ",
                "color": 16753920,
                "image": {
                    "url": "https://cdn.discordapp.com/attachments/886360792381935636/1123725647089504417/Cyber-Criminals-Meme_1-transformed_1.png"
                }
            }
        ],
    }
    telegram_message = "🚨 DDoS Attack Alert! Access to website might be limited. If you can't connect, try again in a few minutes. We apologize for any inconvenience."

    send_discord_webhook(DISCORD_WEBHOOK_ALERT, json.dumps(discord_message))
    send_telegram_message(TELEGRAM_CHAT_ID_ALERT, telegram_message)

if __name__ == '__main__':
    while True:
        try:
            send_request()
        except Exception as error:
            error_message = f'❗️ An error occurred ERROR: \n{str(error)}'
            print(error_message)
            send_log(error_message)
            time.sleep(60)  # Wait for 60 seconds before retrying
