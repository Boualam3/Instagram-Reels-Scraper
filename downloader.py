import csv
# import os
import random
import subprocess
import time
# from pathlib import Path
from urllib.parse import urlparse


def download_reels_from_csv(csv_path, output_folder):
    """
    Downloads Instagram reels from CSV

    Args:
        csv_path (Path): Path to CSV file
        output_folder (Path): Directory to save downloads
    """
    # Create output directory
    output_folder.mkdir(parents=True, exist_ok=True)

    # Track results
    results = {'success': 0, 'failed': 0, 'skipped': 0}

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if 'url' not in reader.fieldnames:
                print("❌ CSV must contain 'url' column")
                return

            for i, row in enumerate(reader, 1):
                url = row['url'].strip()
                plays = row['plays'].strip()
                if not url:
                    continue

                try:
                    # Validate URL
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"

                    parsed = urlparse(url)
                    if 'instagram.com' not in parsed.netloc:
                        print(f"⚠️ Skipping non-Instagram URL: {url}")
                        results['skipped'] += 1
                        continue

                    # Extract reel ID
                    reel_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                    output_file = output_folder / f"{reel_id}—{plays}.mp4"

                    # Skip existing
                    if output_file.exists():
                        print(f"⏩ Exists: {reel_id}—{plays}")
                        results['skipped'] += 1
                        continue

                    # Download with yt-dlp
                    cmd = [
                        'yt-dlp',
                        '-f', 'best',
                        '-o', str(output_file),
                        '--no-check-certificate',
                        '--quiet',
                        url
                    ]

                    print(f"⬇️ Downloading ({i}): {reel_id}")
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        results['success'] += 1
                        print(f"✅ Saved: {reel_id}—{plays}")
                    else:
                        results['failed'] += 1
                        print(f"❌ Failed: {reel_id} | Error: {result.stderr.strip()}")

                    # Anti-rate-limiting delay
                    time.sleep(random.uniform(1, 3))

                except Exception as e:
                    results['failed'] += 1
                    print(f"⚠️ Error processing {url}: {str(e)}")

    except Exception as e:
        print(f"❌ CSV read error: {e}")
        return

    # Print summary
    print("\n📊 Results:")
    print(f"• Total: {sum(results.values())}")
    print(f"• Success: {results['success']}")
    print(f"• Failed: {results['failed']}")
    print(f"• Skipped: {results['skipped']}")
