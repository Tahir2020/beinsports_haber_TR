#!/usr/bin/env python3
import json
import os
from datetime import datetime

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "channel_name": "beIN Sports Haber",
            "channel_logo": "https://www.tvlogolar.xyz/europa/turkey/beinsportshaber.png",
            "group_title": "Bein Sports Haber"
        }

def main():
    config = load_config()
    
    # Stream URL'yi oku
    try:
        with open('stream_url.txt', 'r', encoding='utf-8') as f:
            stream_url = f.readline().strip()
    except:
        print("❌ stream_url.txt okunamadı")
        exit(1)
    
    if not stream_url:
        print("❌ Stream URL boş")
        exit(1)
    
    # M3U oluştur
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""
    
    with open('beinsports_haber.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print("✅ M3U dosyası oluşturuldu")
    
    # Cache'ye kaydet
    os.makedirs('cache', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    cache_file = f"cache/stream_url_{timestamp}.txt"
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
    
    print(f"💾 Cache'e kaydedildi: {cache_file}")

if __name__ == "__main__":
    main()
