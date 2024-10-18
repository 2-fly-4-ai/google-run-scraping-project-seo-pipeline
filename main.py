import os
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify
import time
import json
import base64

load_dotenv()
app = Flask(__name__)

# Proxy configuration
proxy_options = {
    'proxy': {
        'http': 'http://4ff8c485e6bd4438b268866d4ce0dbe0:@api.zyte.com:8011',
        'https': 'http://4ff8c485e6bd4438b268866d4ce0dbe0:@api.zyte.com:8011',
        'no_proxy': 'localhost,127.0.0.1'
    }
}

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options,
        seleniumwire_options=proxy_options
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

        # Interact with the website
        driver.find_element(By.CSS_SELECTOR, 'input[name="url"]').send_keys(youtube_url)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(10)  # Adjust as needed

        download_link = None
        for request in driver.requests:
            if request.response and 'MP3' in request.url:
                download_link = request.url
                break

        if download_link:
            return jsonify({"download_url": download_link}), 200
        else:
            print("Download link not found. Taking screenshot.")
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "message": "Download link not found"}), 200

    except Exception as e:
        print(f"Error during processing: {e}")
        if driver:
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "error": str(e)}), 500
        else:
            return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')