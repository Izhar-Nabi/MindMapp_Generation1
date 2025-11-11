import os
import xml.etree.ElementTree as ET

def merge_mindmaps(base_folder="."):
    mindmap_folder = os.path.join(base_folder, "mindmaps_After_Login")
    output_path = os.path.join(base_folder, "Full_Website_Structure_After_Login.mm")
    website_name=base_folder.split(".")[-2]
    # --- Find the master mindmap file dynamically ---
    master_path = None
    for file_name in os.listdir(mindmap_folder):
        if "home" in file_name.lower() and file_name.endswith(".mm"):
            master_path = os.path.join(mindmap_folder, file_name)
            break
    
    if not master_path:
        raise FileNotFoundError(f"❌ No 'Home' mindmap found in {mindmap_folder}")
    """
    Merge all subpage .mm mindmaps into their respective nodes under the 'Header' node
    in the master mindmap (e.g., merge About.mm into Header -> About).
    """

    # Validate paths
    if not os.path.exists(mindmap_folder):
        raise FileNotFoundError(f"❌ Mindmap folder not found: {mindmap_folder}")

    print(f"🔍 Loading master mindmap: {master_path}")
    # --- Handle missing Home.mm
    if not os.path.exists(master_path):
        print(f"⚠️ Master mindmap not found at {master_path}. Creating a new one...")
        os.makedirs(os.path.dirname(master_path), exist_ok=True)

        # Create base XML structure
        root = ET.Element("map", version="1.0.1")
        home_node = ET.SubElement(root, "node", TEXT=website_name)
        header_node = ET.SubElement(home_node, "node", TEXT="Header")

        master_tree = ET.ElementTree(root)
        master_tree.write(master_path, encoding="utf-8", xml_declaration=True)
        print(f"✅ Created new master mindmap with root '{website_name}' and 'Header' node.")
    else:
        print(f"🔍 Loading master mindmap: {master_path}")
        master_tree = ET.parse(master_path)

    master_root = master_tree.getroot()

    # --- Ensure there's a 'Header' node
    header_node = None
    for node in master_root.findall(".//node"):
        if node.attrib.get("TEXT", "").strip().lower() == "header":
            header_node = node
            break

    if header_node is None:
        print("⚠️ No 'Header' node found — creating one under root.")
        root_node = master_root.find(".//node")
        header_node = ET.SubElement(root_node, "node", TEXT="Header")

    print("📂 Found or created Header node. Beginning smart merge...")

    # --- Loop through all subpage mindmaps
    for file_name in os.listdir(mindmap_folder):
        if not file_name.lower().endswith(".mm"):
            continue
        if file_name.lower() in ["home.mm", "full_website_structure_after_login.mm"]:
            continue

        page_name = os.path.splitext(file_name)[0].strip()
        sub_path = os.path.join(mindmap_folder, file_name)

        print(f"\n🔗 Processing {file_name} → {page_name.title()}")

        try:
            sub_tree = ET.parse(sub_path)
            sub_root = sub_tree.getroot().find(".//node")

            if sub_root is None:
                print(f"⚠️ Skipped (no valid root node in {file_name})")
                continue

            # --- Find matching node under Header (case-insensitive)
            target_node = None
            for node in header_node.findall(".//node"):
                if node.attrib.get("TEXT", "").strip().lower() == page_name.lower():
                    target_node = node
                    break

            # --- If not found, create a new node under Header
            if target_node is None:
                target_node = ET.SubElement(header_node, "node", TEXT=page_name.title())
                print(f"🆕 Created new header subnode for '{page_name}'")

            # --- Append all children from subpage mindmap
            sub_children = sub_root.findall("./node")
            if not sub_children:
                print(f"⚠️ No subnodes found in {file_name}.")
                continue

            for child in sub_children:
                target_node.append(child)

            print(f"✅ Merged '{page_name}' content into Header → {target_node.attrib.get('TEXT')}")

        except Exception as e:
            print(f"❌ Error merging {file_name}: {e}")

    # --- Save final merged mindmap
    ET.indent(master_tree, space="  ")
    master_tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"\n✅ Full merged mindmap saved as: {output_path}")


# if __name__ == "__main__":
#     merge_mindmaps()
