# import os
# import json
# import asyncio
# import base64
# from playwright.async_api import async_playwright # pyright: ignore[reportMissingImports]
# from openai import OpenAI # type: ignore
# from dotenv import load_dotenv # type: ignore
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import re
# from opik import configure 
# from opik.integrations.openai import track_openai 

# # -------------------------------
# # CONFIGURATION
# # -------------------------------
# def configure_openai():
#     """Configure OpenAI GPT client with Opik tracing."""
#     load_dotenv()
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#     if not OPENAI_API_KEY:
#         raise ValueError("❌ OPENAI_API_KEY not found in .env file.")
    
#     # Initialize Opik
#     configure()
#     client = OpenAI(api_key=OPENAI_API_KEY)
#     return track_openai(client)
# # load_dotenv()
# # api_key = os.getenv("OPENAI_API_KEY")
# # if not api_key:
# #     raise ValueError("❌ OPENAI_API_KEY not found in .env file")
# # client = OpenAI(api_key=api_key)
# client= configure_openai()
# def normalize_text(text: str) -> str:
#     """Normalize text for consistent matching."""
#     text = text.lower()
#     text = re.sub(r'[^a-z0-9\s]', ' ', text)  # remove symbols
#     text = re.sub(r'\s+', ' ', text)  # collapse spaces
#     return text.strip()

# def find_best_url_match(target_name, url_map, threshold=0.85):
#     """Finds the best URL match using cosine similarity on normalized text."""
#     if not url_map:
#         return None

#     normalized_map = {normalize_text(k): v for k, v in url_map.items()}
#     target_norm = normalize_text(target_name)

#     keys = list(normalized_map.keys())
#     vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
#     vectors = vectorizer.fit_transform([target_norm] + keys)
#     sims = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

#     best_index = sims.argmax()
#     best_score = sims[best_index]

#     if best_score >= threshold:
#         matched_key = keys[best_index]
#         print(f"🤝 Cosine match → '{target_name}' ≈ '{matched_key}' (score={best_score:.2f})")
#         return matched_key
#     else:
#         print(f"⚠️ No cosine match (max={best_score:.2f}) for {target_name}")
#         return None
# # -------------------------------
# # FUNCTION: TAKE SCREENSHOT
# # -------------------------------
# async def take_screenshot(url, name, screenshot_folder):
#     """Takes a full-page screenshot and saves it in /screenshots"""
#     print(f"📸 Taking screenshot of {url}...")
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         try:
#             await page.goto(url, wait_until="domcontentloaded", timeout=120000)
#             await page.wait_for_timeout(5000)
#             screenshot_path = os.path.join(screenshot_folder, f"{name}.png")
#             await page.screenshot(path=screenshot_path, full_page=True)
#             print(f"📸 Screenshot saved: {screenshot_path}")
#             return screenshot_path
#         except Exception as e:
#             print(f"❌ Failed to load {url}: {e}")
#             return None
#         finally:
#             await browser.close()


# # -------------------------------
# # FUNCTION: GENERATE MINDMAP USING GEMINI
# # -------------------------------
# def generate_mindmap_from_screenshot(image_path, page_name, all_links,output_folder):
#     """Generate a .mm mindmap file based on webpage screenshot and links."""
#     # Convert image to bytes
#     with open(image_path, "rb") as f:
#         image_data = f.read()

#     # 🧠 Smart Prompt for Gemini
#     if page_name.lower() in ["home", "homepage"]:
#          return None
#     else:
#         prompt = f"""
#         You are MindArchitect-GPT, an advanced assistant that converts webpage screenshots and link data into clean FreeMind (.mm) XML mind maps.

#         🧠 BACKSTORY
#         You specialize in analyzing visual webpage structures and producing valid, concise XML hierarchies representing content flow, forms, and UI elements.

#         🎯 PURPOSE
#         Produce a .mm file that represents only the page-specific visible content, excluding the header and footer.

