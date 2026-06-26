#!/usr/bin/env python3

import subprocess
import json
import sys
import re
from datetime import datetime
from pathlib import Path

COOKIE_FILE = "cookies.txt"

def clean_cookie_file():
    """Cookie dosyasındaki geçersiz cookie'leri temizle"""
    cookie_path = Path(COOKIE_FILE)
    if not cookie_path.exists():
        return False
    
    # Sorunlu cookie'ler
    blocked_cookies = ["CONSISTENCY", "ST-sbra4i", "OTZ", "__Secure-YEC", "__Secure-YENID", "consent.youtube.com"]
    
    try:
        content = cookie_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        cleaned_lines = []
        header_lines = []
        cookie_lines = []
        
        for line in lines:
            # Başlık satırlarını koru
            if line.startswith("#"):
                header_lines.append(line)
                continue
            
            # Boş satırları atla
            if not line.strip():
                continue
            
            # Cookie'yi kontrol et
            parts = line.split("\t")
            if len(parts) >= 7:
                cookie_name = parts[5].strip()
                # Domain kontrolü
                domain = parts[0].strip()
                
                # Sorunlu cookie'leri filtrele
                if cookie_name not in blocked_cookies:
                    # consent.youtube.com domainini filtrele
                    if "consent.youtube.com" not in domain:
                        cookie_lines.append(line)
        
        # Header + cookie'leri birleştir
        cleaned_lines = header_lines + cookie_lines
        
        # Eğer hiç cookie kalmadıysa dosyayı boş bırak
        if not cookie_lines:
            cookie_path.write_text("", encoding="utf-8")
            print("   ⚠️ Tüm cookie'ler temizlendi, dosya boşaltıldı")
            return True
        
        # Yeni dosyayı yaz
        cookie_path.write_text("\n".join(cleaned_lines), encoding="utf-8")
        print(f"   ✅ Cookie dosyası temizlendi: {len(cookie_lines)} cookie korundu")
        return True
        
    except Exception as e:
        print(f"   ⚠️ Cookie temizleme hatası: {e}")
        return False

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
    """YouTube canlı yayın URL'sini al - Cookie hatası durumunda cookie'siz dener"""
    
    print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Manifest URL alınıyor...")
    
    # Cookie dosyasını kontrol et ve temizle
    cookie_path = Path(COOKIE_FILE)
    use_cookie = False
    
    if cookie_path.exists() and cookie_path.stat().st_size > 0:
        print("   🍪 Cookie dosyası bulundu, temizleniyor...")
        clean_cookie_file()
        
        # Tekrar kontrol et
        if cookie_path.exists() and cookie_path.stat().st_size > 0:
            use_cookie = True
            print("   ✅ Cookie kullanılacak")
        else:
            print("   ⚠️ Cookie dosyası boş, cookiesiz devam ediliyor")
    else:
        print("   ⚠️ Cookie dosyası yok veya boş, cookiesiz devam ediliyor")
    
    # Denenecek yöntemler
    methods = []
    
    # 1) Cookie'li deneme (eğer varsa)
    if use_cookie:
        methods.append({
            "name": "cookie/default",
            "cmd": [
                'yt-dlp',
                '-g',
                '--cookies', COOKIE_FILE,
                '--js-runtimes', 'deno',
                '--remote-components', 'ejs:github',
                '--extractor-args', 'youtube:player_client=default',
                '-f', quality,
                youtube_url
            ]
        })
        
        methods.append({
            "name": "cookie/default/hls",
            "cmd": [
                'yt-dlp',
                '-g',
                '--cookies', COOKIE_FILE,
                '--js-runtimes', 'deno',
                '--remote-components', 'ejs:github',
                '--extractor-args', 'youtube:player_client=default',
                '-f', 'best[protocol=m3u8_native]/best[protocol=m3u8]/best',
                youtube_url
            ]
        })
    
    # 2) Cookie'siz denemeler
    methods.append({
        "name": "no-cookie/default",
        "cmd": [
            'yt-dlp',
            '-g',
            '--js-runtimes', 'deno',
            '--remote-components', 'ejs:github',
            '--extractor-args', 'youtube:player_client=default',
            '-f', quality,
            youtube_url
        ]
    })
    
    methods.append({
        "name": "no-cookie/default/hls",
        "cmd": [
            'yt-dlp',
            '-g',
            '--js-runtimes', 'deno',
            '--remote-components', 'ejs:github',
            '--extractor-args', 'youtube:player_client=default',
            '-f', 'best[protocol=m3u8_native]/best[protocol=m3u8]/best',
            youtube_url
        ]
    })
    
    # 3) Farklı client denemeleri (cookie'siz)
    for client in ["android", "ios", "web", "tv"]:
        methods.append({
            "name": f"no-cookie/{client}",
            "cmd": [
                'yt-dlp',
                '-g',
                '--js-runtimes', 'deno',
                '--remote-components', 'ejs:github',
                '--extractor-args', f'youtube:player_client={client}',
                '-f', 'best[protocol=m3u8_native]/best[protocol=m3u8]/best',
                youtube_url
            ]
        })
    
    # 4) Klasik yt-dlp (cookie'siz)
    for client in ["default", "android", "ios", "web"]:
        methods.append({
            "name": f"classic/{client}",
            "cmd": [
                'yt-dlp',
                '-g',
                '--extractor-args', f'youtube:player_client={client}',
                '-f', 'best[protocol=m3u8_native]/best[protocol=m3u8]/best',
                youtube_url
            ]
        })
    
    # Her yöntemi dene
    for method in methods:
        print(f"   ▶️ Deneme: {method['name']}")
        
        try:
            result = subprocess.run(
                method['cmd'],
                capture_output=True,
                text=True,
                timeout=90
            )
            
            # Cookie hatasını kontrol et
            if result.stderr and "invalid Netscape format cookies file" in result.stderr:
                print(f"   ⚠️ Cookie hatası, geçiliyor...")
                continue
            
            if result.returncode == 0 and result.stdout.strip():
                stream_url = result.stdout.strip().splitlines()[0]
                
                if stream_url and ('manifest' in stream_url or '.m3u8' in stream_url or 'googlevideo' in stream_url):
                    print(f"   ✅ {method['name']} ile URL bulundu")
                    return stream_url
                    
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ Zaman aşımı")
            continue
        except Exception as e:
            print(f"   ⚠️ Hata: {e}")
            continue
    
    print("❌ Hiçbir yöntemle URL alınamadı")
    return None

