import json
import csv
from pathlib import Path

DATA_DIR = Path("./output2/")
OUTPUT_CSV = "reels_summary_2.csv"

def format_number(count):
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.0f}K"
    return str(count)

def extract_media_info(json_path):
    with open(json_path, encoding="utf-8") as f:
        try:
            content = json.load(f)
            edges = content.get("data", {}) \
                           .get("xdt_api__v1__clips__user__connection_v2", {}) \
                           .get("edges", [])
        except Exception as e:
            print(f"Error parsing {json_path}: {e}")
            return []

    results = []
    for edge in edges:
        media = edge.get("node", {}).get("media", {})
     #    user = media.get("user", {})

        # Find highest-res thumbnail
     #    candidates = media.get("image_versions2", {}).get("candidates", [])
     #    thumbnail_url = None
     #    if candidates:
     #        thumbnail_url = max(candidates, key=lambda c: c.get("width", 0)).get("url")
        plays = media.get("play_count", 0)
        likes = media.get("like_count", 0)
        engagement = round((likes / plays * 100), 2) if plays else 0.0
        results.append({
	     "url": f"instagram.com/reel/{media.get('code')}/" if media.get("code") else "",
		"plays": plays,
		"likes": likes,
		"engagement_rate": f"{engagement:.2f}%",
		})


    return results

def load_all_data(data_dir):
    all_rows = []
    for json_file in data_dir.glob("query_*.json"):
        all_rows.extend(extract_media_info(json_file))
    return all_rows

def write_csv(rows, output_file):
    # Sort by play_count descending
    rows.sort(key=lambda r: r.get("play_count", 0), reverse=True)
    if not rows:
        print("No data to write.")
        return

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[✓] Wrote {len(rows)} rows to {output_file}")

if __name__ == "__main__":
    rows = load_all_data(DATA_DIR)
    formatted_rows = [
        {**item,"plays":format_number(item.get("plays",0) or 0), "likes":format_number(item.get("likes",0) or 0)} for item in  rows]

    write_csv(formatted_rows, OUTPUT_CSV)