#         🧩 POMAL FRAMEWORK
#         **P (Purpose):** Create a hierarchical mindmap of the webpage structure.  
#     **O (Objective):** Capture meaningful sections, forms, buttons, and links based on the screenshot and link data.  
#     **M (Method):**
#     1. Visually interpret the screenshot layout.  
#     2. Group content into clear sections (e.g., “Hero Section,” “About,” “Contact,” etc.).  
#     3. If a section is text-only → summarize its visible text in one short descriptive line.  
#     4. If a section includes forms, buttons, or links → represent those as nested nodes.  
#     5. Use provided link data for hyperlink nodes.  
#     6. Properly escape XML entities (`& → &amp;`, `< → &lt;`, `>` → &gt;`). 
#     **A (Action):**
#     - Output strictly valid XML conforming to FreeMind format.  
#     - Each node should have meaningful `TEXT` attributes and `LINK` if available.  
#     - Use single-line summaries for long paragraphs.  
#     **L (Limitations):**
#     - Do **not** output markdown, commentary, or plain text explanations.  
#     - Properly escape XML entities (`& → &amp;`, `< → &lt;`, `>` → &gt;`).  
#     - Do **not** duplicate header or footer nodes.
    
#         🧭 STRUCTURE RULES (for non-Home pages)
#         1. Root node: "{page_name}"  
#     2. Skip all Header and Footer elements.  
#     3. Organize main content hierarchically:
#     - Page Title  
#         - Main Content  
#             - Visible Section 1  
#             - Visible Section 2  
#             - Forms  
#             - Buttons  
#     4. For **forms**:
#     - Represent each input field as a child node.  
#     - Include buttons with their visible text.  
#     5. For **buttons**:
#     - Use visible button text or purpose (e.g., "Submit Form", "Learn More").  
#     6. For **text-only sections**:
#     - Create a node named after its visible heading or logical title.
#     - Inside, add one summary node that captures the text meaning in one line (no full paragraphs).
#     7 For **links**:
#     - Use `LINK` attributes for clickable URLs. 

#     ### 🧩 PROVIDED LINKS
#         Use only these links when adding `LINK` attributes:
#         {json.dumps(all_links, indent=2)}

#         💡 FEW-SHOT EXAMPLE
#         **Example 1 — Text-Only Section**

# **Input Context:**
# Screenshot shows a section with heading "About Us" and 3 short paragraphs about the company mission.
# No buttons or forms visible.



# **Expected Output:**

# <map version="1.0.1">
#   <node TEXT="About Page">
#     <node TEXT="Main Content">
#       <node TEXT="About Us">
#         <node TEXT="We are a tech-driven company focused on building sustainable digital solutions."/>
#       </node>
#     </node>
#   </node>
# </map>
# Example 2 — Section With Buttons

# Input Context:


# Section title: "Join Our Team"
# Visible button: "Apply Now"
# Link: https://example.com/careers
# Expected Output:


# <map version="1.0.1">
#   <node TEXT="Careers Page">
#     <node TEXT="Main Content">
#       <node TEXT="Join Our Team">
#         <node TEXT="Apply Now" LINK="https://example.com/careers"/>
#       </node>
#     </node>
#   </node>
# </map>
# Example 3 — Form Section

# Input Context:



# Section: Contact Us
# Fields: Name, Email, Message
# Button: Send Message
# Link: https://example.com/contact
# Expected Output:

# xml

# <map version="1.0.1">
#   <node TEXT="Contact Page">
#     <node TEXT="Main Content">
#       <node TEXT="Contact Form">
#         <node TEXT="Name Field"/>
#         <node TEXT="Email Field"/>
#         <node TEXT="Message Field"/>
#         <node TEXT="Send Message" LINK="https://example.com/contact"/>
#       </node>
#     </node>
#   </node>
# </map>
    
# 🪄 OUTPUT REQUIREMENTS

# Output only valid XML — no markdown or prose.

# Maintain indentation, hierarchy, and clean one-line summaries for text-only sections.

# Output must be directly usable as a .mm file.

# Now, using the provided screenshot and link context, generate the .mm XML mindmap for the page titled {page_name}.
#         """
        
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4.1",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
#                             },
#                         },
#                     ],
#                 }
#             ],
#             temperature=0.0,
#         )
#         mindmap_content = response.choices[0].message.content.strip()
#         lines= mindmap_content.splitlines()
#         if len(lines) > 2:
#             lines = lines[1:-1]
#         # Ensure valid .mm extension file is saved
#         cleaned_mindmap = "\n".join(lines).strip()
#         output_path = os.path.join(output_folder, f"{page_name}.mm")
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write(cleaned_mindmap)

#         print(f"🧭 Mindmap generated → {output_path}")
#         return output_path

#     except Exception as e:
#         print(f"❌ Error generating mindmap for {page_name}: {e}")
#         return None


