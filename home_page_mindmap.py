import os
import json
import asyncio
import re
import base64
from playwright.async_api import async_playwright
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

def configure_openai():
    """Configure OpenAI GPT API client."""
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY not found. Please set it in your .env file.")
    return OpenAI(api_key=OPENAI_API_KEY)

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

def generate_home_mindmap_from_screenshot(client, output_folder,page_name,screenshot_path):
    print("🚀 Generating Home Page mindmap from screenshot...")
    with open(page_name, "r", encoding="utf-8") as f:    
        all_links = json.load(f)
    with open(screenshot_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    prompt=f"""
        You are an intelligent assistant specialized in generating professional website mind maps 
                in valid FreeMind (.mm) XML format.

                ### Objective
                Analyze the provided webpage screenshot, context, and extracted links to generate a clear and 
                hierarchical mind map representing the website's structure and navigation.

                ### Rules & Structure
                1. The root node must always be the page title: .
                2. If the page title is "Home" (or "Homepage"):
                - It must include the **Header**, **Footer** as subnodes.
                - All other pages (e.g., About, Services, Contact, Login, Signup, etc.) should appear 
                    as subnodes of the Home Page Header.
                - The **Header** and **Footer** should only exist once — under the Home Page.
                3. For non-home pages:
                - The **Header** and **Footer** must **not** be repeated.
                - Only include page-specific sections, forms, buttons, and visible links and content.
                4. Every visible major section of the webpage should be represented as a main node.
                5. Each node must be enriched with relevant **links**, **buttons**, and **form fields** 
                based on the provided data and visible content.
                6. Only include links that exist in the provided list:
                {json.dumps(all_links, indent=2)}
                8. If the page has forms:
                - Represent each form as a node.
                - Add its form fields (e.g., text boxes, dropdowns, submit buttons) as subnodes.
                9. If the page has buttons:
                - Represent each button as a node.
                - Include the visible button text or purpose as its subnode.
                10. Ensure logical grouping and a consistent hierarchy reflecting the webpage layout.
                12. Maintain clean hierarchy — for example:
                    - Home Page
                    - Header
                        - Navigation Links
                        - Main Content
                        - Visible Sections
                    - Footer
                13. Output must be valid XML conforming to FreeMind (.mm) syntax.
                14. **Do not** include any commentary, markdown formatting, or explanations in the output.

                ### Expected Output
                Return only a valid FreeMind (.mm) XML file structure representing the page hierarchy, 
                with proper nesting, link grouping, and visible UI elements.
                """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in website information architecture and FreeMind XML."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                    ]
                }
            ],
        )

        mindmap_content = response.choices[0].message.content.strip()
        start_index = mindmap_content.find("<map")
        if start_index == -1:
            raise ValueError("Gemini output does not contain valid <map> XML structure.")

        mindmap_content = mindmap_content[start_index:].strip()
        # 🧹 Remove closing ``` if present
        if mindmap_content.endswith("```"):
            mindmap_content = mindmap_content[:-3].strip()
            
        os.makedirs(output_folder, exist_ok=True)
        # output_path = os.path.join(output_folder, f"{"home"}.mm")
        filename = "home"
        output_path = os.path.join(output_folder, f"{filename}.mm")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(mindmap_content)

        print(f"🧭 Mindmap generated → {output_path}")
        replace_ampersand_with_space(output_path,output_path)
        return output_path

    except Exception as e:
        print(f"❌ Error generating mindmap for: {e}")
        return None
# if __name__ == "__main__":
#     client = configure_openai()
#     output_folder="mindmaps"
#     # generate_home_mindmap_from_screenshot(client, output_folder)
#     replace_ampersand_with_space("lionsandtigers\mindmaps\home.mm","lionsandtigers\mindmaps\home.mm")
