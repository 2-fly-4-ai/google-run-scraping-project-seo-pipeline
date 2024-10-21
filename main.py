import os
import re
import time
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from functools import wraps
import openai

load_dotenv()
app = Flask(__name__)
apiKey = os.getenv('SPM_APIKEY')
openai.api_key = os.getenv('OPENAI_API_KEY')
API_KEY = os.getenv('API_KEY')  # Make sure this is set in your .env file

# Proxy configuration
proxy_server = f"http://{apiKey}:@api.zyte.com:8011"  # Adjust if authentication is required differently

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

def clean_html_with_openai(html_content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Ensure the model name is correct
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that cleans HTML content and extracts the main content while removing other elements."
                },
                {
                    "role": "user",
                    "content": f"Clean the following HTML content, removing any unnecessary elements not related to the content and focusing on the main text content related to the subject. Make sure you output in HTML as well:\n\n{html_content}"
                }
            ],
            max_tokens=5000,
            n=1,
            stop=None,
            temperature=0.8,
        )
        
        cleaned_content = response.choices[0].message['content']
        return cleaned_content
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return html_content  # Return original content if OpenAI cleaning fails

def cf_manual_solver(page):
    """
    Attempts to solve Cloudflare CAPTCHA manually.
    Note: Automated solving of CAPTCHAs can violate terms of service and is generally discouraged.
    Consider using professional CAPTCHA-solving services if necessary.
    """
    try:
        # Detect if Cloudflare CAPTCHA is present
        captcha_iframe = page.query_selector("iframe[src*='captcha']")
        if captcha_iframe:
            print("CAPTCHA detected. Attempting to solve...")
            # Placeholder for CAPTCHA solving logic
            # This could involve manual intervention or integration with solving services
            # For example:
            # captcha_solver.solve(captcha_iframe)
            # Wait and verify if CAPTCHA is solved
            time.sleep(10)  # Wait time for CAPTCHA solving
            print("CAPTCHA solving attempted.")
        else:
            print("No Cloudflare CAPTCHA detected.")
    except Exception as err:
        print(f"Failed to solve CAPTCHA: {err}")

@app.route('/scrape_html', methods=['POST'])
@require_api_key 
def scrape_html():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": proxy_server} if apiKey else None,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/112.0.0.0 Safari/537.36'
                ]
            )
            context = browser.new_context(
                # Emulate a specific device or viewport if needed
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/112.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Navigate to the URL
            page.goto(url, timeout=60000)  # 60 seconds timeout
            page.wait_for_load_state('networkidle', timeout=60000)

            # Optional: Handle CAPTCHA if present
            # Uncomment the following line if you have a method to solve CAPTCHAs
            # cf_manual_solver(page)

            # Scroll down to load dynamic content
            page.evaluate("window.scrollTo(0, 600);")
            time.sleep(5)  # Wait for additional content to load

            html_content = page.content()

            # Close the browser context
            context.close()
            browser.close()

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'noscript', 'iframe', 'object', 'embed', 'applet', 'audio', 'video', 'svg', 'canvas']):
                script_or_style.decompose()

            # Remove all attributes from remaining tags
            for tag in soup.find_all(True):
                tag.attrs = {}

            # Extract the desired content tags
            content_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul'])

            # Combine the cleaned content
            cleaned_html = ''.join(str(tag) for tag in content_tags)

            # Clean the HTML content using OpenAI
            final_cleaned_content = clean_html_with_openai(cleaned_html)

            return jsonify({"html": final_cleaned_content}), 200
    except PlaywrightTimeoutError:
        error_message = "Timeout while loading the page."
        print(error_message)
        return jsonify({"error": error_message}), 504
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')