import requests
import os
import re
import json
import gzip
import io
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from dateutil import parser
import time

load_dotenv()

# =================================================================
# 1. GÜNCEL VAVOO İMZA VE VERİ ÇEKME MOTORU
# =================================================================

def getAuthSignature():
    """Vavoo sunucusuna erişim için gerekli imzayı alır."""
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
        resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=15)
        signature = resp.json().get("signature")
        if signature:
            return signature
    except Exception as e:
        print(f"❌ İmza hatası: {e}")
    return None

def fetch_vavoo_channels(group=""):
    """Vavoo kataloğundan belirtilen gruptaki kanalları çeker."""
    signature = getAuthSignature()
    if not signature:
        return []

    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "mediahubmx-signature": signature
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
            "filter": {"group": group} if group else {"group": ""},
            "cursor": cursor
        }
        try:
            resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=payload, headers=headers, timeout=15)
            data = resp.json()
            items = data.get("items", [])
            all_channels.extend(items)
            cursor = data.get("nextCursor")
            if not cursor: break
        except Exception as e:
            print(f"❌ Veri çekme hatası: {e}")
            break
    return all_channels

# =================================================================
# 2. YARDIMCI ARAÇLAR
# =================================================================

def clean_channel_name(name):
    return re.sub(r'\s*\.(a|b|c|s|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|t|u|v|w|x|y|z)\s*$', '', name, flags=re.IGNORECASE).strip()

def normalize_channel_name(name):
    name = re.sub(r"\s+", "", name.strip().lower())
    name = re.sub(r"\.it\b", "", name)
    name = re.sub(r"hd|fullhd", "", name)
    return name

# =================================================================
# 3. ANA FONKSİYONLAR (UYARLANMIŞ)
# =================================================================

def italy_channels():
    """İtalya kanallarını çeker ve 'channels_italy.m3u8' dosyasına yazar."""
    print("🇮🇹 İtalya kanalları çekiliyor...")
    channels = fetch_vavoo_channels("Italy")
    
    if channels:
        with open("channels_italy.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                name = clean_channel_name(ch.get("name", "Isimsiz"))
                url = ch.get("url", "")
                if url:
                    f.write(f'#EXTINF:-1 group-title="Italy",{name}\n{url}\n')
        print(f"✅ channels_italy.m3u8 oluşturuldu ({len(channels)} kanal).")

def world_channels_generator():
    """Tüm dünya kanallarını çeker ve 'world.m3u8' dosyasına yazar."""
    print("🌍 Dünya kanalları çekiliyor...")
    channels = fetch_vavoo_channels("")
    
    if channels:
        with open("world.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                name = clean_channel_name(ch.get("name", "Isimsiz"))
                url = ch.get("url", "")
                group = ch.get("group", "World")
                if url:
                    f.write(f'#EXTINF:-1 group-title="{group}",{name}\n{url}\n')
        print(f"✅ world.m3u8 oluşturuldu ({len(channels)} kanal).")

# =================================================================
# 4. BİRLEŞTİRME VE TEMİZLİK (DİĞER FONKSİYONLAR)
# =================================================================

def merger_playlist():
    print("🔗 Playlistler birleştiriliyor (Normal)...")
    NOMEREPO = os.getenv("NOMEREPO", "TV").strip()
    NOMEGITHUB = os.getenv("NOMEGITHUB", "").strip()
    
    content = f'#EXTM3U url-tvg="https://raw.githubusercontent.com/{NOMEGITHUB}/{NOMEREPO}/main/epg.xml"\n'
    
    for f_name in ["channels_italy.m3u8", "eventi.m3u8"]:
        if os.path.exists(f_name):
            with open(f_name, "r", encoding="utf-8") as f:
                content += f.read().replace("#EXTM3U", "")
                
    with open("lista.m3u", "w", encoding="utf-8") as f:
        f.write(content)

def remover():
    for f in ["channels_italy.m3u8", "eventi.m3u8", "world.m3u8"]:
        if os.path.exists(f):
            os.remove(f)

# =================================================================
# 5. ANA ÇALIŞTIRICI (MAIN)
# =================================================================

def main():
    try:
        # Kanalları Oluştur
        italy_channels()
        
        world_flag = os.getenv("WORLD", "no").strip().lower()
        if world_flag == "si":
            world_channels_generator()
            
        # Birleştir
        merger_playlist()
        
        # Temizle (Gerekiyorsa aktif edin)
        # remover()
        
        print("🚀 İşlem başarıyla tamamlandı!")
    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

if __name__ == "__main__":
    main()
