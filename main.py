import os
import setuptools
import time
import requests
from bs4 import BeautifulSoup
from keep_alive import keep_alive

# Selenium / undetected_chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise SystemExit("TOKEN ve CHAT_ID environment variable olarak ayarlanmalı.")

URL = "https://www.willhaben.at/iad/gebrauchtwagen/auto/gebrauchtwagenboerse?sort=1&rows=30&CAR_MODEL/MAKE=1003&CAR_MODEL/MAKE=1056&CAR_MODEL/MAKE=1057&CAR_MODEL/MAKE=1065&ENGINE/FUEL=100003&MOTOR_CONDITION=20&isNavigation=true&sfId=0b534f06-7302-42a1-9217-91e92ef9c569&page=1&ENGINEEFFECT_FROM=66&PRICE_TO=6000&MILEAGE_TO=190000&YEAR_MODEL_FROM=2009"

sent_ads = set()

def check_ads():
    """
    Willhaben sayfasını Selenium (headless) ile açıp ilan linklerini toplayacak.
    - Chrome headless kullanır (undetected_chromedriver)
    - Bulunan linklerin href'atlarını kontrol eder.
    """
    new_ads = []
    driver = None
    try:
        options = uc.ChromeOptions()
        # headless yeni paramı; bazı platformlarda "--headless" kullan
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        # isteğe bağlı: ülke/locale
        options.add_argument("--lang=de-DE")

        # Başlat
        driver = uc.Chrome(options=options)

        # Git ve bekle (explicit wait)
        driver.get(URL)
        # sayfanın dinamik olarak yüklenmesi için bekle (örneğin list öğesi gelene kadar)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/iad/']"))
            )
        except Exception:
            # bekleme başarısız olsa da devam edeceğiz (sayfa statik olabilir)
            pass

        # Tüm linkleri topla (ilan linkleri genelde /iad/ ile başlıyor)
        elems = driver.find_elements(By.CSS_SELECTOR, "a[href^='/iad/']")
        for e in elems:
            href = e.get_attribute("href")
            if not href:
                continue
            # filtre: sadece willhaben içindeki ilana benzeyen linkleri tut
            if "/iad/gebrauchtwagen/" in href or "/iad/auto/" in href or "/iad/" in href:
                # normalize: tam url ise olduğu gibi al, yoksa base ile birleştir
                link = href
                # uniq ve daha önce yollanmadıysa listele
                if link not in sent_ads:
                    sent_ads.add(link)
                    new_ads.append(link)

        # Güvenlik: eğer çok fazla link varsa kısa tut (isteğe bağlı)
        # new_ads = new_ads[:30]
        return new_ads

    except Exception as e:
        print("Sayfa okunamadı (selenium):", e)
        return []
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=15)
        print("Telegram response:", r.status_code, r.text)
    except Exception as e:
        print("Telegram gönderilemedi:", e)

# keep alive webserver
keep_alive()

print("Bot başlatıldı, döngü çalışıyor...")
# Test bildirimi (isteğe bağlı, deploy sonrası test için)
# send_telegram("✅ Bot yeniden başlatıldı ve çalışıyor!")

while True:
    print("Sayfa kontrol ediliyor...")
    new = check_ads()
    if new:
        for a in new:
            send_telegram(a)
            print("Yeni ilan gönderildi:", a)
    else:
        print("Yeni ilan yok.")
    time.sleep(180)  # 3 dakikada bir kontrol (test için daha kısa yapabilirsin)
