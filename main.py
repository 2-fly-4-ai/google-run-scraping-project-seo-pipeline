import os
from dotenv import load_dotenv
import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
from selenium_stealth import stealth
import time
import base64
import json
import threading
# from selenium_stealth import stealth

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

# 'headers': {
#                 'X-Crawlera-No-Bancheck': '1',
#                 'X-Crawlera-Profile': 'desktop',
#                 'X-Crawlera-Cookies': 'disable',
#             }

def wait_for_download_link(driver, timeout=60):
    end_time = time.time() + timeout
    while time.time() < end_time:
        for req in driver.requests:
            if req.response and 'download?' in req.url.lower() and req.response.status_code == 200:
                return req.url
        time.sleep(1)
    return None

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(
        options=chrome_options,
        seleniumwire_options=proxy_options
    )
    
    # Apply stealth settings
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
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
        # Access the MP3 conversion site
        driver.get("https://ezmp3.cc")
        # Capture a screenshot at the start of the session
        start_screenshot = driver.get_screenshot_as_png()
        start_screenshot_base64 = base64.b64encode(start_screenshot).decode('utf-8')
        # Wait for the input element to be present
        input_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="url"]'))
        )
        input_element.send_keys(youtube_url)
        # Wait for the submit button to be present and clickable
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        submit_button.click()

        # Wait for the download link to be present
        download_button_present = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Download MP3']"))
        )
        if download_button_present:
            download_button_present.click()
            print("Clicked Download MP3 button")

        download_link = wait_for_download_link(driver)
        if download_link:
            driver.get(download_link)
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "download_url": download_link, "start_screenshot": start_screenshot_base64}), 200
        else:
            print("Download link not found. Taking screenshot.")
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "message": "Download link not found", "start_screenshot": start_screenshot_base64}), 200
    except Exception as e:
        print(f"Error during processing: {e}")
        if driver:
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "error": str(e), "start_screenshot": start_screenshot_base64}), 500
        else:
            return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
