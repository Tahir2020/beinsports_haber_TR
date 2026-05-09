#!/usr/bin/env python3
"""
YouTube Canlı Yayın Bağlantısı Otomatik Güncelleyici + M3U Oluşturucu
Cache yönetimi ile eski bağlantıları temizler, sadece günceli tutar
"""

import subprocess
import json
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

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
    """Cache klasörünü temizle, eski dosyaları sil"""
    if not os.path.exists(cache_dir):
        return
    
    print(f"🧹 Cache temizleniyor: {cache_dir}")
    deleted_count = 0
    
    try:
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            
            # Eski URL dosyalarını sil
            if os.path.isfile(item_path) and item.endswith('.txt'):
                file_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(item_path))).total_seconds() / 3600
                
                if file_age_hours > max_age_hours:
                    os.remove(item_path)
                    deleted_count += 1
                    print(f"  ✓ Silindi: {item} (yaş: {file_age_hours:.1f} saat)")
            # Eski m3u dosyalarını sil
            elif os.path.isfile(item_path) and item.endswith('.m3u'):
                file_age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(item_path))).total_seconds() / 3600
                
                if file_age_hours > max_age_hours:
                    os.remove(item_path)
                    deleted_count += 1
                    print(f"  ✓ Silindi: {item} (yaş: {file_age_hours:.1f} saat)")
        
        print(f"✅ {deleted_count} eski dosya temizlendi")
        
    except Exception as e:
        print(f"⚠️ Cache temizleme hatası: {e}")

def save_to_cache(stream_url, config):
    """Yeni bağlantıyı cache'e kaydet"""
    cache_dir = config.get('cache_dir', 'cache')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Cache klasörünü oluştur
    os.makedirs(cache_dir, exist_ok=True)
    
    # URL'yi cache'e kaydet
    cache_url_file = os.path.join(cache_dir, f"stream_url_{timestamp}.txt")
    with open(cache_url_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
        f.write(f"\n# Oluşturulma: {datetime.now().isoformat()}\n")
        f.write(f"# Kaynak: {config['youtube_url']}\n")
    
    # M3U'yu cache'e kaydet
    cache_m3u_file = os.path.join(cache_dir, f"beinsports_haber_{timestamp}.m3u")
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']} - {timestamp}
{stream_url}
# Güncelleme: {datetime.now().isoformat()}
"""
    with open(cache_m3u_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"💾 Cache'e kaydedildi: {cache_url_file}")
    print(f"💾 Cache'e kaydedildi: {cache_m3u_file}")
    
    return cache_url_file, cache_m3u_file

def update_current_files(stream_url, config, cache_url_file, cache_m3u_file):
    """Mevcut dosyaları güncelle (eskiyi sil, yeniyle değiştir)"""
    
    # 1. Ana stream_url.txt dosyasını güncelle
    output_file = config['output_file']
    
    # Eski dosyayı yedekle (isteğe bağlı)
    if os.path.exists(output_file):
        backup_file = f"{output_file}.old"
        shutil.copy2(output_file, backup_file)
        print(f"📦 Yedek oluşturuldu: {backup_file}")
    
    # Yeni içeriği yaz
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
        f.write(f"\n# Son güncelleme: {datetime.now().isoformat()}\n")
        f.write(f"# Cache referansı: {cache_url_file}\n")
    
    print(f"✅ Güncellendi: {output_file}")
    
    # 2. Ana M3U dosyasını güncelle
    m3u_file = config['m3u_file']
    
    # Eski M3U'yu yedekle
    if os.path.exists(m3u_file):
        backup_m3u = f"{m3u_file}.old"
        shutil.copy2(m3u_file, backup_m3u)
        print(f"📦 Yedek oluşturuldu: {backup_m3u}")
    
    # Yeni M3U içeriğini yaz
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
# Son güncelleme: {datetime.now().isoformat()}
# Cache: {cache_m3u_file}
"""
    with open(m3u_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"✅ Güncellendi: {m3u_file}")

def get_stream_url(youtube_url, quality):
    """yt-dlp ile güncel akış bağlantısını al"""
    try:
        cmd = ['yt-dlp', '-g', '-f', quality, youtube_url]
        
        print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Yeni manifest URL alınıyor...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        stream_url = result.stdout.strip()
        
        if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
            print(f"✅ Yeni manifest URL oluşturuldu")
            print(f"📎 URL: {stream_url[:120]}...")
            return stream_url
        else:
            print(f"⚠️ Geçersiz URL formatı")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ yt-dlp timeout (60 saniye)")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp hatası: {e}")
        if e.stderr:
            print(f"Hata detayı: {e.stderr[:200]}")
        return None
    except FileNotFoundError:
        print("❌ yt-dlp bulunamadı! Önce 'pip install yt-dlp' ile kurun")
        return None

def compare_and_update(stream_url, config):
    """Yeni URL ile eski URL'yi karşılaştır, farklıysa güncelle"""
    output_file = config['output_file']
    
    # Eski URL'yi oku
    old_url = None
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                old_url = f.readline().strip()
        except:
            pass
    
    # URL değişmiş mi kontrol et
    if old_url and old_url == stream_url:
        print("\n⚠️ URL değişmemiş, güncelleme yapılmadı")
        print(f"Mevcut URL hala geçerli: {stream_url[:100]}...")
        return False
    
    print(f"\n🔄 URL değişti! Eski ve yeni URL farklı")
    if old_url:
        print(f"Eski: {old_url[:80]}...")
        print(f"Yeni: {stream_url[:80]}...")
    
    return True

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🎬 beIN Sports Haber - Canlı Yayın Bağlantı Güncelleyici")
    print("📅", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    config = load_config()
    
    # Cache temizleme (1 saatten eski dosyalar)
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
    
    # URL değişikliğini kontrol et
    if not compare_and_update(stream_url, config):
        # URL değişmemiş olsa bile yine de cache'e kaydet (zaman damgası için)
        cache_url_file, cache_m3u_file = save_to_cache(stream_url, config)
        print("\n✅ URL değişmemiş olsa da cache'e kaydedildi")
        sys.exit(0)
    
    # Yeni URL'yi cache'e kaydet
    cache_url_file, cache_m3u_file = save_to_cache(stream_url, config)
    
    # Ana dosyaları güncelle (eskiyi sil, yeniyle değiştir)
    update_current_files(stream_url, config, cache_url_file, cache_m3u_file)
    
    print("\n" + "=" * 60)
    print("✅ İşlem başarıyla tamamlandı!")
    print(f"📁 Ana M3U: {config['m3u_file']}")
    print(f"💾 Cache klasörü: {config.get('cache_dir', 'cache')}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