# # -------------------------------
# # MAIN FUNCTION (FOR INTEGRATION)
# # -------------------------------
# async def generate_mindmaps_from_headers(
#     base_folder=".",  # 👈 new argument to represent the domain folder (e.g., "example.com")
#     headers_folder=None,
#     extracted_headers_path=None,
#     output_folder=None,
#     screenshot_folder=None
# ):
#     """
#     Main pipeline:
#     1. Reads all header JSONs.
#     2. Takes screenshots.
#     3. Calls OpenAI to create .mm mindmaps.
#     """


#     # --- Resolve all folder paths relative to base_folder ---
#     if headers_folder is None:
#         headers_folder = os.path.join(base_folder, "headers")
#         print(f"####################################### base folder {base_folder}#################################################")
#     if extracted_headers_path is None:
#         extracted_headers_path = os.path.join(base_folder, "header_links.json")
#     if output_folder is None:
#         output_folder = os.path.join(base_folder, "mindmaps")
#     if screenshot_folder is None:
#         screenshot_folder = os.path.join(base_folder, "screenshots")

#     # --- Ensure output directories exist ---
#     os.makedirs(output_folder, exist_ok=True)
#     os.makedirs(screenshot_folder, exist_ok=True)
#     # --- Load extracted header links ---
#     with open(extracted_headers_path, "r", encoding="utf-8") as f:
#         header_data = json.load(f)

#     header_url_map = {
#         normalize_text(item["text"]): item["href"]
#         for item in header_data if "href" in item
#     }
#     all_outputs = []
#     # --- Input validation ---
#     print(f"Checking for headers folder at: {headers_folder}")
#     if not os.path.exists(headers_folder):
#         print(f"❌ Folder '{headers_folder}' not found.")
#         return

#     if not os.path.exists(extracted_headers_path):
#         print(f"❌ File '{extracted_headers_path}' not found.")
#         return

#     # --- Load extracted header links ---
#     with open(extracted_headers_path, "r", encoding="utf-8") as f:
#         header_data = json.load(f)

#     all_outputs = []

#     # --- Process each header JSON file ---
#     for header_file in sorted(os.listdir(headers_folder)):
#         if not header_file.endswith(".json"):
#             continue

#         page_name = os.path.splitext(header_file)[0]
#         header_path = os.path.join(headers_folder, header_file)

#         try:
#             with open(header_path, "r", encoding="utf-8") as f:
#                 all_links = json.load(f)
#         except Exception as e:
#             print(f"⚠️ Failed to load {header_file}: {e}")
#             continue

#         if not all_links:
#             print(f"⚠️ No links found in {header_file}. Skipping...")
#             continue

#         page_url = header_url_map.get(normalize_text(page_name))
#         print(f"🔍 Mapped page name '{page_name}' to URL: {page_url}")

#         if not page_url:
#             print(f"🔍 Trying cosine match for '{page_name}'...")
#             matched_key = find_best_url_match(page_name, header_url_map)
#             if matched_key:
#                 page_url = header_url_map.get(matched_key)
#         if not page_url:
#             print(f"⚠️ No matching URL found for '{page_name}' in header_links.json. Skipping...")
#             continue

#         print(f"\n🌐 Processing: {page_name.upper()} ({page_url})")

#         # --- Take screenshot ---
#         screenshot_path = await take_screenshot(page_url, page_name, screenshot_folder)
#         if not screenshot_path:
#             print(f"⚠️ Screenshot failed for {page_name}")
#             continue

#         # --- Generate mindmap using OpenAI ---
#         output_path = generate_mindmap_from_screenshot(
#             screenshot_path, page_name, all_links, output_folder
#         )

#         if output_path:
#             all_outputs.append(output_path)

#     print(f"\n✅ All mindmaps generated successfully in: {output_folder}")
#     return all_outputs



# # -------------------------------
# # Allow running standalone
# # -------------------------------
# # if __name__ == "__main__":
# #     asyncio.run(generate_mindmaps_from_headers())

#!/usr/bin/env python3
"""
Header-based pages → chunked screenshots → multi-stage GPT → FreeMind mindmaps
"""
import os
import re
import json
import time
import math
import textwrap
import base64
from io import BytesIO
from typing import List, Dict
import xml.etree.ElementTree as ET


