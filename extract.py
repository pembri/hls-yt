import json
import subprocess
import os

with open('channels.json') as f:
    channels = json.load(f)

os.makedirs('channel', exist_ok=True)

for slug, url in channels.items():
    print(f"Processing {slug}...")
    try:
        result = subprocess.run([
            'yt-dlp', '-g',
            '--no-warnings', '--quiet',
            '--cookies', '/tmp/cookies.txt',
            '--extractor-args', 'youtube:player_client=ios',
            url
        ], capture_output=True, text=True, timeout=60)

        hls_url = None
        for line in result.stdout.strip().split('\n'):
            if '.m3u8' in line:
                hls_url = line.strip()
                break

        if hls_url:
            with open(f'channel/{slug}.m3u8', 'w') as f:
                f.write(f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=0\n{hls_url}\n")
            print(f"  OK: {slug}")
        else:
            print(f"  FAILED: {slug}")
            print(f"  stderr: {result.stderr[:200]}")
    except Exception as e:
        print(f"  ERROR: {slug} - {e}")
