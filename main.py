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
from bs4 import BeautifulSoup
from functools import wraps
import time
import openai

load_dotenv()
app = Flask(__name__)
apiKey = os.getenv('SPM_APIKEY')
openai.api_key = os.getenv('OPENAI_API_KEY')
API_KEY = os.getenv('API_KEY')  # Add this line to load the API key

# Proxy configuration
proxy_options = {
    'proxy': {
        'http': f'http://{apiKey}:@api.zyte.com:8011',
        'https': f'http://{apiKey}:@api.zyte.com:8011',
        'no_proxy': 'localhost,127.0.0.1'
    }
}

# API key authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if provided_api_key and provided_api_key == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Invalid or missing API key"}), 401
    return decorated_function

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

def clean_html_with_openai(html_content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that cleans and summarizes HTML content."},
                {"role": "user", "content": f"Please clean the following HTML content, removing any unnecessary elements and focusing on the main text content related to the subject, make sure you output in html aswell:\n\n{html_content}"}
            ],
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5,
        )
        
        cleaned_content = response.choices[0].message['content'].strip()
        return cleaned_content
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return html_content  # Return original content if OpenAI cleaning fails

@app.route('/scrape_html', methods=['POST'])
@require_api_key 
def scrape_html():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(url)
        # cf_manual_solver(driver)

        time.sleep(3)

        html_content = driver.page_source
       
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(['script', 'style', 'noscript', 'iframe', 'object', 'embed', 'applet', 'audio', 'video', 'svg', 'canvas']):
            script_or_style.decompose()

        # Remove all attributes from remaining tags
        for tag in soup.find_all(True):
            tag.attrs = {}

        # Extract all header tags (h1, h2, h3, etc.) and paragraph tags (p)
        content_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])

        # Extract the cleaned content
        cleaned_html = ''.join(str(tag) for tag in content_tags)

        # Clean the HTML content using OpenAI
        final_cleaned_content = clean_html_with_openai(cleaned_html)

        return jsonify({"html": final_cleaned_content}), 200
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')