def create_m3u8(stream_url, config):
    """M3U8 dosyasını oluştur"""
    
    # YouTube URL'si ise direkt stream URL'sini kullan
    if "youtube.com" in stream_url or "youtu.be" in stream_url:
        # Eğer hala YouTube URL'si döndüyse, bu bir hata
        print("❌ Hala YouTube URL'si döndü, geçersiz stream")
        return False
    
    # Sade M3U8 formatı
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""
    
    m3u8_file = config.get('m3u8_file', 'Bein_Sports_Haberler.m3u8')
    
    with open(m3u8_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"✅ {m3u8_file} oluşturuldu")
    return True

def main():
    print("=" * 50)
    print("🎬 beIN Sports Haber Güncelleyici")
    print("=" * 50)

    config = load_config()
    
    # Cookie dosyasını başlangıçta temizle
    cookie_path = Path(COOKIE_FILE)
    if cookie_path.exists():
        print(f"\n📄 Cookie dosyası bulundu, temizleniyor...")
        clean_cookie_file()

    stream_url = get_stream_url(
        config['youtube_url'],
        config['quality']
    )

    if not stream_url:
        print("❌ Stream URL alınamadı")
        sys.exit(1)

    if not create_m3u8(stream_url, config):
        print("❌ M3U8 dosyası oluşturulamadı")
        sys.exit(1)

    print("\n✅ İşlem tamamlandı")

if __name__ == "__main__":
    main()
