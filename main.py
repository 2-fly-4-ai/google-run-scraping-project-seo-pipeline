import os
import re
import time
import base64
import json
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

load_dotenv()
app = Flask(__name__)
apiKey = os.getenv('SPM_APIKEY')

# Proxy configuration
proxy_options = {
    'proxy': {
        'http': f'http://{apiKey}:@api.zyte.com:8011',
        'https': f'http://{apiKey}:@api.zyte.com:8011',
        'no_proxy': 'localhost,127.0.0.1'
    }
}

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        options=chrome_options,
        seleniumwire_options=proxy_options,
    )

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver

def cf_manual_solver(driver) -> None:
    captcha_frame_regex = re.compile(r'cf-chl-widget-.{3,6}')
    try:
        matching_elements = driver.find_elements(By.XPATH, "//*[contains(@id, 'cf-chl-widget-')]")
        cf_captcha_frame = None
        for element in matching_elements:
            element_id = element.get_attribute("id")
            accessible_name = element.get_attribute("aria-label") or ""
            if captcha_frame_regex.match(element_id) and 'Cloudflare security challenge' in accessible_name:
                cf_captcha_frame = element
                break
        if cf_captcha_frame:
            WebDriverWait(driver, 15.0).until(EC.frame_to_be_available_and_switch_to_it(cf_captcha_frame))
            captcha_checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'ctp-checkbox-label'))
            )
            captcha_checkbox.click()
            driver.switch_to.default_content()
            print("CAPTCHA solved successfully.")
        else:
            print("No Cloudflare CAPTCHA detected.")
    except Exception as err:
        print(f'Failed to solve CAPTCHA: {err}')

@app.route('/scrape_html', methods=['POST'])
def scrape_html():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(url)
        # cf_manual_solver(driver)
        html_content = driver.page_source

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract all header tags (h1, h2, h3, etc.) and paragraph tags (p)
        content_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])

        # Remove any style tags and scripts
        for script_or_style in soup(['style', 'script']):
            script_or_style.decompose()

        # Extract the cleaned content
        cleaned_html = ''.join(str(tag) for tag in content_tags)




        return jsonify({"html": cleaned_html}), 200
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')

# curl -X POST -F 'url=https://example.com' https://scraper-url-html-30316204799.us-central1.run.app/scrape_html