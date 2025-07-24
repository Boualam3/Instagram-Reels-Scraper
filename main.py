import argparse
import asyncio
import json
import os
from dotenv import load_dotenv
from pathlib import Path
from insta_login import login_instagram
from intrecept import run_scraper
from reels import load_all_data, write_csv

CONFIG_FILE = Path(".scraper_config.json")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    else:
        print("❌ Config not found. Please run `python main.py config` first.")
        exit(1)


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
    extract_parser.add_argument(
        "-o", "--output",
        default="reels_summary.csv",
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

    args = parser.parse_args()

    if args.command == "config":
        config = prompt_for_config()
        save_config(config)

    elif args.command == "login":
        config = load_config()
        load_dotenv()
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        if not username or not password:
            print("❌ Please provide USERNAME and PASSWORD in .env")
            exit(1)
        asyncio.run(login_instagram(username, password, headless=config.get("headless")))

    elif args.command == "scrape":
        config = load_config()
        if not Path("insta_session.json").exists():
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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