from dotenv import load_dotenv
from openai import OpenAI
from opik import configure as opik_configure
from opik.integrations.openai import track_openai
from PIL import Image
import asyncio
from playwright.async_api import async_playwright

# Optional tiktoken for token counting
try:
    import tiktoken
    from tiktoken import encoding_for_model
    TIKTOKEN_AVAILABLE = True
except Exception:
    TIKTOKEN_AVAILABLE = False

# -------------------------
# CONFIG
# -------------------------
MAX_INPUT_TOKENS = 1_000_000
CHUNK_MODEL = "gpt-4.1"
FINAL_MODEL = "gpt-4.1"
IMAGE_TOKEN_OVERHEAD = 85
IMAGE_BYTES_PER_TOKEN = 771
COMPRESS_IMAGES = True
COMPRESS_MAX_WIDTH = 1200
TRUNCATE_PREV_TOKENS = 200000

# -------------------------
# Utilities
# -------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def configure_openai_with_opik() -> OpenAI:
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found in environment.")
    opik_configure()
    client = OpenAI(api_key=key)
    return track_openai(client)

# -------------------------
# Images
# -------------------------
def compress_image_to_base64(path: str, max_width: int = COMPRESS_MAX_WIDTH) -> str:
    with Image.open(path) as img:
        if img.width > max_width:
            ratio = max_width / float(img.width)
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

def load_images_as_base64(folder_path: str, compress: bool = COMPRESS_IMAGES) -> List[Dict]:
    valid_ext = {".png", ".jpg", ".jpeg", ".webp"}
    imgs = []
    for filename in sorted(os.listdir(folder_path)):
        if not any(filename.lower().endswith(e) for e in valid_ext):
            continue
        fp = os.path.join(folder_path, filename)
        if compress:
            b64 = compress_image_to_base64(fp)
            raw_bytes = base64.b64decode(b64)
        else:
            with open(fp, "rb") as fh:
                raw = fh.read()
            b64 = base64.b64encode(raw).decode("utf-8")
            raw_bytes = raw
        imgs.append({"filename": filename, "base64": b64, "bytes_len": len(raw_bytes), "path": fp})
    return imgs

def estimate_image_tokens_from_bytes(image_bytes_len: int) -> int:
    return IMAGE_TOKEN_OVERHEAD + (image_bytes_len // IMAGE_BYTES_PER_TOKEN)

def count_text_tokens_for_model(model: str, text: str) -> int:
    if TIKTOKEN_AVAILABLE:
        try:
            enc = encoding_for_model(model)
            return len(enc.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)

def chunk_images_by_token_limit(model: str, prompt_text: str, images: List[Dict], max_tokens: int = MAX_INPUT_TOKENS) -> List[List[Dict]]:
    batches = []
    current_batch = []
    current_tokens = count_text_tokens_for_model(model, prompt_text)
    for img in images:
        img_tokens = estimate_image_tokens_from_bytes(img["bytes_len"])
        if current_tokens + img_tokens > max_tokens:
            if current_batch:
                batches.append(current_batch)
            current_batch = [img]
            current_tokens = count_text_tokens_for_model(model, prompt_text) + img_tokens
            if current_tokens > max_tokens:
                print(f"⚠️ Single image '{img['filename']}' exceeds token limit ({current_tokens})")
                batches.append(current_batch)
                current_batch = []
                current_tokens = count_text_tokens_for_model(model, prompt_text)
        else:
            current_batch.append(img)
            current_tokens += img_tokens
    if current_batch:
        batches.append(current_batch)
    return batches

def build_messages(prompt_text: str, previous_output: str, images_batch: List[Dict]) -> list:
    content_items = [{"type": "text", "text": prompt_text}]
    if previous_output:
        content_items.append({"type": "text", "text": previous_output})
    for img in images_batch:
        content_items.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img['base64']}"}})
    return [
        {"role": "system", "content": "You are an expert in website information architecture and FreeMind XML."},
        {"role": "user", "content": content_items},
    ]

def truncate_text_to_token_budget(model: str, text: str, token_budget: int) -> str:
    if not text:
        return ""
    if TIKTOKEN_AVAILABLE:
        try:
            enc = encoding_for_model(model)
            tokens = enc.encode(text)
            if len(tokens) <= token_budget:
                return text
            return enc.decode(tokens[-token_budget:])
        except Exception:
            pass
    return text[-token_budget*4:]

