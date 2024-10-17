import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from flask import Flask, request, jsonify
from zyte_smartproxy_selenium import webdriver
import time
import json
import base64
from io import BytesIO

load_dotenv()

app = Flask(__name__)

# Fetch Zyte API Key from .env file
SPM_APIKEY = os.getenv('SPM_APIKEY')

def get_driver():
    # chrome_options = Options()
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("window-size=1024,768")  # Ensure consistent screenshot size
    # chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Use Zyte SmartProxy Selenium to initialize Chrome with proxy
    driver = webdriver.Chrome(
        # chrome_options=chrome_options,
        spm_options={'spm_apikey': SPM_APIKEY}
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

        # Interact with the webpage to input YouTube URL and trigger download
        driver.find_element(By.CSS_SELECTOR, 'input[name="url"]').send_keys(youtube_url)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Wait for the download process to complete
        time.sleep(10)  # Adjust based on actual timing

        download_link = None
        try:
            # Analyze network requests to find MP3 download URL
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
            print("Download link not found. Taking screenshot.")  # Log the error
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "message": "Download link not found"}), 200  # Return 200 with screenshot

    except Exception as e:
        print(f"Error during processing: {e}")  # Log the error
        if driver:
            screenshot = driver.get_screenshot_as_png()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            return jsonify({"screenshot": screenshot_base64, "error": str(e)}), 500  # Return 500 with screenshot and error
        else:
            return jsonify({"error": str(e)}), 500  # Driver initialization failed

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
