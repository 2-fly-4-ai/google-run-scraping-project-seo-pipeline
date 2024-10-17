import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from flask import Flask, request
import time
import json

load_dotenv()

app = Flask(__name__)


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    return driver


@app.route('/download_mp3', methods=['POST'])
def download_mp3():
    youtube_url = request.form.get('youtube_url')

    if not youtube_url:
        return "YouTube URL is required", 400

    driver = None  # Initialize driver *before* the try block
    try:
        driver = get_driver()
        driver.get("https://ezmp3.cc")

        driver.find_element(By.CSS_SELECTOR, 'input[name="url"]').send_keys(youtube_url)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        time.sleep(10)  # Adjust as needed

        try:
            download_link = None
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

            if download_link:
                return {"download_url": download_link}, 200
            else:
                return "MP3 download link not found in network requests.", 500

        except Exception as e:
            print(f"Error finding download link: {e}")
            return "Error finding download link. Site structure may have changed or network requests could not be accessed.", 500

    except Exception as e:
        print(f"Error during processing: {e}")
        return f"Error during processing: {e}", 500

    finally:
        if driver:  # Check if driver was initialized
            driver.quit()


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')