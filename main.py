import argparse # noqa : F401
import asyncio
import glob # noqa : F401
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from insta_login import login_instagram
from intrecept import run_scraper
from reels import load_all_data, write_csv

CONFIG_FILE = Path(".scraper_config.json")


def load_config():
    if not CONFIG_FILE.exists():
        default = {
        "url": "",
        "output_dir": "",
        "scroll_count": "",
        "scroll_delay": "",
        "headless": "",
       }
        save_config(default)
    with open(CONFIG_FILE, "r") as f:
            return json.load(f)




def load_credentials():
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    if not username or not password:
        print("❌ Please provide USERNAME and PASSWORD in .env")
        exit(1)
    return username, password


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print("✅ Config saved to .scraper_config.json")


def prompt_for_config():
    url = input("🔗 Instagram Reels URL: ")
    output_dir = input("📁 Output folder [default: output]: ") or "output"

    scroll_count = int(input("🔃 Scroll count [default: 20]: ") or 20)
    scroll_delay = int(input("⏳ Scroll delay (seconds) [default: 2]: ") or 2)
    headless_input = input("🕶️ Run headless? (y/n) [default: n]: ") or "n"
    headless = headless_input.lower() == "y"
    OUTPUT_DIR = Path(str(output_dir))
    OUTPUT_DIR.mkdir(exist_ok=True)
    return {
        "url": url,
        "output_dir": output_dir,
        "scroll_count": scroll_count,
        "scroll_delay": scroll_delay,
        "headless": headless,
    }


def main():
    parser = argparse.ArgumentParser(description="📸 Instagram Reels Scraper")
    subparsers = parser.add_subparsers(dest="command")

    # Command: config
    subparsers.add_parser("config", help="Setup scraper configuration interactively")

    # Command: login
    subparsers.add_parser("login", help="Login using credentials in .env and save session")

    # Command: scrape
    subparsers.add_parser("scrape", help="Scrape Instagram Reels using saved session and config")

    # Command: extract
    extract_parser = subparsers.add_parser("extract", help="Convert saved JSONs to summarized CSV")
    config = load_config()
    output_file = config.get('output_dir') + '.csv' if config.get('output_dir') else "reels_summary.csv" # noqa E501

    extract_parser.add_argument(
        "-o", "--output",
        default=output_file,
        help="Output CSV filename"
    )
    extract_parser.add_argument(
        "-sbp", "--sort-by-plays",
        action="store_true",
        help="Sort output by play count"
    )
    extract_parser.add_argument(
        "-sbl", "--sort-by-likes",
        action="store_true",
        help="Sort output by like count"
    )
    extract_parser.add_argument(
        "-sbe", "--sort-by-engagement",
        action="store_true",
        help="Sort output by engagement rate (%)"
    )

    # Command: download
    # Dynamically find latest CSV
    csv_files = sorted(glob.glob("*.csv"), key=os.path.getmtime, reverse=True)
    latest_csv = csv_files[0] if csv_files else "reels_summary.csv"
    download_parser = subparsers.add_parser("download", help="Download reels from summary CSV")
    download_parser.add_argument(
        "-i", "--input",
        default=latest_csv,
        help=f"Input CSV file containing reel URLs [default: {latest_csv}]"
    )
    download_parser.add_argument(
        "-o", "--output",
        default="downloads",
        help="Base output folder to save downloaded videos"
    )
    args = parser.parse_args()

    if args.command == "config":
        config = prompt_for_config()
        save_config(config)

    elif args.command == "login":
        config = load_config()
        username, password = load_credentials()
        asyncio.run(login_instagram(username, password, headless=config.get("headless")))

    elif args.command == "scrape":
        config = load_config()
        if not Path("insta_session.json").exists():
            username, password = load_credentials()
            asyncio.run(login_instagram(username, password, headless=config.get("headless")))
        asyncio.run(run_scraper(
            url=config["url"],
            session_file=Path("insta_session.json"),
            output_dir=Path(config["output_dir"]),
            scroll_count=config["scroll_count"],
            scroll_delay=config["scroll_delay"],
            headless=config["headless"],
        ))

    elif args.command == "extract":

        config = load_config()
        output_dir = Path(config.get("output_dir"))
        output_csv = args.output 
        rows = load_all_data(output_dir)
        # write_csv(rows, output_csv)
    
        def sort_key(row):
            keys = []
            if args.sort_by_plays:
                keys.append(float(row["plays"] or 0))  # .replace("M", "e6").replace("K", "e3")
            if args.sort_by_likes:
                keys.append(float(row["likes"] or 0))  # .replace("M", "e6").replace("K", "e3")
            if args.sort_by_engagement:
                keys.append(float(row["engagement_rate"].replace("%", "")))
            return tuple(-k for k in keys) if keys else 0

        if args.sort_by_plays or args.sort_by_likes or args.sort_by_engagement:
            rows.sort(key=sort_key)

        write_csv(rows, output_csv)

    elif args.command == "download":
        from downloader import download_reels_from_csv
        csv_path = Path(args.input)
        output_base = Path(args.output)
        #  downloads/{csv filename}/
        output_dir = output_base / csv_path.stem
        print(f"csv_path : {csv_path}")
        print(f"output_base : {output_base}")
        print(f"output_dir : {output_dir}")
        async def download():
            await  download_reels_from_csv(
            csv_path=csv_path,
            output_folder=output_dir
        )
        asyncio.run(download())
    else:
        parser.print_help()


if __name__ == "__main__":
    try:

        main()
    except KeyboardInterrupt:
        print("Interrupted!!!")
