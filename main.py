import os, json, smtplib
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import chromedriver_binary
from webdriver_manager.utils import ChromeType
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders, message
from flask import Flask, render_template, request, send_file
import time

load_dotenv()

app = Flask(__name__)

YOUTUBE_TRENDING_URL = 'https://www.youtube.com/feed/trending'

def get_driver():
  chrome_options = Options()
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
  return driver

# ... (rest of your existing code) ...

@app.route('/download_mp3', methods=['POST'])
def download_mp3():
    youtube_url = request.form.get('youtube_url')

    if not youtube_url:
        return "YouTube URL is required", 400

    try:
        driver = get_driver()
        driver.get("https://ezmp3.cc")

        # Type the YouTube URL into the input field
        driver.find_element(By.CSS_SELECTOR, 'input[name="url"]').send_keys(youtube_url)

        # Click the submit button
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Wait for the page to load and the download button to appear
        time.sleep(10)  # Adjust as needed

        # Find and click the "Download MP3" button
        download_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Download MP3')]")
        download_button.click()

        # Wait for the download to start (adjust time as needed)
        time.sleep(5)

        # Assuming the downloaded file is in the default download directory
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads") 
        mp3_files = [f for f in os.listdir(download_dir) if f.endswith(".mp3")]

        if mp3_files:
            latest_mp3 = max(mp3_files, key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
            mp3_path = os.path.join(download_dir, latest_mp3)
            return send_file(mp3_path, as_attachment=True)
        else:
            return "MP3 file not found", 404

    except Exception as e:
        print(f"Error during download: {e}")
        return f"Error during download: {e}", 500

    finally:
        driver.quit()

# ... (rest of your existing code) ...

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0') 