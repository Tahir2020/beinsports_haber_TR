#!/usr/bin/env python3

import subprocess
import json
import sys
from datetime import datetime


def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "youtube_url": "https://www.youtube.com/@beINSPORTSTurkiye/live",
            "quality": "best[height<=1080][fps<=50]/best",
            "m3u8_file": "Bein_Sports_Haberler.m3u8",
            "channel_name": "beIN Sports Haber",
        }


def get_stream_url(youtube_url, quality):
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

    print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Manifest URL alınıyor...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=90
        )

        stream_url = result.stdout.strip().splitlines()[0]

        if stream_url and ('manifest' in stream_url or '.m3u8' in stream_url):
            print("✅ Manifest URL alındı")
            return stream_url

        return None

    except subprocess.CalledProcessError as e:
        print("❌ yt-dlp hatası:")
        print(e.stderr)
        return None

    except Exception as e:
        print(f"❌ Hata: {e}")
        return None


def create_m3u8(stream_url, config):
    # Sade M3U8 formatı
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""

    with open(config['m3u8_file'], 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"✅ {config['m3u8_file']} oluşturuldu")


def main():
    print("=" * 50)
    print("🎬 beIN Sports Haber Güncelleyici")
    print("=" * 50)

    config = load_config()

    stream_url = get_stream_url(
        config['youtube_url'],
        config['quality']
    )

    if not stream_url:
        print("❌ Stream URL alınamadı")
        sys.exit(1)

    create_m3u8(stream_url, config)

    print("✅ İşlem tamamlandı")


if __name__ == "__main__":
    main()