# -------------------------
# Playwright screenshot
# -------------------------
async def take_chunked_screenshots(url: str, page_name: str, screenshot_folder: str,
                                  partition_height: int = 1600, scroll_increment: int = 400) -> List[str]:
    out_dir = os.path.join(screenshot_folder, page_name)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)

        # ⭐ NEW: Wait 2 seconds to allow all content to load
        await page.wait_for_timeout(2000)
        total_height = await page.evaluate("document.documentElement.scrollHeight")
        page_width = await page.evaluate("document.documentElement.scrollWidth")
        for y in range(0, total_height, scroll_increment):
            await page.evaluate(f"window.scrollTo(0,{y})")
            await page.wait_for_timeout(150)
        await page.evaluate(f"window.scrollTo(0,{total_height})")
        await page.wait_for_timeout(400)
        num_chunks = math.ceil(total_height / partition_height)
        for i in range(num_chunks):
            top = i * partition_height
            height = min(partition_height, total_height - top)
            await page.set_viewport_size({"width": page_width, "height": height})
            await page.evaluate(f"window.scrollTo(0,{top})")
            await page.wait_for_timeout(200)
            path = os.path.join(out_dir, f"image_{i+1}.png")
            await page.screenshot(path=path)
            paths.append(path)
        await browser.close()
    return paths

# -------------------------
# Multi-stage orchestrator
# -------------------------
def multi_stage_mindmap_generation(client, model: str, prompt_text: str, images: List[Dict], output_file: str) -> str:
    batches = chunk_images_by_token_limit(model, prompt_text, images, MAX_INPUT_TOKENS)
    previous_output = ""
    final_output = None
    for idx, batch in enumerate(batches, start=1):
        prev_for_call = truncate_text_to_token_budget(model, previous_output, TRUNCATE_PREV_TOKENS) if previous_output else ""
        messages = build_messages(prompt_text, prev_for_call, batch)
        resp = client.chat.completions.create(model=model, temperature=0.0, messages=messages)
        msg_text = resp.choices[0].message.content.strip()
        previous_output = msg_text
        final_output = msg_text
    if not final_output:
        raise RuntimeError("No output from GPT")
    start = final_output.find("<map")
    if start == -1:
        with open(output_file+".raw.txt","w",encoding="utf-8") as fh:
            fh.write(final_output)
        raise ValueError("Output missing <map> XML; raw saved.")
    mm_xml = final_output[start:]
    if mm_xml.endswith("```"):
        mm_xml = mm_xml[:-3].strip()
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file,"w",encoding="utf-8") as fh:
        fh.write(mm_xml)
    return output_file

# -------------------------
# Prompt builder
# -------------------------
def build_mindmap_prompt(page_name: str, all_links: List[Dict]) -> str:
    if page_name.lower() in ["home", "homepage"]:
        return None
    return textwrap.dedent(f"""
        You are an intelligent assistant specialized in generating structured, professional website mind maps
            in valid FreeMind (.mm) XML format.

            ### 🎯 Objective
            Analyze the provided webpage screenshot, context, and extracted links to create a clear, hierarchical mind map 
            that accurately represents the *page content and structure* of the website.

            The generated mind map will help visualize the layout, navigation, and interactive elements of the webpage.

            ---

            ### 🧭 Core Rules & Structure
            1. The **root node** must always be the page title: "{page_name}".
            2. **Exclude** all elements that belong to the **Header** or **Footer**.
            - Do not include header menus, site logos, navigation bars, or footer links.
            - Use the provided screenshot as a reference to visually identify and exclude these.
            3. Focus only on **page-specific visible content** (the body section).
            - Include meaningful text sections, visible links, content blocks, images, and widgets.
            - Don't include all content of text, only the main headings and sections summary in one line.
            - Don't use more then two nodes for content , if any link or buttonn is present in the visible section then use that as the new node text.
            - Make sure to make visible sections heading based on content inside it 
            - Don't duplicate it 
            4. The hierarchy should follow the logical layout of the page:
            - Page Title
                - Main Content
                - Visible Sections
                - Forms (if any)
                - Buttons (if any)
            5. **Forms**:
            - Represent each form as a node.
            - Add its fields (e.g., text inputs, dropdowns, submit buttons) as child nodes.
            6. **Buttons**:
            - Represent each button as a node.
            - Use the visible button text or function as its subnode.
            7. **Links**:
            - Only include links that exist in the provided list below:
                {json.dumps(all_links, indent=2)}
            - Skip duplicate or irrelevant links.
            8. Every visible major section of the webpage should be represented as a main node.
            9. Each node must be enriched with relevant **links**, **buttons**, and **form fields** 
            based on the provided data and visible content.
        🧩  Output Formatting Rules
            Output only valid FreeMind XML — no markdown, explanations, or comments.

            The structure must begin with:

            xml
            Copy code
            <map version="1.0.1">
                <node TEXT="{page_name}">
                    ...
                </node>
            </map>
            All nodes must use proper indentation and XML escaping for special characters.

            Ensure the output is fully parsable by FreeMind or Freeplane (no syntax errors).

            🪄 Summary
            Your goal:

            Accurately extract and represent all visible, meaningful, and interactive elements of the page content.

            Exclude any part of the header or footer.

            Return only the valid .mm XML output.
            
    """).strip()

