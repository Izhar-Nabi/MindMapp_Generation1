from playwright.sync_api import sync_playwright, TimeoutError
import json
import os
import math

def extract_all_links_with_submenus(url, headless=False, output_file="header_links.json"):
    """
    Extracts all header links, including from simple dropdowns and complex mega menus.
    It hovers over each potential parent item and scrapes any revealed sub-menus.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=100)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        all_links = []

        try:
            print(f"🌐 Visiting: {url}")
            # page.goto(url, wait_until="networkidle")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # --- STEP 1: Scrape all initially visible header links ---
            print("🕵️‍♀️ Extracting initially visible top-level header links...")
            header_selector = "header a"
            initial_links = page.eval_on_selector_all(
                header_selector,
                """els => els
                    .filter(e => e.href && e.offsetParent !== null) // Filter for visible links
                    .map(e => ({
                        text: e.innerText.trim(),
                        href: e.href
                    }))"""
            )
            all_links.extend(initial_links)
            print(f"✅ Found {len(initial_links)} initial visible links.")

            # --- STEP 2: Iterate and scrape sub-menus (simple and mega) ---
            # This selector finds any LI in the header that contains a sub_menu (UL or DIV)
            parent_menu_selector = "header li:has(ul.sub_menu), header li:has(div.sub_menu)"
            
            print(f"🔍 Looking for parent menu items with selector: '{parent_menu_selector}'")
            parent_locators = page.locator(parent_menu_selector)
            
            parent_count = parent_locators.count()

            if parent_count == 0:
                print("ℹ️ No hoverable parent menu items found. The initial scan is complete.")
            else:
                print(f"✅ Found {parent_count} parent menu items. Now scraping sub-menus one by one...")
                
                for i in range(parent_count):
                    parent_item = parent_locators.nth(i)
                    try:
                        # Find the main link of the parent to get its text
                        parent_link = parent_item.locator("a").first
                        parent_text = parent_link.inner_text()
                        print(f"\n Hovering over '{parent_text.splitlines()[0].strip()}'...")
                        
                        parent_link.hover(timeout=5000)
                        
                        # Wait for either type of sub-menu to become visible
                        submenu_locator = parent_item.locator("ul.sub_menu, div.sub_menu").first
                        submenu_locator.wait_for(state="visible", timeout=5000)
                        
                        # Use a more robust JS evaluator to get text from various elements
                        submenu_links = submenu_locator.locator("a").evaluate_all(
                            """els => els.filter(e => e.href).map(e => {
                                let text = '';
                                // Try to find a heading or specific text element first
                                const heading = e.querySelector('h1, h2, h3, h4, h5');
                                if (heading) {
                                    text = heading.innerText;
                                } else {
                                    // Fallback to the link's own text content
                                    text = e.innerText;
                                }
                                // If still no text, try the image alt text
                                if (!text || text.trim() === '') {
                                    const img = e.querySelector('img');
                                    if (img && img.alt) {
                                        text = img.alt;
                                    }
                                }
                                return { text: text.trim(), href: e.href };
                            })"""
                        )
                        
                        if submenu_links:
                            print(f"  ➡️ Found {len(submenu_links)} sub-menu links.")
                            all_links.extend(submenu_links)
                        
                    except TimeoutError:
                        print("  ⚠️ Timed out waiting for a sub-menu to appear. Skipping.")
                    except Exception as e:
                        print(f"  ⚠️ Could not process a sub-menu: {e}")

            # --- STEP 3: Clean and de-duplicate the master list ---
            print("\n🧹 Cleaning and de-duplicating all collected links...")
            unique_links = []
            # seen_hrefs = set()

            for link in all_links:
                text = link.get("text", "").strip()
                href = link.get("href", "").strip()
                if href==url:
                    continue
                if text=="":
                    text = href.rstrip('/').split('/')[-1] 
                    unique_links.append({"text": text, "href": href})
                else:
                    unique_links.append({"text": text, "href": href})

            #     if "\n" in text:
            #         text = text.split("\n")[0].strip()

            #     if not text or not href or href.startswith("javascript:") or href in seen_hrefs:
            #         continue
                
            #     seen_hrefs.add(href)
            #     unique_links.append({"text": text, "href": href})

            # --- STEP 4: Save final results ---
            if unique_links:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(unique_links, f, indent=2, ensure_ascii=False)
                print(f"✅ Extracted a total of {len(unique_links)} unique header links. Saved to {output_file}")
                return output_file
            else:
                print("❌ No valid links found after the entire process.")
                return None

        except Exception as e:
            print(f"❌ An error occurred during the process: {e}")
            return None
        finally:
            browser.close()
            
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
    links_file = extract_all_links_with_submenus(target_url, headless=False)

    if links_file:
        print(f"\n🎉 Process complete. Check the file: {links_file}")
    else:
        print("\n🚫 Process finished without creating a file.")