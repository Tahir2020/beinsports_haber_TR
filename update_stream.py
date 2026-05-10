#!/usr/bin/env python3
"""
YouTube Canlı Yayınını M3U8'e Çeviren Araç
beIN Sports Haber ve benzeri YouTube kanalları için
"""

import subprocess
import json
import sys
import os
from datetime import datetime

CONFIG_FILE = "config.json"
COOKIE_FILE = "cookies.txt"

def load_config():
    """config.json dosyasını yükler, yoksa oluşturur."""
    default_config = {
        "youtube_url": "https://www.youtube.com/watch?v=i7UpPgxfZZ8",
        "quality": "best[height<=1080][fps<=50]/best",
        "m3u_file": "Bein_Sports_Haberler.m3u",
        "channel_name": "beIN Sports Haber",
        "channel_logo": "https://www.tvlogolar.xyz/europa/turkey/beinsportshaber.png",
        "group_title": "TR: beIN SPORTS HABER"
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ config.json bozuk. Varsayılan ayarlar kullanılıyor.")
            return default_config
    else:
        print("⚠️ config.json bulunamadı. Varsayılan ayarlarla oluşturuluyor.")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config

def check_cookie_file():
    """cookies.txt dosyasının varlığını kontrol eder."""
    if not os.path.exists(COOKIE_FILE):
        print(f"⚠️ UYARI: {COOKIE_FILE} dosyası bulunamadı!")
        print("   YouTube engellemesini aşmak için bir cookies.txt dosyası gereklidir.")
        print("   Chrome/Firefox için 'Get cookies.txt LOCALLY' eklentisi ile alabilirsiniz.")
        print("   (Önce YouTube'da oturum açmayı unutmayın!)")
        return False
    return True

def get_stream_url(youtube_url, quality):
    """yt-dlp ile stream URL'sini alır - GELİŞTİRİLMİŞ VERSİYON"""
    
    print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Stream URL alınıyor...")
    print(f"📺 Hedef: {youtube_url}")
    
    # Yöntem 1: cookies.txt ile (en güvenilir)
    if os.path.exists(COOKIE_FILE):
        print("🍪 Yöntem 1: cookies.txt ile deneniyor...")
        cmd_cookie = [
            'yt-dlp', '-g', '--no-check-certificate',
            '--cookies', COOKIE_FILE,
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-f', quality,
            youtube_url
        ]
        try:
            result = subprocess.run(cmd_cookie, capture_output=True, text=True, timeout=90)
            if result.returncode == 0:
                stream_url = result.stdout.strip().splitlines()[0]
                if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
                    print("✅ Stream URL alındı (cookies ile)")
                    return stream_url
        except subprocess.TimeoutExpired:
            print("⏱️ Zaman aşımı (cookies yöntemi)")
    
    # Yöntem 2: Android player_client ile (cookies olmadan dene)
    print("🌐 Yöntem 2: Android player_client ile deneniyor...")
    cmd_android = [
        'yt-dlp', '-g', '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '--extractor-args', 'youtube:player_client=android',
        '-f', quality,
        youtube_url
    ]
    try:
        result = subprocess.run(cmd_android, capture_output=True, text=True, timeout=90)
        if result.returncode == 0:
            stream_url = result.stdout.strip().splitlines()[0]
            if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
                print("✅ Stream URL alındı (Android yöntemi ile)")
                return stream_url
        else:
            print(f"⚠️ Android yöntemi hata verdi: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("⏱️ Zaman aşımı (Android yöntemi)")
    
    # Yöntem 3: iOS player_client ile dene
    print("📱 Yöntem 3: iOS player_client ile deneniyor...")
    cmd_ios = [
        'yt-dlp', '-g', '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        '--extractor-args', 'youtube:player_client=ios',
        '-f', quality,
        youtube_url
    ]
    try:
        result = subprocess.run(cmd_ios, capture_output=True, text=True, timeout=90)
        if result.returncode == 0:
            stream_url = result.stdout.strip().splitlines()[0]
            if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
                print("✅ Stream URL alındı (iOS yöntemi ile)")
                return stream_url
    except subprocess.TimeoutExpired:
        print("⏱️ Zaman aşımı (iOS yöntemi)")
    
    print("❌ Tüm yöntemler başarısız oldu!")
    return None

def create_m3u(stream_url, config):
    """M3U dosyasını oluşturur."""
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""
    with open(config['m3u_file'], 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    print(f"✅ {config['m3u_file']} oluşturuldu")
    print(f"📁 Dosya konumu: {os.path.abspath(config['m3u_file'])}")

def main():
    print("=" * 50)
    print("🎬 YouTube Canlı Yayın M3U8 Dönüştürücü")
    print("=" * 50)
    
    config = load_config()
    
    print(f"\n📋 Yapılandırma:")
    print(f"   📺 YouTube URL: {config['youtube_url']}")
    print(f"   📁 Çıktı dosyası: {config['m3u_file']}")
    print(f"   🖼️ Logo: {config['channel_logo']}")
    
    check_cookie_file()
    
    stream_url = get_stream_url(config['youtube_url'], config['quality'])
    
    if not stream_url:
        print("\n❌ Stream URL alınamadı!")
        print("\n💡 Çözüm önerileri:")
        print("   1. YouTube'da oturum açın")
        print("   2. 'Get cookies.txt LOCALLY' eklentisi ile cookies.txt oluşturun")
        print("   3. Dosyayı bu script'in yanına koyun")
        print("   4. yt-dlp'yi güncelleyin: pip install --upgrade yt-dlp")
        sys.exit(1)
    
    create_m3u(stream_url, config)
    print("\n✅ İşlem tamamlandı")

if __name__ == "__main__":
    main()
