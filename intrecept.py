import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# 🔧 Config
# INSTAGRAM_REELS_URL = "https://www.instagram.com/reputeforge/reels/"
INSTAGRAM_REELS_URL = "https://www.instagram.com/digital_chadvertising/reels/"

SCROLL_COUNT = 20
SCROLL_DELAY = 2
SESSION_FILE = "insta_session.json"
OUTPUT_DIR = Path("output2")
OUTPUT_DIR.mkdir(exist_ok=True)

# Counter
response_count = 0

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)  # 👈 adds slight delay between actions
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()

        # ✅ Log and hook into all GraphQL requests and responses
        def is_graphql_response(res):
            return "graphql" in res.url and res.status == 200

        def is_graphql_request(req):
            return "graphql" in req.url

        page.on("request", lambda request: print(f"🔍 Request: {request.url}") if is_graphql_request(request) else None)
        page.on("response", lambda response: asyncio.create_task(handle_response(response)) if is_graphql_response(response) else None)

        print(f"🔗 Navigating to: {INSTAGRAM_REELS_URL}")
        await page.goto(INSTAGRAM_REELS_URL, wait_until="domcontentloaded")

        # ⚠️ Let Instagram initialize its data
        await asyncio.sleep(5)

        print("📜 Scrolling and watching for requests...")
        for i in range(SCROLL_COUNT):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            print(f"↕️ Scrolled ({i+1}/{SCROLL_COUNT})")
            await asyncio.sleep(SCROLL_DELAY + 2)  # ⏳ wait longer to let queries fire

        print("✅ Done scrolling. Waiting for any final GraphQL responses...")
        await asyncio.sleep(10)

        await browser.close()
        print(f"💾 Total responses saved: {response_count}")

async def handle_response(response):
    global response_count
    try:
        if "graphql" in response.url and response.status == 200:
            data = await response.json()
            timestamp = int(datetime.now().timestamp() * 1000)
            filename = OUTPUT_DIR / f"query_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            response_count += 1
            print(f"📦 Saved: {filename.name}")
    except Exception as e:
        print(f"❌ Error saving response: {e}")

if __name__ == "__main__":
    asyncio.run(run())
