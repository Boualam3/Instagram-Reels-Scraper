# import os
import random
import asyncio
# from pathlib import Path
from urllib.parse import urlparse
from utils import load_csv_rows


async def download_reels_from_csv(
    csv_path=None, output_folder=None,
    notify=None, should_stop=None, single_url=None
):
    """
    Downloads Instagram reels from CSV  or Signle URL if exists

    Args:
        csv_path (Path): Path to CSV file
        output_folder (Path): Directory to save downloads
    """
    # Create output directory
    output_folder.mkdir(parents=True, exist_ok=True)

    async def log(msg):
        if notify:
            from nicegui import run

            await run.io_bound(lambda: notify(msg))
        else:
            print(msg)

    async def run_download(url, output_file):
        cmd = [
                'yt-dlp',
                '-f', 'best',
                '-o', str(output_file),
                '--no-check-certificate',
                '--quiet',
                url
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    # Download a single URL
    if single_url:
        url = single_url.strip()
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        reel_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        output_file = output_folder / f"{reel_id}.mp4"
        if output_file.exists():
            await log(f"⏩ Already exists: {reel_id}")
            return
        await log(f"⬇️ Downloading: {reel_id}")

        returncode, _, stderr = await run_download(url, output_file)
        if returncode == 0:
            await log(f"✅ Saved: {reel_id}")
        else:
            await log(f"❌ Failed: {reel_id} | Error: {stderr.strip()}")
        return

    # Full CSV Mode
    rows = load_csv_rows(csv_path)
    if not rows:
        await log("❌ No rows found in CSV.")
        return

    # Track results
    results = {'success': 0, 'failed': 0, 'skipped': 0}

    for i, row in enumerate(rows, 1):
        url = row['url'].strip() if row.get('url') else ""
        plays = row['plays'].strip() if row.get('plays') else ""
        if not url:
            continue

        if should_stop and should_stop():
            await log("🛑 Download stopped.")
            break

        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"

            parsed = urlparse(url)
            if 'instagram.com' not in parsed.netloc:
                await log(f"⚠️ Skipping non-Instagram URL: {url}")
                results['skipped'] += 1
                continue

            # Extract reel ID
            reel_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            output_file = output_folder / f"{reel_id}—{plays}.mp4"

            # Skip existing
            if output_file.exists():
                await log(f"⏩ Exists: {reel_id}—{plays}")
                results['skipped'] += 1
                continue

            await log(f"⬇️ Downloading ({i}): {reel_id}")
            returncode, _, stderr = await run_download(url, output_file)

            if returncode == 0:
                results['success'] += 1
                await log(f"✅ Saved: {reel_id}—{plays}")
            else:
                results['failed'] += 1
                await log(f"❌ Failed: {reel_id} | Error: {stderr.strip()}")

            # Anti-rate-limiting delay
            await asyncio.sleep(random.uniform(1, 2.5))

        except Exception as e:
            results['failed'] += 1
            print(f"⚠️ Error processing {url}: {str(e)}")

    await log("\n📊 Results:")
    await log(f"• Total: {sum(results.values())}")
    await log(f"• Success: {results['success']}")
    await log(f"• Failed: {results['failed']}")
    await log(f"• Skipped: {results['skipped']}")

