# Anti-DDoS Python Script

This is a simple Python script designed to detect timeouts and enable Cloudflare custom WAF rules. The script was created to help users who prefer to have their Cloudflare WAF off when not needed.

## Prerequisites

- Cloudflare free plan
- Another server with SSH access to host the script
- Python installed on the server (you can also host it on the same server, but it's not recommended)

## FAQ

**Q: How does it work?**

A: The script sends a request every second to detect timeouts (default timeout is 5 seconds). It then pings the server IP to check if the server is up. If the server is down, it waits for 60 minutes and repeats the process. If the server is up but there is downtime, it indicates a potential DDoS attack. The script then uses the Cloudflare API to update WAF rules (examples provided in the code). After 60 minutes, it turns off the Cloudflare rules.

**Q: Is it tested and functional?**

A: Yes, it works effectively with a stable hosting provider. If your hosting provider experiences instability, the script might trigger itself even without a DDoS attack.

**Q: Can I customize the DDoS detection method?**

A: Yes, you can modify the script to use your own DDoS detection method. The provided timeout-based method is effective for stable VPS setups.

## Screenshots

Downtime during DDoS attacks:
![downtime](https://github.com/plisskien/anti_ddos_script/assets/29129602/bc99f130-a490-4e95-b22c-e40a560950df)

High CPU usage during server downtime:
![ddps-dead-server](https://github.com/plisskien/anti_ddos_script/assets/29129602/7e3b5af8-63d9-40aa-9714-bff44224e5be)

Normal CPU usage during non-attack period:
![ddos-not-dead-server](https://github.com/plisskien/anti_ddos_script/assets/29129602/298e7365-918d-41f4-9ce4-c4446b042760)

Cloudflare dashboard showing requests:
![cloudflare-panel](https://github.com/plisskien/anti_ddos_script/assets/29129602/4a410fdd-c9c5-4c0d-8d2a-7ee3c8ff3172)

Discord logs for reference:
![discord-logs](https://github.com/plisskien/anti_ddos_script/assets/29129602/b71d13ee-a9ab-4504-96b7-f6716d5369a9)

## Sources 
- Uptime Kuma
- Grafana integrated with Prometheus
