import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from utils import log

response_count = 0


async def run_scraper(
    url,
    session_file,
    output_dir=Path("output"),
    scroll_count=20,
    scroll_delay=2,
    headless=False,
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless, slow_mo=100
        )  # 👈 adds slight delay between actions
        context = await browser.new_context(storage_state=session_file)
        page = await context.new_page()

        # ✅ Log and hook into all GraphQL requests and responses
        def is_graphql_response(res):
            return "graphql" in res.url and res.status == 200

        def is_relevant_response(res):
            url = res.url
            if is_graphql_response(res):
                return True
            return any(endpoint in url for endpoint in [
                '/api/v1/clips/music'
            ])

        page.on(
            "response",
            lambda response: asyncio.create_task(handle_response(
                response, output_dir)
            )
            if is_relevant_response(response)
            else None,
        )  # type: ignore

        log(f"🔗 Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded")

        # ⚠️ Let Instagram initialize its data
        await asyncio.sleep(5)

        log("📜 Scrolling and watching for requests...")
        for i in range(int(scroll_count)):
            await page.evaluate(
                "window.scrollBy(0, document.body.scrollHeight)"
            )
            log(f"↕️ Scrolled ({i+1}/{scroll_count})")
            await asyncio.sleep(scroll_delay + 2)
            # ⏳ wait longer to let queries fire

        log("✅ Done scrolling. Waiting for any final GraphQL responses...")
        await asyncio.sleep(10)

        await browser.close()
        log(f"💾 Total responses saved: {response_count}")


async def handle_response(response, output_dir):
    global response_count
    try:
        if response.status != 200:
            return
        data = await response.json()
        timestamp = int(datetime.now().timestamp() * 1000)
        if "graphql" in response.url:
            filename = output_dir / f"graphql_{timestamp}.json"
        elif "clips/music" in response.url:
            filename = output_dir / f"rest_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        response_count += 1
        log(f"📦 Saved: {filename.name}")
    except Exception as e:
        log(f"❌ Error saving response: {e}")
