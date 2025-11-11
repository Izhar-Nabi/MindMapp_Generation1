from lxml import etree as ET
import os

def collapse_all_nodes(input_file, output_file=None):
    """Collapse all <node> elements by setting FOLDED='true'."""
    if output_file is None:
        output_file = input_file  # overwrite input if no output specified

    print(f"🔍 Reading mindmap: {input_file}")
    parser = ET.XMLParser(remove_blank_text=False)
    tree = ET.parse(input_file, parser)
    root = tree.getroot()

    count = 0
    for node in root.iter("node"):
        node.set("FOLDED", "true")
        count += 1

    # Write back, preserving <richcontent> sections
    tree.write(
        output_file,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )

    print(f"✅ Collapsed {count} nodes in: {output_file}")


# ========================
# Runner Example
# ========================
if __name__ == "__main__":
    INPUT_MM = r""
    OUTPUT_MM = r"dayzee\Full_Website_Structure_updated_with_descriptions.mm"

    if not os.path.exists(INPUT_MM):
        print("❌ Input file not found.")
    else:
        collapse_all_nodes(INPUT_MM, OUTPUT_MM)
