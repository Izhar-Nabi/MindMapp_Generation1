from playwright.async_api import async_playwright # pyright: ignore[reportMissingImports]
import json
import asyncio
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from dotenv import load_dotenv # type: ignore

# Load credentials from .env file
load_dotenv()

# USERNAME = os.getenv("SITE_USERNAME")
# PASSWORD = os.getenv("SITE_PASSWORD")

BASE_URL = "https://www.340bpriceguide.net"


async def extract_links_from_page(page, page_url):
    """Extract all meaningful links from the current page"""
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else "No Title"

    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        text = a.get_text(strip=True)
        if href and text:
            links.append({
                "page_title": title,
                "hyper_text": text,
                "link": href
            })
    return links


async def extract_header_links_and_screenshots(username, password, base_folder=".", headless=True):
    HEADERS_FOLDER = os.path.join(base_folder, "headers_After_Login")
    SCREENSHOT_FOLDER = os.path.join(base_folder, "screenshots_After_Login")
    os.makedirs(HEADERS_FOLDER, exist_ok=True)
    os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to login page...")
        await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")

        print("🔐 Waiting for login form...")
        await page.wait_for_selector("input[name='username']:visible", timeout=15000)
        await page.wait_for_selector("input[name='password']:visible", timeout=15000)

        print("🔑 Filling credentials...")
        await page.locator("input[name='username']:visible").fill(username)
        await page.locator("input[name='password']:visible").fill(password)

        # Optional checkbox
        try:
            await page.locator("input[type='checkbox']:visible").check()
        except:
            pass

        print("➡️ Clicking 'Log In'...")
        await page.locator("button:has-text('Log In'):visible").click()

        # Wait for login success
        try:
            await page.wait_for_url("**/my-profile", timeout=15000)
            print("✅ Login successful!")
        except:
            print("⚠️ Login may not have redirected yet, waiting for network idle...")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

        # Take screenshot after login
        await page.screenshot(path=os.path.join(SCREENSHOT_FOLDER, "after_login.png"), full_page=True)
        print("📸 Screenshot saved: after_login.png")

        # Extract header links
        print("🔗 Extracting header links...")
        header_links = await page.eval_on_selector_all(
            "header a",
            "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))"
        )

        # Clean links: remove empty or logout links
        clean_links = [
            l for l in header_links
            if l.get("text")
            and "logout" not in l.get("href", "").lower()
            and l.get("text").strip().lower() != "logout"
        ]

        with open(os.path.join(base_folder, "header_links_After_Login.json"), "w", encoding="utf-8") as f:
            json.dump(clean_links, f, indent=2, ensure_ascii=False)
        print(f"✅ Found {len(clean_links)} header links (Logout skipped).")

        # Visit each header link
        for link in clean_links:
            text = link["text"].replace(" ", "_").replace("/", "_")
            href = link["href"]

            print(f"\n🌍 Visiting: {text} → {href}")
            try:
                await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Take screenshot
                screenshot_path = os.path.join(SCREENSHOT_FOLDER, f"{text}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved: {screenshot_path}")

                # Extract links
                links = await extract_links_from_page(page, href)

                # Save links
                output_path = os.path.join(HEADERS_FOLDER, f"{text}.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(links, f, indent=2, ensure_ascii=False)
                print(f"✅ Extracted {len(links)} links → {output_path}")

            except Exception as e:
                print(f"❌ Error processing {href}: {e}")

        await browser.close()
        print("\n🎉 All header pages processed successfully (Logout skipped)!")


# if __name__ == "__main__":
#     if not USERNAME or not PASSWORD:
#         raise ValueError("❌ Please set SITE_USERNAME and SITE_PASSWORD in your .env file")

#     extract_header_links_and_screenshots(USERNAME, PASSWORD, headless=False)
