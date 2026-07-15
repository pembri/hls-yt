import json
import os
import subprocess
import urllib.request

WORK_DIR = os.getcwd()
WORKER_BASE = os.environ.get("WORKER_BASE", "")
COOKIES_FILE = os.environ.get("COOKIES_FILE", "")

with open("channels.json") as f:
    channels = json.load(f)

print(f"  Found {len(channels)} channels:")
for slug in channels:
    print(f"  - {slug}")
print()
print("🔄 Extracting HLS URLs...")
print()

os.makedirs("channel", exist_ok=True)

success = 0
failed = 0
successful_channels = []

for slug, url in channels.items():
    print(f"  [{slug}] Processing...", end=" ", flush=True)
    try:
        cmd = ["yt-dlp", "-j", "--no-warnings", "--quiet"]
        if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]
        cmd += ["--extractor-args", "youtube:player_client=web"]
        cmd += [url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        hls_url = None
        try:
            info = json.loads(result.stdout.strip().split("\n")[0])
            for fmt in info.get("formats", []):
                if fmt.get("manifest_url") and ".m3u8" in fmt.get("manifest_url", ""):
                    hls_url = fmt["manifest_url"]
                    break
            if not hls_url and info.get("manifest_url"):
                hls_url = info["manifest_url"]
        except Exception:
            hls_url = None

        if hls_url:
            try:
                req = urllib.request.Request(hls_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    manifest_content = resp.read().decode("utf-8")
            except Exception:
                manifest_content = None

            if manifest_content and "#EXTM3U" in manifest_content:
                with open(f"channel/{slug}.m3u8", "w") as f:
                    f.write(manifest_content)
                print("✅ OK")
                success += 1
                successful_channels.append(slug)
            else:
                print("❌ FAILED (fetch manifest)")
                failed += 1
        else:
            print("❌ FAILED")
            if result.stderr:
                print(f"     {result.stderr.strip()[:100]}")
            failed += 1
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        failed += 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        failed += 1

print()
print("  📝 Generating playlist.m3u8...")
playlist_lines = ["#EXTM3U"]
for slug in successful_channels:
    name = slug.replace("-", " ").title()
    stream_url = f"{WORKER_BASE}/stream-hls/{slug}/master.m3u8"
    playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-id="{slug}",{name}')
    playlist_lines.append(stream_url)

with open("playlist.m3u8", "w") as f:
    f.write("\n".join(playlist_lines) + "\n")

print(f"  ✅ Success: {success} | ❌ Failed: {failed}")
print(f"  📺 playlist.m3u8: {len(successful_channels)} channels")

if success == 0:
    raise SystemExit(1)
