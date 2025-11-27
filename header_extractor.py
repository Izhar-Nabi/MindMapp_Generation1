from playwright.sync_api import sync_playwright, TimeoutError
import json
import os
import math

def extract_header_links(url, headless=True, output_file="header_links.json"):
    """
    Extract ONLY:
    - Top level header links (text + href)
    - Dropdown submenu links (text + href)
    
    Works for: WordPress, Shopify, custom HTML, mega menus.
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        all_links = []

        # ----------------------------------------
        # 1. Detect <header> tag
        # ----------------------------------------
        header = page.locator("header")
        if header.count() == 0:
            print("❌ No <header> found.")
            return None

        header = header.first

        # ----------------------------------------
        # 2. Extract all top-level <a> links
        # ----------------------------------------
        top_links = header.locator("a[href]").all()

        for link in top_links:
            try:
                text = link.inner_text().strip()
                href = link.get_attribute("href")

                if not href:
                    continue
                if href =="#":
                    continue
                # skip email/tel/js links
                if href.startswith(("javascript:", "mailto:", "tel:","/")):
                    continue

                # Clean text
                if not text:
                    continue

                all_links.append({"text": text, "href": href})

            except:
                pass

        # ----------------------------------------
        # 3. Extract dropdown links by hovering over menu items
        # ----------------------------------------
        menu_items = header.locator("nav a, li > a, li > button").all()

        for item in menu_items:
            try:
                item.hover(timeout=2000)
            except:
                continue

            # Find dropdowns revealed after hover
            dropdown = item.locator(
                """
                xpath=ancestor::li//*[self::ul or self::div][
                    contains(@class, 'menu') or
                    contains(@class, 'dropdown') or
                    contains(@class, 'sub') or
                    contains(@class, 'mega')
                ]
                """
            )

            if dropdown.count() == 0:
                continue

            dd = dropdown.first

            try:
                dd.wait_for(state="visible", timeout=1500)
            except:
                continue

            submenu_links = dd.locator("a[href]").all()

            for sl in submenu_links:
                try:
                    text = sl.inner_text().strip()
                    href = sl.get_attribute("href")

                    if not href:
                        continue
                    if href.startswith(("javascript:", "mailto:", "tel:","/")):
                        continue
                    if href =="#":
                        continue

                    if not text:
                        print(href)
                        continue

                    all_links.append({"text": text, "href": href})

                except:
                    pass

        # ----------------------------------------
        # 4. Clean & dedupe
        # ----------------------------------------
        cleaned = []
        seen = set()

        for link in all_links:
            t = link["text"].strip()
            h = link["href"].strip()

            if (t, h) in seen:
                continue

            seen.add((t, h))
            cleaned.append({"text": t, "href": h})

        # ----------------------------------------
        # 5. Save Output
        # ----------------------------------------
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)

        print(f"✅ Done. Extracted {len(cleaned)} links.")
        return cleaned
            
def home_screenshot(url,output_folder):
    partition_height= 1500
    scroll_increment= 400
    scroll_pause=0.2
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        # -------------------------
        # Scroll slowly to load all lazy content
        # -------------------------
        total_height = page.evaluate("document.body.scrollHeight")
        print(f"📏 Total page height: {total_height}px")

        for y in range(0, total_height, scroll_increment):
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(int(scroll_pause * 1000))  # wait in milliseconds

        # Ensure final scroll to bottom
        page.evaluate(f"window.scrollTo(0, {total_height})")
        page.wait_for_timeout(500)

        # -------------------------
        # Take partitioned screenshots
        # -------------------------
        page_width = page.evaluate("document.body.scrollWidth")
        num_screens = math.ceil(total_height / partition_height)
        print(f"🖼 Number of screenshots: {num_screens}")

        for i in range(num_screens):
            top = i * partition_height
            height = min(partition_height, total_height - top)

            # Resize viewport to current partition height
            page.set_viewport_size({
                "width": page_width,
                "height": height
            })

            # Scroll to top of this partition
            page.evaluate(f"window.scrollTo(0, {top})")
            page.wait_for_timeout(int(scroll_pause * 1000))

            # Screenshot this partition
            file_path = os.path.join(output_folder, f"image_{i+1}.png")
            page.screenshot(path=file_path)
            print(f"✅ Saved: {file_path}")

        browser.close()
    


if __name__ == "__main__":
    target_url = "https://dayzee.com/"
    links_file = extract_header_links(target_url, headless=False)

    if links_file:
        print(f"\n🎉 Process complete. Check the file: {links_file}")
    else:
        print("\n🚫 Process finished without creating a file.")