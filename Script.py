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

# Cloudflare APIs https://developers.cloudflare.com/api/operations/waf-rules-update-a-waf-rule <-everything what you need to know!
API_URL_JS_CHALLENGE = 'https://api.cloudflare.com/client/v4/zones/ZONE_ID/rulesets/PACKAGE_ID/rules/IDENTIFIER'
API_URL_MANAGED_CHALLENGE = 'https://api.cloudflare.com/client/v4/zones/ZONE_ID/rulesets/PACKAGE_ID/rules/IDENTIFIER'

# Credentials for Cloudflare, here you can get API KEY -> https://dash.cloudflare.com/profile/api-tokens Use Global API Key!!!, Use Cloudflare email 
API_EMAIL = os.getenv('CLOUDFLARE_ACCOUNT_EMAIL')
API_KEY = os.getenv('CLOUDFLARE_GLOBAL_KEY')

URL = os.getenv('WEBSITE_URL') # Your URL
IP_SERVER = os.getenv('WEBSITE_SERVER_IP') # To check if server is online, vector that checks if website may have a DDoS attack
TIMEOUT = 5 # Setup your custom timeout, in my case 5 is perfect, you can use higher timeout if you have crappy hosting (it is important to know which value is not normal, in my case it is 5 seconds, you can make simple script to check it out)
BREAK_TIME = 3600 # Time between turning on, and off rules in seconds, usually DDoS attack last around 20 minutes, but I prefer to setup 60 min. 
DELAY_TIME = 1 # Setup delay between requests in seconds, remember too many requests in short time might trigger default Cloudflare WAF

cloudflare_headers = {
    'X-Auth-Email': API_EMAIL,
    'X-Auth-Key': API_KEY,
    'Content-Type': 'application/json'
}

bypass_key_headers = {
    "User-Agent": 'secret-user-agent', # Custom user agent to bypass Cloudflare WAF (You don't have to use it)
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

# Timeout checker with info about time response via Discord webhook, I like SPAM
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

# Main function that will trigger everything if timeout will be detected 
def ddos():
    try:
        ping = ping3.ping(IP_SERVER) # Ping server to check if this is DDoS attack, or just server is dead
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

# We are going to turn ON two rules JS Challenge, and Managed Challenge. (It is better to use two rules if you use more complex expressions, but this is up to you)
def turn_on_cloudflare_rule_js_challenge():
    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",
        "expression": "(http.host contains \"example.com\" )" # Make own expression, or at least just change example.com to your website
    }
    update_cloudflare_rule(API_URL_JS_CHALLENGE, payload)

def turn_on_cloudflare_rule_managed_challenge():
    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge",
        "expression": "(http.host contains \"example.com\" )" # Make own expression, or at least just change example.com to your website
    }
    update_cloudflare_rule(API_URL_MANAGED_CHALLENGE, payload)

# You can't just turn OFF Cloudflare role lol, so it is setup in this way that nobody will trigger it, you can delete rule, and create it again, but in my opinion this is simpler option
def turn_off_cloudflare_rule_js_challenge():
    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",
        "expression": "(ip.src eq 255.255.255.255)" # No one will trigger this rule 
    }
    update_cloudflare_rule(API_URL_JS_CHALLENGE, payload)

def turn_off_cloudflare_rule_managed_challenge():
    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge",
        "expression": "(ip.src eq 255.255.255.255)" # No one will trigger this rule 
    }
    update_cloudflare_rule(API_URL_MANAGED_CHALLENGE, payload)

# Alert your users about DDoS attack, message is embedded
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

# Everythings is in loop with extra alerts if something is not ok Discord webhook/text in console
if __name__ == '__main__':
    while True:
        try:
            send_request()
        except Exception as error:
            error_message = f'❗️ An error occurred ERROR: \n{str(error)}'
            print(error_message)
            send_log(error_message)
            time.sleep(60)  # Wait for 60 seconds before retrying
