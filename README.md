# Anti-DDoS Python Script
Simple Python script that will detect timeout, and enable Cloudflare custom WAF rule. This is simple script that was created for people that don't really like to have their custom Cloudflare WAF always ON.
Keep in mind that this is my first even created Python script, I don't have any knowledge how to code, I made this script just for me, but I thought it would be nice thing to share it, maybe there are peaople with similar problem.

**Q&A**<br />
Q: What do I need to use it?<br />
A: Cloudflare free plan, another server to host script with SSH access, and installed python. (You can also host it on same server, but I don't recommend it)<br />

Q: Is it even working?<br />
A: Yes, you just need stable hosting provider. If your hosting provider is not too stable, script might trigger itself, without any DDoS attack.<br />

Q: How it works during DDoS attack?<br />
A: It will send every second request to detect timeout (default value is 5 seconds), after that script will check if server is up (It will ping server IP). If server is not up it will wait 60min, and start doing everything again.
If server is up, and there is downtime, it probbaly means that website is under DDoS attack, after that script will use Cloudflare API to update WAF rules, be sure to make own Cloudflare rules! (In code you have example)
After 60min it will turn off Cloudflare rules, and will start everything again. This script is working for me perfecly, key is fast reaction! If you want you can make own DDoS detection, in my case timeout is perfect since I have stable VPS.
<br />
Here you have proof.

![downtime](https://github.com/plisskien/anti_ddos_script/assets/29129602/bc99f130-a490-4e95-b22c-e40a560950df)
Here we can see all downtimes, all screenshots will show similar period of time, to show same DDoS attacks

![ddps-dead-server](https://github.com/plisskien/anti_ddos_script/assets/29129602/7e3b5af8-63d9-40aa-9714-bff44224e5be)
Here we can see that CPU usage was at 100%, during this time website was offline, see first screenshot

![ddos-not-dead-server](https://github.com/plisskien/anti_ddos_script/assets/29129602/298e7365-918d-41f4-9ce4-c4446b042760)
Here we can see that CPU usage was at around 30-40%, and during this time site was online, see first screenshot 

![cloudflare-panel](https://github.com/plisskien/anti_ddos_script/assets/29129602/4a410fdd-c9c5-4c0d-8d2a-7ee3c8ff3172)
Here you can see 'Requests Through Cloudflare' from my dashboard, this second DDoS was smaller, but it was still enough to take down my site

![discord-logs](https://github.com/plisskien/anti_ddos_script/assets/29129602/b71d13ee-a9ab-4504-96b7-f6716d5369a9)
Here we can see Discord logs, this is how it looks like



