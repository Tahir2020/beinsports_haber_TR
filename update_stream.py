#!/usr/bin/env python3
"""
YouTube Canlı Yayın Bağlantısı Otomatik Güncelleyici + M3U Oluşturucu
Deno + EJS + Cookies uyumlu sürüm
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
            "youtube_url": "https://www.youtube.com/watch?v=i7UpPgxfZZ8",
            "quality": "best[height<=1080][fps<=50]/best",
            "output_file": "stream_url.txt",
            "m3u_file": "Bein_Sports_Haberler.m3u",
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
                file_age_hours = (
                    datetime.now() - datetime.fromtimestamp(os.path.getmtime(item_path))
                ).total_seconds() / 3600

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

    cache_m3u_file = os.path.join(cache_dir, f"Bein_Sports_Haberler_{timestamp}.m3u")
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="beinsports.tr" tvg-name="{config['channel_name']}" tvg-logo="{config['channel_logo']}" group-title="{config['group_title']}",{config['channel_name']}
{stream_url}
"""

    with open(cache_m3u_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    return cache_url_file, cache_m3u_file


def update_current_files(stream_url, config):
    """Mevcut dosyaları güncelle"""

    output_file = config['output_file']

    if os.path.exists(output_file):
        backup_file = f"{output_file}.old"
        shutil.copy2(output_file, backup_file)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(stream_url)
        f.write(f"\n# Son güncelleme: {datetime.now().isoformat()}\n")

    print(f"✅ Güncellendi: {output_file}")

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
    """yt-dlp ile güncel akış bağlantısını al"""

    cmd = [
        'yt-dlp',
        '-g',
        '--cookies', 'cookies.txt',
        '--js-runtimes', 'deno',
        '--remote-components', 'ejs:github',
        '--extractor-args', 'youtube:player_client=default',
        '-f', quality,
        youtube_url
    ]

    print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Yeni manifest URL alınıyor...")
    print("📝 Komut: yt-dlp -g --cookies cookies.txt --js-runtimes deno --remote-components ejs:github")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=90
        )

        stream_url = result.stdout.strip().splitlines()[0]

        if stream_url and ('.m3u8' in stream_url or 'manifest' in stream_url):
            print("✅ Yeni manifest URL oluşturuldu")
            return stream_url

        print("⚠️ Geçersiz URL formatı")
        print(result.stdout)
        return None

    except subprocess.CalledProcessError as e:
        print("❌ yt-dlp hatası")
        print(e.stderr)
        return None

    except subprocess.TimeoutExpired:
        print("❌ yt-dlp timeout")
        return None


def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("🎬 beIN Sports Haber - Canlı Yayın Bağlantı Güncelleyici")
    print("📅", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)

    config = load_config()

    clean_cache_directory(
        config.get('cache_dir', 'cache'),
        config.get('max_cache_age_hours', 1)
    )

    stream_url = get_stream_url(
        config['youtube_url'],
        config.get('quality', 'best[height<=1080][fps<=50]/best')
    )

    if not stream_url:
        print("\n❌ Kritik hata: Yeni manifest URL alınamadı!")
        print("Mevcut dosyalar korundu.")
        sys.exit(1)

    save_to_cache(stream_url, config)

    update_current_files(stream_url, config)

    print("\n" + "=" * 60)
    print("✅ İşlem başarıyla tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()
