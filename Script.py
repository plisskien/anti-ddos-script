import time
import requests
import json
import ping3
from datetime import datetime, timedelta
from requests.exceptions import Timeout

# Discord webhooks DDoS alert/logs
WEBHOOK_ALERT = 'DISCORD_WEBHOOK_ALERT'
WEBHOOK_LOGS = 'DISCORD_WEBHOOK_LOGS'

# Cloudflare APIs https://developers.cloudflare.com/api/operations/waf-rules-update-a-waf-rule <-everything what you need to know!
API_URL_JS_CHALLENGE = 'https://api.cloudflare.com/client/v4/zones/ZONE_ID/rulesets/PACKAGE_ID/rules/IDENTIFIER'
API_URL_MANAGED_CHALLENGE = 'https://api.cloudflare.com/client/v4/zones/ZONE_ID/rulesets/PACKAGE_ID/rules/IDENTIFIER'

# Credentials for Cloudflare, here you can get API KEY -> https://dash.cloudflare.com/profile/api-tokens Use Global API Key!!!, Use Cloudflare email 
API_EMAIL = 'CLOUDFLARE_ACCOUNT_EMAIL'
API_KEY = 'CLOUDFLARE_GLOBAL_KEY'

URL = 'WEBSITE_URL' # Your URL
IP_SERVER = 'WEBSITE_SERVER_IP' # To check if server is online, vector that checks if website may have a DDoS attack, look at line 57
TIMEOUT = 5 # Setup your custom timeout, in my case 5 is perfect, you can use higer timeout if you have crappy hosting (it is important to know which value is not normal, in my case it is 5 seconds, you can make simple script to check it out)
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

# Timeout checker with info about time response via Discord webhook, I like SPAM

def send_request():
    while True:
        try:
            time.sleep(DELAY_TIME) 
            start_time = time.time() 
            response = requests.get(URL, timeout=TIMEOUT, headers=bypass_key_headers) 
            current_time = datetime.now().strftime('%m-%d %H:%M:%S')
            end_time = time.time()  
            response_time = end_time - start_time  
            
            send_discord_webhook_logs(f'🏓 Response time: {response_time} seconds, date: {current_time}')

        except Timeout:
            send_discord_webhook_logs('⚠️ Request timed out!')
            ddos()
            time.sleep(BREAK_TIME)

# Main function that will trigger everything if timeout will be detected 

def ddos():  
        try:
            ping = ping3.ping(IP_SERVER) # Ping server to check if this is DDoS attack, or just server is dead
            if ping is None:
                raise Exception
        except Exception:
            send_discord_webhook_logs('😥 VPS is just down! **Taking a break for 60 minutes**')
            time.sleep(BREAK_TIME) 
            return
        # If there is timeout, and server is up this part will be triggered 
        if True:
            send_discord_webhook_logs('🔥 Seems like forum is under DDoS, confirmation from another source!')
            send_discord_webhook_logs('🔥🧱 Requesting update to turn **ON** Cloudflare WAF')
            turn_on_cloudflare_rule_managed_challenge()
            turn_on_cloudflare_rule_js_challenge()
            send_discord_webhook_alert()
            send_discord_webhook_logs('⏱️ **Taking a break for 60 minutes**')
            time.sleep(BREAK_TIME) 
            send_discord_webhook_logs('🔥🧱 Requesting update to turn **OFF** Cloudflare WAF')
            turn_off_cloudflare_rule_managed_challenge()
            turn_off_cloudflare_rule_js_challenge()
            send_discord_webhook_logs('🟢 **Starting monitoring again**')
            send_request()

# We are going to turn ON two rules JS Challenge, and Managed Challenge. (It is better to use two rules if you use more complex expressions, but this is up to you)

def turn_on_cloudflare_rule_js_challenge():

    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",  # Make own expression, or at least just change example.exe to your website, if you use more complex expressions you can use both rules, but if you want to use simple rule e.g. Managed Challenge for example.com you can use one rule
        "expression": "(http.host contains \"example.com\" )"
    }
    
    response = requests.patch(API_URL_JS_CHALLENGE, json=payload, headers=cloudflare_headers)
    send_discord_webhook_logs('🆙 WAF was updated **JS Challenge**, status code: ' + str(response.status_code))

def turn_on_cloudflare_rule_managed_challenge():

    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge", # Make own expression, or at least just change example.exe to your website, if you use more complex expressions you can use both rules, but if you want to use simple rule e.g. Managed Challenge for example.com you can use one rule
        "expression": "(http.host contains \"example.com\" )"
    }

    response = requests.patch(API_URL_MANAGED_CHALLENGE, json=payload, headers=cloudflare_headers)
    send_discord_webhook_logs('🆙 WAF was updated **Managed Challenge**, status code: ' + str(response.status_code))

# You can't just turn OFF Cloudflare role lol, so it is setup in this way that nobody will trigger it, you can delete rule, and create it again, but in my opinion this is simpler option

def turn_off_cloudflare_rule_js_challenge():
    payload = {
        "action": "js_challenge",
        "description": "JS Challenge",
        "expression": "(ip.src eq 255.255.255.255)" # No one will trigger this rule 
    }

    response = requests.patch(API_URL_JS_CHALLENGE, json=payload, headers=cloudflare_headers)
    send_discord_webhook_logs('🆙 WAF was updated **JS Challenge**, status code: ' + str(response.status_code))

def turn_off_cloudflare_rule_managed_challenge():
    payload = {
        "action": "managed_challenge",
        "description": "Managed Challenge",
        "expression": "(ip.src eq 255.255.255.255)" # No one will trigger this rule 
    }

    response = requests.patch(API_URL_MANAGED_CHALLENGE, json=payload, headers=cloudflare_headers)
    send_discord_webhook_logs('🆙 WAF was updated **Managed Challenge**, status code: ' + str(response.status_code))

# Alert your users about DDoS attack, message is embedded

def send_discord_webhook_alert():
    send_discord_webhook_logs('📢 Sending Discord Webhook about DDoS attack!')
    data = {
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
    response = requests.post(WEBHOOK_ALERT, json=data)

def send_discord_webhook_logs(content):
    data = {
        'content': content
    }
    response = requests.post(WEBHOOK_LOGS, json=data)

# Everythings is in loop with extra alerts if something is not ok Discord webhook/text in console

if __name__ == '__main__':
    while True:
        try:
            send_request()
        except Exception as error:
            error_message = f'❗️ An error occurred ERROR: \n{str(error)}'
            print(f'An error occurred ERROR: \n{str(error)}')
            send_discord_webhook_logs(error_message)
            continue