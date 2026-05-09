#!/usr/bin/env python3
"""
YouTube Canlı Yayın Bağlantısı Otomatik Güncelleyici + M3U Oluşturucu
JavaScript runtime hatası çözüldü
"""

import subprocess
import json
import sys
import os
import shutil
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
            "group_title": "Bein Sports Haber",
            "cache_dir": "cache",
            "keep_old_urls": False,
            "max_cache_age_hours": 1
        }

def clean_cache_directory(cache_dir, max_age_hours=1):
    """Cache klasörünü temizle"""
    if not os.path.exists(cache_dir):
        return
    
    print(f"🧹 Cache temizleniyor: {cache_dir}")
    deleted_count = 0
    
    try:
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            
            if os.path.isfile(item_path):
                file_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(item_path))).total_seconds() / 3600
                
                if file_age_hours > max_age_hours:
                    os.remove(item_path)
                    deleted_count += 1
                    print(f"  ✓ Silindi: {item}")
        
        print(f"✅ {deleted_count} eski dosya temizlendi")
        
    except Exception as e:
        print(f"⚠️ Cache temizleme hatası: {e}")

def save_to_cache(stream_url, config):
    """Yeni bağlantıyı cache'e kaydet"""
    cache_dir = config.get('cache_dir', 'cache')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_url_file = os.path.join(cache_dir, f"stream_url_{timestamp}.txt")
    with open(cache_url_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
        f.write(f"\n# Oluşturulma: {datetime.now().isoformat()}\n")
    
    cache_m3u_file = os.path.join(cache_dir, f"beinsports_haber_{timestamp}.m3u")
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""
    with open(cache_m3u_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    return cache_url_file, cache_m3u_file

def update_current_files(stream_url, config):
    """Mevcut dosyaları güncelle"""
    
    # Ana stream_url.txt dosyasını güncelle
    output_file = config['output_file']
    
    if os.path.exists(output_file):
        backup_file = f"{output_file}.old"
        shutil.copy2(output_file, backup_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
        f.write(f"\n# Son güncelleme: {datetime.now().isoformat()}\n")
    
    print(f"✅ Güncellendi: {output_file}")
    
    # Ana M3U dosyasını güncelle
    m3u_file = config['m3u_file']
    
    if os.path.exists(m3u_file):
        backup_m3u = f"{m3u_file}.old"
        shutil.copy2(m3u_file, backup_m3u)
    
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""
    with open(m3u_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"✅ Güncellendi: {m3u_file}")

def get_stream_url(youtube_url, quality):
    """yt-dlp ile güncel akış bağlantısını al - JS runtime hatası çözüldü"""
    
    # Yöntem 1: YouTube cookies ve extractor-args ile
    cmd = [
        'yt-dlp', 
        '-g', 
        '-f', quality,
        '--extractor-args', 'youtube:player_client=android',
        '--no-check-certificate',
        youtube_url
    ]
    
    print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Yeni manifest URL alınıyor...")
    print(f"📝 Komut: yt-dlp -g -f {quality} --extractor-args youtube:player_client=android")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        stream_url = result.stdout.strip()
        
        if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
            print(f"✅ Yeni manifest URL oluşturuldu")
            return stream_url
        else:
            print(f"⚠️ Geçersiz URL formatı")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ yt-dlp timeout (60 saniye)")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ İlk yöntem başarısız, alternatif deneniyor...")
        return get_stream_url_alternative(youtube_url, quality)

def get_stream_url_alternative(youtube_url, quality):
    """Alternatif yöntem - farklı player client ile"""
    
    # Yöntem 2: Farklı player client
    clients = ['android_embedded', 'ios', 'web']
    
    for client in clients:
        cmd = [
            'yt-dlp', 
            '-g', 
            '-f', quality,
            '--extractor-args', f'youtube:player_client={client}',
            '--no-check-certificate',
            youtube_url
        ]
        
        print(f"🔄 Deneniyor: client={client}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            
            if result.returncode == 0:
                stream_url = result.stdout.strip()
                if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
                    print(f"✅ Başarılı! Client={client}")
                    return stream_url
        except:
            continue
    
    print("❌ Tüm yöntemler başarısız oldu")
    return None

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🎬 beIN Sports Haber - Canlı Yayın Bağlantı Güncelleyici")
    print("📅", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    config = load_config()
    
    # Cache temizleme
    clean_cache_directory(
        config.get('cache_dir', 'cache'), 
        config.get('max_cache_age_hours', 1)
    )
    
    # Yeni manifest URL al
    stream_url = get_stream_url(
        config['youtube_url'], 
        config.get('quality', 'best[height<=1080][fps<=50]')
    )
    
    if not stream_url:
        print("\n❌ Kritik hata: Yeni manifest URL alınamadı!")
        print("Mevcut dosyalar korundu.")
        sys.exit(1)
    
    # URL'yi cache'e kaydet
    cache_url_file, cache_m3u_file = save_to_cache(stream_url, config)
    
    # Ana dosyaları güncelle
    update_current_files(stream_url, config)
    
    print("\n" + "=" * 60)
    print("✅ İşlem başarıyla tamamlandı!")
    print("=" * 60)

if __name__ == "__main__":
    main()
