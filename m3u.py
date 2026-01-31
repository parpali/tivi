import requests
import re
import os

# Vavoo için FlareSolverr gerekmez, bu yüzden URL tanımlamaya gerek yok.

def vavoo_kanallari_cek():
    print("Vavoo kanalları çekiliyor...")
    
    # 1. Vavoo Sunucusuna Giriş İçin İmza (Signature) Al
    def get_imza():
        headers = {
            "user-agent": "okhttp/4.11.0",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8"
        }
        data = {
            "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
            "reason": "app-blur",
            "locale": "de",
            "metadata": {"device": {"type": "Handset", "os": "Android", "model": "Pixel 4", "brand": "Google"}}
        }
        try:
            resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=10)
            return resp.json().get("signature")
        except:
            print("❌ İmza alınamadı!")
            return None

    # 2. Kanal İsimlerini Temizle
    def isim_temizle(name):
        return re.sub(r'\s*\.[a-z]\s*$', '', name, flags=re.IGNORECASE).strip()

    # 3. Kanalları Çek
    imza = get_imza()
    if not imza: return

    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "mediahubmx-signature": imza
    }

    all_channels = []
    cursor = 0
    while True:
        payload = {
            "language": "de",
            "region": "AT",
            "catalogId": "iptv",
            "id": "iptv",
            "adult": False,
            "sort": "name",
            "filter": {"group": ""},
            "cursor": cursor
        }
        try:
            resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=payload, headers=headers, timeout=10)
            data = resp.json()
            items = data.get("items", [])
            all_channels.extend(items)
            cursor = data.get("nextCursor")
            if not cursor: break
        except:
            break

# 4. M3U Olarak Kaydet
    print(f"Toplam çekilen ham veri: {len(all_channels)}") # BU SATIRI EKLEDİK
    if all_channels:
        with open("vavoo.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in all_channels:
                name = isim_temizle(ch.get("name", "Isimsiz"))
                url = ch.get("url", "")
                category = ch.get("group", "Genel")
                if url:
                    f.write(f'#EXTINF:-1 group-title="{category} VAVOO",{name}\n{url}\n')
        
        print(f"✅ Bitti! {len(all_channels)} kanal 'vavoo.m3u' dosyasına kaydedildi.")
    else:
        print("❌ Hiç kanal bulunamadı.")

if __name__ == "__main__":
    vavoo_kanallari_cek()