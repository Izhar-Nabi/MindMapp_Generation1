import xml.etree.ElementTree as ET
import re
import sys
import os

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


if __name__ == "__main__":
    input_path = r"lionsandtigers\mindmaps\home.mm"
    output_path = r"lionsandtigers\mindmaps\home.mm"
    replace_ampersand_with_space(input_path, output_path)
