import os
import json
from openai import OpenAI # type: ignore
from dotenv import load_dotenv # type: ignore
from opik import configure 
from opik.integrations.openai import track_openai 
import re
import xml.etree.ElementTree as ET


# Load environment variables from .env file
load_dotenv()
def configure_openai():
    """Configure OpenAI GPT client with Opik tracing."""
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("❌ OPENAI_API_KEY not found in .env file.")
    
    # Initialize Opik
    configure()
    client = OpenAI(api_key=OPENAI_API_KEY)
    return track_openai(client)

# Files
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

def validation(base_folder="."):
    MM_FILE = os.path.join(base_folder, "Merged_Website_Structure.mm")
    OUTPUT_FILE = os.path.join(base_folder, "Full_Website_Structure_updated.mm")
    header_file = os.path.join(base_folder,"header_links.json")
    print(base_folder)
    print(header_file)
    # Load OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY not found in .env file")
    client = configure_openai()

    # Load files
    with open(MM_FILE, "r", encoding="utf-8") as f:
        mm_content = f.read()
    with open(header_file, "r") as f: # C:\Users\izhar.nabi\Desktop\vscod\MindMap\mindmap_web_app\340bpriceguide.net\header_links.json
        data = json.load(f)
    
    texts = [item["text"] for item in data]

    user_prompt = """
    Generate a valid FreeMind (.mm) XML file that represents a complete website structure.

    ✅ Requirements:
    1. The first node must be "Home Page".
    2. The "Home Page" must contain three subnodes:
    - Header
    - Main Content
    - Footer
    3. The "Header" and "Footer" should appear only once, under the Home Page. The content inside them should not include in any other page.
    4. Every other page (e.g.,Search, About, Contact, Login(if present), Signup(if present), etc.) must be direct subnodes of the header .
    5. Each page node must include all its UI elements (buttons, forms, links, and content) as nested subnodes.
    6. If any page contains subpages, represent them as child nodes under that page.
    7. Maintain a clear hierarchical structure that accurately reflects parent-child relationships between pages and their components.
    8. If a link’s {texts} contains “login”, “log in”, “sign up”, or “signup” (case-insensitive), then include it as a subnode under the Home Page
    9. Ensure all nodes are properly nested and the XML is valid.
    10. Use hyperlinks (LINK attribute) for nodes that represent pages, linking to their respective URLs.
    11. Properly escape XML entities (`& → &amp;`, `< → &lt;`, `>` → &gt;`). 
    The output must be a well-formed .mm (FreeMind) XML mindmap file without any extra commentary.
    """

    system_prompt = """
    You are an assistant that validates and constructs FreeMind (.mm) XML mindmap files.
    You will receive:
    1. The original .mm file (XML format).
    2. The user's instructions.

    Your job:
    - Validate that the .mm structure matches the specified hierarchy and requirements.
    - Ensure the file includes all expected nodes, subnodes, buttons, links, and forms.
    - Fix any missing or misplaced elements while preserving valid XML formatting.
    - Output only the corrected .mm XML file without explanations or comments.
    """

    full_prompt = f"""
    User instruction:
    {user_prompt}

    Original Mindmap (.mm):
    {mm_content}

    Final hirarchical structure must be:
    Home Page
    ├── Header
    ├── [Other Pages like About, Contact ,search etc.]
    |---Home Page Content
    ├── Footer
    ├── Login(if present )
    ├── Signup(if present )

    """

    # Call GPT
    response = client.chat.completions.create(
        model="gpt-4.1",   # or "gpt-4o-mini" if you want faster/cheaper
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ],
        temperature=0
    )
    mindmap_content = response.choices[0].message.content.strip()

        # 🧹 CLEAN: Remove markdown or extra text before XML
    start_index = mindmap_content.find("<map")
    if start_index == -1:
        raise ValueError("OpenAI output does not contain valid <map> XML structure.")

    mindmap_content = mindmap_content[start_index:].strip()
    # 🧹 Remove closing ``` if present
    if mindmap_content.endswith("```"):
        mindmap_content = mindmap_content[:-3].strip()
    # Save updated mindmap
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(mindmap_content)

    replace_ampersand_with_space(OUTPUT_FILE,OUTPUT_FILE)
    print(f"✅ Updated mindmap saved as {OUTPUT_FILE}")


# if __name__ == "__main__":
#     validation()
