import requests
import re
import os

def vavoo_kanallari_cek():
    print("Vavoo kanalları çekiliyor...")
    
    def get_imza():
        headers = {
            "user-agent": "okhttp/4.11.0",
            "accept": "application/json"
        }
        data = {
            "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
            "reason": "app-blur",
            "locale": "de",
            "metadata": {"device": {"type": "Handset", "os": "Android", "model": "Pixel 4", "brand": "Google"}}
        }
        try:
            resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=15)
            sig = resp.json().get("signature")
            if sig:
                print(f"✅ İmza başarıyla alındı.")
                return sig
            else:
                print(f"❌ İmza boş döndü! Yanıt: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ İmza isteği hatası: {e}")
            return None

    imza = get_imza()
    if not imza: 
        print("İmza olmadan devam edilemiyor.")
        return

    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "mediahubmx-signature": imza
    }

    all_channels = []
    cursor = 0
    print("Kanal listesi isteniyor...")
    
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
            resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=payload, headers=headers, timeout=15)
            data = resp.json()
            items = data.get("items", [])
            all_channels.extend(items)
            print(f"Şu ana kadar çekilen kanal sayısı: {len(all_channels)}")
            
            cursor = data.get("nextCursor")
            if not cursor: break
        except Exception as e:
            print(f"❌ Kanal çekme hatası: {e}")
            break

    # Dosya Oluşturma Kısmı
    if all_channels:
        try:
            with open("vavoo.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for ch in all_channels:
                    name = ch.get("name", "Isimsiz")
                    url = ch.get("url", "")
                    category = ch.get("group", "Genel")
                    if url:
                        f.write(f'#EXTINF:-1 group-title="{category} VAVOO",{name}\n{url}\n')
            print(f"✅ BAŞARILI: 'vavoo.m3u' dosyası {len(all_channels)} kanal ile yazıldı.")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")
    else:
        print("⚠️ KRİTİK: Liste boş olduğu için dosya oluşturulmadı. Vavoo IP engeli uyguluyor olabilir.")

if __name__ == "__main__":
    vavoo_kanallari_cek()