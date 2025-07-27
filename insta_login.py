# import asyncio
import json
import os
from playwright.async_api import async_playwright
from pathlib import Path
from dotenv import load_dotenv

from utils import log

# Load environment variables from the .env file (if present)
load_dotenv()

# Your Instagram credentials
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# Folder to store login session
STORAGE_FILE = "insta_session.json"


async def login_instagram(username=USERNAME, password=PASSWORD, headless=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        # Set True if you want headless
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

        log("✅ Logged in. Checking for 'Save Info' dialog...")
        try:

            save_info_btn_xpath = '''
            //*[@id="mount_0_0_+b"]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/section/div/button''' # noqa E501

            save_button = page.locator(save_info_btn_xpath)

            # await save_button.wait_for(state="visible", timeout=10000)
            await save_button.click()
            log("💾 Clicked 'Save Info'")

        except Exception as e:
            log(f"⚠️ 'Save Info' dialog not found. Proceeding...\nError: {e}")
        # ✅ Save session
        session_data = await context.storage_state()
        Path(STORAGE_FILE).write_text(json.dumps(session_data))
        log(f"✅ Session saved to {STORAGE_FILE}")

        await browser.close()
