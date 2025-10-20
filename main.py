import os
import requests
from bs4 import BeautifulSoup
import time
from keep_alive import keep_alive

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise SystemExit("TOKEN ve CHAT_ID environment variable olarak ayarlanmalı.")

URL = "https://www.willhaben.at/iad/gebrauchtwagen/auto/gebrauchtwagenboerse?sort=1&rows=30&CAR_MODEL/MAKE=1003&CAR_MODEL/MAKE=1056&CAR_MODEL/MAKE=1057&CAR_MODEL/MAKE=1065&ENGINE/FUEL=100003&MOTOR_CONDITION=20&isNavigation=true&sfId=0b534f06-7302-42a1-9217-91e92ef9c569&page=1&ENGINEEFFECT_FROM=66&PRICE_TO=6000&MILEAGE_TO=190000&YEAR_MODEL_FROM=2009"

sent_ads = set()

def check_ads():
    # headers'i try dışında da tanımlayabilirsiniz; burada try içine koyduk
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/123.0 Safari/537.36"
        }
        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print("Sayfa okunamadı:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    ads = soup.find_all("a", class_="aditem-detail-title")
    new_ads = []
    for ad in ads:
        href = ad.get("href")
        if not href:
            continue
        link = "https://www.willhaben.at" + href
        if link not in sent_ads:
            sent_ads.add(link)
            new_ads.append(link)
    return new_ads

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=10)
        print("Telegram response:", r.status_code, r.text)
    except Exception as e:
        print("Telegram gönderilemedi:", e)

# web sunucusunu başlat
keep_alive()

print("Bot başlatıldı, döngü çalışıyor...")
send_telegram("Bot test mesajı")
while True:
    print("Sayfa kontrol ediliyor...")
    new = check_ads()
    if new:
        for a in new:
            send_telegram(a)
            print("Yeni ilan gönderildi:", a)
    else:
        print("Yeni ilan yok.")
    time.sleep(300)  # 5 dakika bekleme
