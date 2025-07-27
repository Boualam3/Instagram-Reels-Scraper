from nicegui import ui
import asyncio
import json
import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from insta_login import login_instagram
from intrecept import run_scraper
from reels import load_all_data, write_csv
from utils import load_csv_rows
from downloader import download_reels_from_csv
from urllib.parse import urlparse

CONFIG_FILE = Path(".scraper_config.json")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_credentials():
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    if not username or not password:
        ui.notify("Missing USERNAME or PASSWORD in .env", color="negative")
        raise SystemExit
    return username, password


with ui.tabs().classes('w-full flex justfy-center items-center') as tabs:
    config_tab = ui.tab('Config')
    login_tab = ui.tab('Login')
    scrape_tab = ui.tab('Scrape')
    extract_tab = ui.tab('Extract')
    download_tab = ui.tab('Download')

with ui.tab_panels(tabs, value=config_tab).classes('w-full'):

    with ui.tab_panel(config_tab):
        config = load_config()

        url = ui.input("🔗 Instagram Reels URL", value=config.get("url", ""))
        output_dir = ui.input("📁 Output folder", value=config.get("output_dir", "output"))
        scroll_count = ui.number("🔃 Scroll count", value=config.get("scroll_count", 20))
        scroll_delay = ui.number("⏳ Scroll delay (s)", value=config.get("scroll_delay", 2))
        headless = ui.checkbox("🕶️ Run headless", value=config.get("headless", False))

        def save_conf():
            OUTPUT_DIR = Path(output_dir.value)
            OUTPUT_DIR.mkdir(exist_ok=True)
            conf = {
                "url": url.value,
                "output_dir": output_dir.value,
                "scroll_count": scroll_count.value,
                "scroll_delay": scroll_delay.value,
                "headless": headless.value,
            }
            save_config(conf)
            ui.notify("✅ Config saved")

        ui.button("Save Config", on_click=save_conf).classes("mt-4")

    with ui.tab_panel(login_tab):
        def login():
            config = load_config()
            username, password = load_credentials()
            asyncio.create_task(login_instagram(username, password, headless=config.get("headless"))) # noqa E501
            ui.notify("✅ Login started (check logs)")

        ui.button("Login with .env Credentials", on_click=login).classes("mt-4")

    with ui.tab_panel(scrape_tab):
        def scrape():
            config = load_config()
            if not Path("insta_session.json").exists():
                username, password = load_credentials()
                asyncio.run(login_instagram(username, password, headless=config.get("headless")))

            asyncio.create_task(run_scraper(
                url=config["url"],
                session_file=Path("insta_session.json"),
                output_dir=Path(config["output_dir"]),
                scroll_count=config["scroll_count"],
                scroll_delay=config["scroll_delay"],
                headless=config["headless"],
            ))
            ui.notify("✅ Scraping started")

        ui.button("Start Scraping", on_click=scrape).classes("mt-4")

    with ui.tab_panel(extract_tab):
        # Radio for sorting criteria (only one can be selected)
        sort_option = ui.radio(
            options=["Sort by Plays", "Sort by Likes", "Sort by Engagement"],
            value="Sort by Plays"
        ).classes("mb-4")

        # Create the table with empty data initially
        table = ui.table(
            rows=[],
            columns=[
                {'name': 'url', 'label': 'URL', 'field': 'url', 'align': 'left'},
                {'name': 'plays', 'label': 'Plays', 'field': 'plays', 'align': 'left'},
                {'name': 'likes', 'label': 'Likes', 'field': 'likes', 'align': 'left'},
                {'name': 'engagement_rate', 'label': 'Engagement Rate', 'field': 'engagement_rate', 'align': 'left'},
            ],
            row_key='url',
            pagination=10
        ).classes("w-full mt-4")

        # Add slot for clickable URL
        table.add_slot('body-cell-url', '''
            <q-td :props="props">
                <a :href="'https://' + props.value" target="_blank" rel="noopener noreferrer" style="color: #1976d2; text-decoration: underline;">
                    {{ props.value }}
                </a>
            </q-td>
        ''') # noqa E501

        def extract():
            config = load_config()
            output_dir = Path(config.get("output_dir"))
            output_csv = output_dir.name + ".csv"
            rows = load_all_data(output_dir)
            
            def sort_key(row):
                def parse_value(value):
                    if isinstance(value, (int, float)):
                        return float(value)
                    if isinstance(value, str):
                        value = value.replace(",", "").replace(" ", "")
                        if "M" in value:
                            return float(value.replace("M", "")) * 1_000_000
                        if "K" in value:
                            return float(value.replace("K", "")) * 1_000
                        return float(value)
                    return 0.0

                if sort_option.value == "Sort by Plays":
                    return -parse_value(row.get("plays", 0))
                elif sort_option.value == "Sort by Likes":
                    return -parse_value(row.get("likes", 0))
                elif sort_option.value == "Sort by Engagement":
                    engagement = row.get("engagement_rate", "0%")
                    if isinstance(engagement, str):
                        return -float(engagement.replace("%", ""))
                    return -float(engagement)
                return 0

            rows.sort(key=sort_key)
            table.rows = rows
            write_csv(rows, output_csv)
            ui.notify(f"✅ Extracted to {output_csv}")

        # Button to trigger extraction and display
        ui.button("Extract CSV", on_click=extract).classes("mt-4")

    with ui.tab_panel(download_tab):
        config = load_config()
        csv_files = sorted(glob.glob("*.csv"), key=os.path.getmtime, reverse=True)
        default_csv = csv_files[0] if csv_files else "reels_summary.csv"

        input_csv = ui.input("CSV filename", value=default_csv)
        output_base = ui.input("Output base folder", value="downloads")
        log = ui.log().classes("max-h-60 overflow-auto text-sm")
        progress = ui.linear_progress(show_value=True).classes("mt-2")

        def stop_download():
            global should_stop_download
            should_stop_download = True
            ui.notify("\u274c Stopping download...")

        async def download():
            global should_stop_download
            should_stop_download = False

            log.clear()
            csv_path = Path(input_csv.value)
            out_base = Path(output_base.value)
            output_dir = out_base / csv_path.stem

            rows = load_csv_rows(csv_path)
            total = len(rows)
            progress.set_value(0)

            for i, row in enumerate(rows):
                if should_stop_download:
                    log.push("🛑 Download stopped by user.")
                    break

                url = row["url"]
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"

                parsed = urlparse(url)
                if 'instagram.com' not in parsed.netloc:
                    log.push(f"⚠️ Skipping non-Instagram URL: {url}")

                    continue

                # Extract reel ID
                reel_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                log.push(f"⬇️ Downloading {reel_id}...")

                try:
                    await download_reels_from_csv(
                        csv_path=None,  # not needed per-row
                        output_folder=output_dir,
                        notify=log.push,
                        should_stop=lambda: should_stop_download,
                        single_url=url,
                    )
                    log.push(f"✅ Done {reel_id}")
                except Exception as e:
                    log.push(f"❌ Failed {reel_id}: {e}")

                progress.set_value(round(((i + 1) / total) * 100))

            if not should_stop_download:
                ui.notify("✅ All downloads complete")
        ui.button("Download Reels", on_click=lambda: asyncio.create_task(download())).classes("mt-4") # noqa E501
        ui.button("Stop", on_click=stop_download).classes("mt-2")

ui.run()
