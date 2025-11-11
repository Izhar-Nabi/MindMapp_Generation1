import os
import re
import asyncio
import xml.etree.ElementTree as ET
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError # pyright: ignore[reportMissingImports]

# === CONFIG ===
# INPUT_MM = "Full_Website_Structure_After_Login_updated.mm"
# OUTPUT_MM = "Full_Website_Structure_After_Login_updated_with_Screenshot.mm"
# SCREENSHOT_DIR = "hyperlink_screenshots_After_Login"
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
AUTH_STATE = "auth_state.json"  # 🔹 Saves login session here

# === LOGIN CONFIG ===
LOGIN_URL = "https://www.340bpriceguide.net/client-login"
# DEFAULT_USERNAME = os.getenv("SITE_USERNAME", "")
# DEFAULT_PASSWORD = os.getenv("SITE_PASSWORD", "")


# os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def safe_filename(url: str) -> str:
    safe = re.sub(r"[<>:\"/\\|?*=&#%@]", "_", url)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:150]


async def login_and_get_context(url,p, username, password, headless=True):
    """Logs in (or reuses saved session) and returns authenticated context."""
    browser = await p.chromium.launch(headless=headless)
    context = None

    if os.path.exists(AUTH_STATE):
        print("♻️ Using saved login session (auth_state.json)...")
        context = await browser.new_context(
            storage_state=AUTH_STATE,
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
            ignore_https_errors=True
        )
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        if "Logout" in (await page.content()):
            print("✅ Session still valid, skipping login.")
            await page.close()
            return browser, context
        print("⚠️ Saved session expired — logging in again.")
        await page.close()
        await context.close()

    # 🚀 Fresh login
    context = await browser.new_context(
        ignore_https_errors=True,
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
    )
    page = await context.new_page()

    print("🌐 Opening login page...")
    await page.goto(LOGIN_URL, timeout=90000)
    await page.wait_for_load_state("networkidle")

    # Wait for login form fields
    print("🔐 Waiting for login form fields...")
    try:
        await page.wait_for_selector("#username", timeout=20000)
        await page.wait_for_selector("#password", timeout=20000)
        # Fill credentials
        print(f"🔑 Logging in as {username}")
        await page.fill("#username", username)
        await page.fill("#password", password)

        # Optional checkbox
        try:
            await page.check("input[type='checkbox']")
        except Exception:
            pass

        # Click Log In
        try:
            await page.click("button.btn.btn-primary")
        except PlaywrightTimeoutError:
            await page.get_by_role("button", name="Log in").click()

        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        html = await page.content()
        if any(keyword in html for keyword in ["Logout", "Dashboard", "Welcome"]):
            print("✅ Login successful — session saved.")
            await context.storage_state(path=AUTH_STATE)
        else:
            print("⚠️ Could not confirm login — screenshots may fail for protected pages.")
    except Exception as e:
        print(f"Initial login attempt failed: {e}")
        print("Trying popup login...")
        await page.goto(url, timeout=90000)
        login_selectors = [
            "a:has-text('Login')", "button:has-text('Login')", "text=Log in",
            "text=Sign in", "text=My Account",
        ]
        for selector in login_selectors:
            try:
                await page.click(selector, timeout=5000)
                await page.wait_for_load_state("networkidle")
                await page.fill("#username", username)
                await page.fill("#password", password)
                await page.click("button.btn.btn-primary")
                await page.wait_for_load_state("networkidle")
                html = await page.content()
                if any(keyword in html for keyword in ["Logout", "Dashboard", "Welcome"]):
                    print("✅ Popup login successful — session saved.")
                    await context.storage_state(path=AUTH_STATE)
                    break
            except Exception as popup_error:
                print(f"Popup login attempt with '{selector}' failed: {popup_error}")
                continue

    return browser, context


async def take_screenshot(context, url: str, filename: str):
    """Capture screenshot while authenticated."""
    page = await context.new_page()
    try:
        await page.goto(url, timeout=90000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await page.screenshot(path=filename)
        print(f"📸 Screenshot captured for {url}")
    except Exception as e:
        print(f"❌ Failed to capture {url}: {e}")
    await page.close()


def add_screenshot_node(parent_node, screenshot_path):
    """Attach screenshot node to the mindmap node."""
    for child in parent_node.findall("node"):
        if child.get("TEXT") == "Screenshot Example":
            return

    node = ET.Element("node", TEXT="Screenshot Example")
    rich = ET.SubElement(node, "richcontent", TYPE="NODE")
    screenshot_path = screenshot_path.replace("\\","/")
    html_str = f"""
    <html>
      <body>
        <p>
        <img src="{screenshot_path}" width="950" height="500"/>
        </p>
      </body>
    </html>
    """.strip()

    html_elem = ET.fromstring(html_str)
    rich.append(html_elem)
    parent_node.append(node)


async def Screenshot(username, password, base_folder=".", headless=True):
    INPUT_MM = os.path.join(base_folder, "Full_Website_Structure_After_Login_updated.mm")
    OUTPUT_MM = os.path.join(base_folder, "Full_Website_Structure_After_Login_updated_with_Screenshot.mm")
    SCREENSHOT_DIR = os.path.join(base_folder, "hyperlink_screenshots_After_Login")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser, context = await login_and_get_context(p, username, password, headless=headless)
        tree = ET.parse(INPUT_MM)
        root = tree.getroot()

        for node in root.iter("node"):
            link = node.get("LINK")
            if link and link.startswith(("http://", "https://")):
                safe_name = safe_filename(link)
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")
                relative_path = os.path.join(os.path.basename(SCREENSHOT_DIR), f"{safe_name}.png").replace("\\", "/")

                if os.path.exists(screenshot_path):
                    print(f"⏩ Skipping existing screenshot: {screenshot_path}")
                else:
                    await take_screenshot(context, link, screenshot_path)

                add_screenshot_node(node, relative_path)

        tree.write(OUTPUT_MM, encoding="utf-8", xml_declaration=True)
        print(f"\n💾 Updated mindmap saved as: {OUTPUT_MM}")

        await browser.close()

# def screenshort_node_after_login():
#     if __name__ == "__main__":
#         asyncio.run(Screenshot())
