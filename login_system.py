
from playwright.sync_api import sync_playwright
import json, time, os
from dotenv import load_dotenv

load_dotenv()

def login_to_site(page, username, password):
    """Handles login (including popup/modals) for a given page."""
    print("🔍 Looking for login button or form...")

    login_selectors = [
        "a:has-text('Login')",
        "button:has-text('Login')",
        "text=Log in",
        "text=Sign in",
        "text=My Account",
    ]

    login_found = None
    for selector in login_selectors:
        try:
            page.wait_for_selector(selector, timeout=4000)
            login_found = selector
            break
        except:
            continue

    if login_found:
        print(f"✅ Found login trigger: {login_found}")
        page.click(login_found)
        time.sleep(2)
    else:
        print("⚠️ No login button found — maybe already on login page")

    # ---- detect username / password fields ----
    user_selectors = [
        "input[name='username']",
        "input[id*='user']",
        "input[id*='email']",
        "input[type='email']",
    ]
    pass_selectors = [
        "input[name='password']",
        "input[id*='pass']",
        "input[type='password']",
    ]

    user_input = None
    pass_input = None

    for sel in user_selectors:
        try:
            page.wait_for_selector(f"{sel}:visible", timeout=5000)
            user_input = sel
            break
        except:
            continue

    for sel in pass_selectors:
        try:
            page.wait_for_selector(f"{sel}:visible", timeout=5000)
            pass_input = sel
            break
        except:
            continue

    if not user_input or not pass_input:
        print("❌ Could not find login inputs — skipping login.")
        return False

    print(f"🧠 Filling login form: {user_input}, {pass_input}")
    page.fill(user_input, username)
    page.fill(pass_input, password)

    submit_selectors = [
        "button[type='submit']",
        "button:has-text('Login')",
        "button:has-text('Sign in')",
        "input[type='submit']",
    ]

    for selector in submit_selectors:
        try:
            page.click(selector)
            break
        except:
            continue

    print("⏳ Waiting after login...")
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    print("✅ Login process completed.")
    return True