from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO
from log_emitter import setup_logging, socketio
import logging
from header_extractor1 import extract_all_links_with_submenus
from header_extractor1 import home_screenshot
from home_page_link_extractor import extract_links
from home_page_mindmap import home_page
from Header_link_Extractor import extract_links_from_header_json
from Header_mindmaps import generate_mindmaps_from_headers
from Merge_All_Header_Mindmap import merge_mindmaps
from Validation_Mindmap import validation
from Screenshot_node import Screenshot_Node
from zip import zip_folder
from button_description import process_mindmap
import json
import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()

# CRITICAL: Use ProactorEventLoop for Windows + Playwright subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = Flask(__name__, static_folder='static', static_url_path='/static')
# Set the logging level for socketio and engineio to WARNING to reduce verbosity
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)


setup_logging(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    url = data.get('url')
    # headless = data.get('headless', True)

    username = data.get("username","").strip()
    password = data.get("password","").strip()
    login_url= data.get("login_url","").strip()


    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        logging.info(f"Extracting links from: {url}")
        logging.info(f"logging url {login_url}")
        from domain_extractor import extract_domain
        folder_name = extract_domain(url)
        logging.info("Creating Folder with domain name")
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
            logging.info(f"folder created with {folder_name} name")
        else:
            logging.info(f"!!!!!!!!!!!!!!!!!!! {folder_name} folder already created!!!!!!!!!!!!!")
        # Run the new extractor function
        json_file_path = os.path.join(folder_name, "header_links.json")
        output_folder = os.path.join(folder_name,"screenshot/home")
        home_screenshot(url, output_folder)
        home_link=extract_links(url)
        output_file=os.path.join(folder_name, "home_page_link.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(home_link, f, indent=2)
        logging.info("Home page links and screenshot captured.")
        Screenshot_folder=os.path.join(folder_name,"screenshot/home")
        output_mm_file=os.path.join(folder_name,"mindmaps/home.mm")
        logging.info("Home page mindmap generated.")
        extract_all_links_with_submenus(url, headless=True, output_file=json_file_path)

        # if not links_file or not os.path.exists(links_file):
            # return jsonify({'error': 'Failed to create header_links.json file'}), 500

        # Load the links from the generated file to return them in the response
        with open(json_file_path, "r", encoding="utf-8") as f:
            cleaned_links = json.load(f)
        
        logging.info(f"Successfully extracted {len(cleaned_links)} links.")
        input_file = json_file_path
        try:
            logging.info("🚀 Starting header link extraction process...")

            # --- Extract header links ---
            extract_links_from_header_json(header_json_path=input_file, base_folder=folder_name)
            logging.info("✅ Header links extracted successfully.")

            # --- Determine domain folder from input file ---
            domain_folder = os.path.dirname(input_file)
            if not domain_folder:
                domain_folder = "."

            # --- Define headers folder path ---
            headers_folder = os.path.join(domain_folder, "headers")
            extracted_header_path=os.path.join(domain_folder,"header_links.json")
            output_folder=os.path.join(domain_folder,"mindmaps")
            screenshot_folder=os.path.join(domain_folder,"screenshot")
            home_screenshot_folder=os.path.join(screenshot_folder,"home")
            home_file=os.path.join(domain_folder,"home_page_link.json")
            output_mm_file=os.path.join(domain_folder,"mindmaps","home.mm")
            # --- Check if headers folder exists ---
            if os.path.isdir(headers_folder):
                logging.info(f"📂 Found headers folder {headers_folder}. Starting MindMap generation...")

                # 🧠 Generate MindMaps for all header link files
                asyncio.run(generate_mindmaps_from_headers(headers_folder,extracted_header_path,output_folder,screenshot_folder))
                logging.info("✅ MindMaps created from header links.")
                logging.info("✅ making home mindmap")
                asyncio.run( home_page(home_screenshot_folder,home_file,output_mm_file))
                logging.info("✅ done home mindmap")
                # 🔗 Merge all generated MindMaps
                logging.info("🔄 Merging all header MindMaps...")
                merge_mindmaps(base_folder=domain_folder)
                logging.info("✅ Merged all header MindMaps successfully.")

                # ✅ Validate the final merged structure
                logging.info("🧩 Starting validation...")
                validation(base_folder=folder_name)
                logging.info("✅ Validation complete.")

                # 🖼️ Take screenshots of nodes
                logging.info("📸 Capturing screenshots for MindMap nodes...")
                asyncio.run(Screenshot_Node(base_folder=folder_name))
                logging.info("✅ Screenshots integrated into MindMap.")

                # 👤 Handle login-related processing if credentials provided
                if username and password:
                    logging.info("🔐 Starting login section...")
                    from ScreenShot_node_After_Login import login_and_get_context
                    from playwright.async_api import async_playwright # type: ignore
                    AUTH_STATE=os.path.join(domain_folder,"auth_state.json")

                    async def main_login():
                        async with async_playwright() as p:
                            browser, context = await login_and_get_context(AUTH_STATE,url,p, username, password, headless=True)
                            if context:
                                # Continue with the rest of the after-login process
                                from header_extractor_after_login import extract_main_nav_after_login
                                from header_extractor_after_login import home_screenshot
                                from Header_Links_Ectractor_After_Login import extract_header_links_and_screenshots
                                from Home_page_link_extractor_After_login import extract_home_link
                                from Header_mindmaps_after_login import header
                                from home_page_mindmaps_after_login import home_page
                                from Merge_all_header_mindmap_After_Login import merge_mindmaps
                                from Validation_Mindmap_After_login import validation_after_login
                                
                                output_folder = os.path.join(domain_folder, "screenshots_After_Login", "Home")
                                HEADER_FILE=os.path.join(domain_folder,"header_links_After_Login.json")
                                HEADERS_FOLDER=os.path.join(domain_folder,"headers_After_Login")
                                home_path=os.path.join(domain_folder,"home_page_links_after_login.json")
                                SCREENSHOT_FOLDER=os.path.join(domain_folder,"screenshots_After_Login")
                                MINDMAP_FOLDER = os.path.join(domain_folder,"mindmaps_After_Login")
                                output_mm_file= os.path.join(MINDMAP_FOLDER,"home.mm")
                                await extract_main_nav_after_login(AUTH_STATE,HEADER_FILE, login_url, username, password, headless=True)
                                await home_screenshot(url,output_folder)
                                await extract_header_links_and_screenshots(url,AUTH_STATE,HEADERS_FOLDER)
                                logging.info("Bhai yahan hu ma home ka mindmap bna rha hu")
                                await extract_home_link(AUTH_STATE,url,home_path)
                                await header(url,HEADERS_FOLDER,SCREENSHOT_FOLDER,MINDMAP_FOLDER)
                                home_page(output_folder,home_path,output_mm_file)
                                merge_mindmaps(base_folder=domain_folder)
                                validation_after_login(base_folder=domain_folder)
                            await browser.close()

                    asyncio.run(main_login())

                    logging.info("📸 Capturing screenshots after login...")
                    from ScreenShot_node_After_Login import Screenshot
                    asyncio.run(Screenshot(url,username=username, password=password, base_folder=domain_folder, headless=True))
                    logging.info("✅ Screenshots after login captured.")

                    # 🧠 Merge all MindMaps into a single file
                    logging.info("🔄 Merging all MindMaps into one unified file...")
                    from Merge import generating_full_mindmapp
                    generating_full_mindmapp(base_folder=domain_folder)
                    logging.info("✅ Unified MindMap generated.")

                    # 📝 Add button descriptions
                    logging.info("🧾 Adding button descriptions to final MindMap...")
                    
                    INPUT_MM = os.path.join(domain_folder, "Merged_Website_Structure_after_login.mm")
                    OUTPUT_MM = os.path.join(domain_folder, "Full_Website_Structure_updated_with_descriptions.mm")

                    if not os.path.exists(INPUT_MM):
                        logging.info(f"❌ {INPUT_MM} file not found.")
                    else:
                        process_mindmap(INPUT_MM, OUTPUT_MM)
                        logging.info("✅ Button descriptions added successfully.")

                        # --- Zip the entire folder after final file creation ---
                        try:
                            output_zip_file = f"{folder_name}.zip"
                            zip_folder(folder_name, output_zip_file)
                            logging.info(f"✅ Successfully zipped the folder to {output_zip_file}")
                        except Exception as e:
                            logging.info(f"❌ Error during zipping: {e}")
                            return jsonify({
                                'error': f"Failed to zip the folder: {e}",
                                'details': traceback.format_exc()
                            }), 500

                else:
                    logging.info("⚠️ No username/password provided — skipping login section.")
                    # --- Zip the folder if no login is provided ---
                    print(f" domain folder is {domain_folder}")
                    
                    INPUT_MM = os.path.join(domain_folder, "Full_Website_Structure_with_screenshots.mm")
                    OUTPUT_MM = os.path.join(domain_folder, "Full_Website_Structure_updated_with_descriptions.mm")
                    print(f"input file {INPUT_MM}")
                    if not os.path.exists(INPUT_MM):
                        logging.info(f"❌ {INPUT_MM} file not found.")
                    else:
                        process_mindmap(INPUT_MM, OUTPUT_MM)
                        logging.info("✅ Button descriptions added successfully.")
                    try:
                        output_zip_file = f"{folder_name}.zip"
                        zip_folder(folder_name, output_zip_file)
                        logging.info(f"✅ Successfully zipped the folder to {output_zip_file}")
                    except Exception as e:
                        logging.info(f"❌ Error during zipping: {e}")
                        return jsonify({
                            'error': f"Failed to zip the folder: {e}",
                            'details': traceback.format_exc()
                        }), 500

            else:
                logging.info(f"❌ Headers folder not found at path: {headers_folder}")

        except Exception as e:
            error_msg = f"An error occurred during MindMap generation: {str(e)}"
            logging.error(f"❌ {error_msg}")
            logging.error(traceback.format_exc())
            return jsonify({
                'error': error_msg,
                'details': traceback.format_exc()
            }), 500

    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logging.error(f"Error during extraction: {error_msg}")
        logging.error(traceback.format_exc())
        return jsonify({
            'error': error_msg,
            'details': traceback.format_exc()
        }), 500

    # ✅ Return cleaned result to API response
    return jsonify({
        'success': True,
        'count': len(cleaned_links),
        'links': cleaned_links,
        'zip_file': f"{folder_name}.zip"
    })

@app.route('/download/<filename>')
def download_file(filename):
    logging.info (os.getcwd())
    return send_from_directory(os.getcwd(), filename, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False,allow_unsafe_werkzeug=True)
   

    

