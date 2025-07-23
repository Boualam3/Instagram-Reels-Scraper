import asyncio
import json
import os
from playwright.async_api import async_playwright
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file (if present)
load_dotenv()

# 🔐 Your Instagram credentials
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# 💾 Folder to store login session
STORAGE_FILE = "insta_session.json"

async def login_instagram():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set True if you want headless
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")

        # ⏳ Wait for username field
        await page.wait_for_selector("input[name='username']")

        # 💬 Fill credentials
        await page.fill("input[name='username']", USERNAME)
        await page.fill("input[name='password']", PASSWORD)

        # 🔐 Click login
        await page.click("button[type='submit']")

        print("✅ Logged in. Checking for 'Save Info' dialog...")
        try:
            # Wait and click "Save Info" button
            await page.wait_for_selector("text=Save info", timeout=5000)
            await page.click("text=Save info")
            print("💾 Clicked 'Save Info'")
        except:
        	  print("⚠️ 'Save Info' dialog not found. Proceeding...")
        # ✅ Save session
        session_data = await context.storage_state() #type:ignore
        Path(STORAGE_FILE).write_text(json.dumps(session_data))
        print(f"✅ Session saved to {STORAGE_FILE}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(login_instagram())
