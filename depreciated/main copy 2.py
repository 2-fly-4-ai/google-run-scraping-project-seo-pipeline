import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify
from zyte_smartproxy_selenium import webdriver as zyte_webdriver
import time
import json
import base64
from io import BytesIO

load_dotenv()

app = Flask(__name__)

SPM_APIKEY = os.getenv('SPM_APIKEY')

selenium_wire_storage = os.path.join(os.getcwd(), "selenium_wire")

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
   
    # Initialize the Chrome driver with Zyte SmartProxy options
    driver = zyte_webdriver.Chrome(
        options=chrome_options,
        spm_options={
            'request_storage_base_dir': selenium_wire_storage,
            'spm_apikey': SPM_APIKEY,
            'headers': {
                'X-Crawlera-No-Bancheck': '1',
                'X-Crawlera-Profile': 'desktop',
                'X-Crawlera-Cookies': 'disable',
            }
        }
    )

    return driver

@app.route('/download_mp3', methods=['POST'])
def download_mp3():
    youtube_url = request.form.get('youtube_url')

    if not youtube_url:
        return jsonify({"error": "YouTube URL is required"}), 400

    driver = None
    try:
        driver = get_driver()
        
        driver.get("https://ezmp3.cc")

        driver.find_element(By.CSS_SELECTOR, 'input[name="url"]').send_keys(youtube_url)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        time.sleep(10)  # Adjust as needed

        download_link = None
        try:
            for request_log in driver.get_log('performance'):
                log_entry = json.loads(request_log['message'])
                if (
                    'request' in log_entry['message'] and
                    'url' in log_entry['message']['request'] and
                    'document' in log_entry['message']['request']['url'] and
                    'MP3' in log_entry['message']['request']['url']
                ):
                    download_link = log_entry['message']['request']['url']
                    break
        except Exception as e:
            print(f"Error analyzing network requests: {e}")

        if download_link:
            return jsonify({"download_url": download_link}), 200
        else:
            print("Download link not found. Taking screenshot.")
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "message": "Download link not found"}), 200

    except FileNotFoundError as fnf_error:
        print(f"FileNotFoundError occurred: {fnf_error}")
        return jsonify({"error": "File not found error occurred. This might be due to a temporary issue with Selenium Wire."}), 500

    except Exception as e:
        print(f"Error during processing: {e}")
        if driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
                return jsonify({"screenshot": screenshot_base64, "error": str(e)}), 500
            except Exception as screenshot_error:
                print(f"Error taking screenshot: {screenshot_error}")
                return jsonify({"error": str(e), "screenshot_error": str(screenshot_error)}), 500
        else:
            return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as quit_error:
                print(f"Error during driver.quit(): {quit_error}")

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')