def replace_ampersand_with_space(input_file, output_file=None):
    """
    Replace '&' with a space in all node TEXT attributes inside a FreeMind (.mm) file,
    even if the XML has unescaped ampersands.
    """
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    if output_file is None:
        output_file = input_file

    # 🔧 Read raw text and fix invalid '&' before parsing
    with open(input_file, "r", encoding="utf-8") as f:
        xml_text = f.read()

    # Replace only ampersands that are NOT part of &amp;, &lt;, etc.
    xml_text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_text)

    # Parse the fixed XML
    root = ET.fromstring(xml_text)

    count = 0
    for node in root.iter("node"):
        text = node.get("TEXT")
        if text and "&" in text:
            print(f"replacing {text}")
            new_text = text.replace("&", " ")
            node.set("TEXT", new_text)
            count += 1

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ Replaced '&' with spaces in {count} nodes → {output_file}")


# -------------------------
# Page processor
# -------------------------
async def process_page(client, page_name: str, page_url: str, all_links: List[Dict],
                       screenshot_folder: str = "screenshot", output_folder: str = "mindmaps"):
    print(f"\n=== Processing page: {page_name} → {page_url} ===")
    chunk_paths = await take_chunked_screenshots(page_url, page_name, screenshot_folder)
    images = []
    for cp in chunk_paths:
        imgs = load_images_as_base64(os.path.dirname(cp), compress=True)
        images.extend([i for i in imgs if os.path.abspath(i["path"]) == os.path.abspath(cp)])
    if not images:
        print(f"⚠️ No images for {page_name}")
        return None
    prompt = build_mindmap_prompt(page_name, all_links)
    output_file = os.path.join(output_folder, f"{page_name}.mm")
    try:
        multi_stage_mindmap_generation(client, CHUNK_MODEL, prompt, images, output_file)
        replace_ampersand_with_space(output_file,output_file)
        print(f"✅ Mindmap saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Failed for {page_name}: {e}")
        return None

# -------------------------
# Main orchestrator
# -------------------------
async def generate_mindmaps_from_headers(headers_folder="headers",
                                         extracted_headers_path="header_links.json",
                                         output_folder="mindmaps",
                                         screenshot_folder="screenshot"):
    client = configure_openai_with_opik()
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(screenshot_folder, exist_ok=True)

    if not os.path.exists(headers_folder) or not os.path.exists(extracted_headers_path):
        print("❌ Headers folder or header_links.json not found.")
        return

    with open(extracted_headers_path,"r",encoding="utf-8") as fh:
        header_data = json.load(fh)
    header_url_map = {normalize_text(item["text"]): item["href"] for item in header_data if "href" in item}

    for header_file in sorted(os.listdir(headers_folder)):
        if not header_file.lower().endswith(".json"):
            continue
        page_name = os.path.splitext(header_file)[0]
        with open(os.path.join(headers_folder, header_file),"r",encoding="utf-8") as fh:
            all_links = json.load(fh)
        if not all_links:
            continue
        page_url = header_url_map.get(normalize_text(page_name))
        if not page_url:
            continue
        await process_page(client, page_name, page_url, all_links, screenshot_folder, output_folder)

    print("\n✅ All pages processed.")

# -------------------------
# Entrypoint
# -------------------------
if __name__ == "__main__":
    try:
        asyncio.run(generate_mindmaps_from_headers())
    except KeyboardInterrupt:
        print("Interrupted by user")
