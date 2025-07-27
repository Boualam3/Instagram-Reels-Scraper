import json
import csv
from utils import log


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
            log(f"Error parsing {json_path}: {e}")
            return []

    results = []
    for edge in edges:
        media = edge.get("node", {}).get("media", {})

        reel_link = f"instagram.com/reel/{media.get('code')}/" if media.get("code") else ""
        plays = media.get("play_count", 0)
        likes = media.get("like_count", 0)
        engagement = round((likes / plays * 100), 2) if plays else 0.0
        results.append({
            "url": reel_link ,
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
    # Sort by plays descending

    rows.sort(key=lambda r: r.get("plays") or 0, reverse=True)
    if not rows:
        log("No data to write.")
        return
    formatted_rows = [
        {
            **item,
            "plays": format_number(item.get("plays") or 0),
            "likes": format_number(item.get("likes") or 0)
        } for item in rows
    ]
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(formatted_rows)

    log(f"[✓] Wrote {len(rows)} rows to {output_file}")


def sort_by(rows, csvfile):
    pass
