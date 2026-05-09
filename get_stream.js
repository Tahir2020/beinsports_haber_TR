const { execSync } = require('child_process');
const fs = require('fs');
const https = require('https');

const YOUTUBE_URL = 'https://www.youtube.com/embed/i7UpPgxfZZ8';
const OUTPUT_FILE = 'stream_url.txt';

// YouTube'dan video ID çek
const videoId = YOUTUBE_URL.split('/').pop();
console.log(`📺 Video ID: ${videoId}`);

// Yöntem 1: yt-dlp'yi Python runtime ile dene
try {
    console.log('🔄 yt-dlp deneniyor...');
    const result = execSync(`yt-dlp -g -f "best[height<=1080]" --extractor-args "youtube:player_client=android" ${YOUTUBE_URL}`, { 
        encoding: 'utf-8',
        timeout: 60000 
    });
    
    const streamUrl = result.trim();
    if (streamUrl && (streamUrl.includes('.m3u8') || streamUrl.includes('manifest'))) {
        console.log('✅ Başarılı!');
        fs.writeFileSync(OUTPUT_FILE, streamUrl + '\n');
        console.log(`💾 Kaydedildi: ${streamUrl.substring(0, 100)}...`);
        process.exit(0);
    }
} catch (error) {
    console.log('❌ yt-dlp başarısız:', error.message);
}

// Yöntem 2: Innertube API (YouTube'un resmi API'si)
console.log('🔄 Innertube API deneniyor...');

const innertubeUrl = 'https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8';

const postData = JSON.stringify({
    videoId: videoId,
    context: {
        client: {
            clientName: 'ANDROID',
            clientVersion: '19.09.37',
            androidSdkVersion: 30,
            hl: 'tr',
            gl: 'TR'
        }
    }
});

const options = {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11)'
    }
};

const req = https.request(innertubeUrl, options, (res) => {
    let data = '';
    
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        try {
            const json = JSON.parse(data);
            
            // HLS manifest URL'ini bul
            if (json.streamingData && json.streamingData.hlsManifestUrl) {
                const streamUrl = json.streamingData.hlsManifestUrl;
                console.log('✅ Innertube API başarılı!');
                fs.writeFileSync(OUTPUT_FILE, streamUrl + '\n');
                console.log(`💾 Kaydedildi: ${streamUrl.substring(0, 100)}...`);
                process.exit(0);
            } else if (json.streamingData && json.streamingData.formats) {
                // En yüksek kaliteyi bul
                const formats = json.streamingData.formats;
                const bestFormat = formats.reduce((best, current) => {
                    const bestHeight = best.height || 0;
                    const currentHeight = current.height || 0;
                    return currentHeight > bestHeight ? current : best;
                }, {});
                
                if (bestFormat.url) {
                    console.log('✅ Video URL bulundu!');
                    fs.writeFileSync(OUTPUT_FILE, bestFormat.url + '\n');
                    process.exit(0);
                }
            }
            
            console.log('❌ Stream URL bulunamadı');
            process.exit(1);
            
        } catch (error) {
            console.log('❌ JSON parse hatası:', error.message);
            process.exit(1);
        }
    });
});

req.on('error', (error) => {
    console.log('❌ API hatası:', error.message);
    process.exit(1);
});

req.write(postData);
req.end();
