#!/usr/bin/env python3
"""
YouTube Canlı Yayın Bağlantısı Otomatik Güncelleyici + M3U Oluşturucu
"""

import subprocess
import json
import sys
import os
from datetime import datetime

def load_config():
    """Yapılandırma dosyasını yükle"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ config.json bulunamadı, varsayılan ayarlar kullanılıyor")
        return {
            "youtube_url": "https://www.youtube.com/embed/i7UpPgxfZZ8",
            "quality": "best[height<=1080][fps<=50]",
            "output_file": "stream_url.txt",
            "m3u_file": "beinsports_haber.m3u",
            "channel_name": "beIN Sports Haber",
            "channel_logo": "https://www.tvlogolar.xyz/europa/turkey/beinsportshaber.png",
            "group_title": "Bein Sports Haber"
        }

def get_stream_url(youtube_url, quality):
    """yt-dlp ile güncel akış bağlantısını al"""
    try:
        cmd = ['yt-dlp', '-g', '-f', quality, youtube_url]
        
        print(f"🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Bağlantı alınıyor...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stream_url = result.stdout.strip()
        
        if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
            print(f"✅ Yeni bağlantı alındı")
            return stream_url
        else:
            print(f"⚠️ Geçersiz bağlantı formatı")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp hatası: {e}")
        return None
    except FileNotFoundError:
        print("❌ yt-dlp bulunamadı! Önce 'pip install yt-dlp' ile kurun")
        return None

def create_m3u_file(stream_url, config):
    """M3U playlist dosyası oluştur"""
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""
    try:
        with open(config['m3u_file'], 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print(f"💾 M3U dosyası oluşturuldu: {config['m3u_file']}")
        return True
    except Exception as e:
        print(f"❌ M3U dosyası yazma hatası: {e}")
        return False

def save_url_to_file(url, filename):
    """Bağlantıyı dosyaya kaydet"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(url)
            f.write('\n')
            f.write(f"# Güncelleme: {datetime.now().isoformat()}\n")
        print(f"💾 Bağlantı {filename} dosyasına kaydedildi")
        return True
    except Exception as e:
        print(f"❌ Dosyaya yazma hatası: {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("🎬 beIN Sports Haber - Canlı Yayın Bağlantı Güncelleyici")
    print("=" * 50)
    
    config = load_config()
    
    youtube_url = config.get('youtube_url')
    quality = config.get('quality', 'best[height<=1080][fps<=50]')
    
    print(f"📺 YouTube URL: {youtube_url}")
    print(f"🎯 Kalite: {quality}")
    print(f"📺 Kanal: {config['channel_name']}")
    print(f"🖼️ Logo: {config['channel_logo']}")
    
    stream_url = get_stream_url(youtube_url, quality)
    
    if stream_url:
        save_url_to_file(stream_url, config['output_file'])
        
        if create_m3u_file(stream_url, config):
            print("\n✅ M3U dosyası başarıyla oluşturuldu!")
            print(f"📁 Dosya: {config['m3u_file']}")
            print("\n📌 M3U içeriği:")
            print("-" * 50)
            print(f"#EXTM3U")
            print(f"#EXTINF:-1 tvg-id=\"beinsports.tr\" tvg-name=\"{config['channel_name']}\" tvg-logo=\"{config['channel_logo']}\" group-title=\"{config['group_title']}\",{config['channel_name']}")
            print(f"{stream_url[:100]}...")
            print("-" * 50)
        else:
            sys.exit(1)
    else:
        print("❌ Bağlantı alınamadı!")
        sys.exit(1)

if __name__ == "__main__":
    main()