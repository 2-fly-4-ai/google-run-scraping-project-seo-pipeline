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
from selenium.webdriver.support.ui import WebDriverWait
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
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that cleans HTML content and extract the main content while removing other elements."},

                {"role": "user", "content": "Clean the following HTML content, removing any unnecessary elements nto related to the content and focusing on the main text content related to the subject, make sure you output in html aswell:\n\n<h3>Get the Reddit app</h3><p><a>🌎🌍🌏</a></p><p>A place for major news from around the world, excluding US-internal news.</p><h1>North Korea Threatens To Declare War With South Korea</h1><p>Users often report submissions from this site for sensationalized articles. Readers have a responsibility to be skeptical, check sources, and comment on any flaws.</p><p>You can help improve this thread by linking to media that verifies or questions this article's claims. Your link could help readers better understand this issue.</p><p><em>I am a bot, and this action was performed automatically. Please </em><a>contact the moderators of this subreddit</a><em> if you have any questions or concerns.</em></p><p>The Korean war officially never ended, so...</p><p>It’ll be a double-war?</p><p>At this point, it feels like North Korea threatens war as often as some of us threaten to quit our jobs... big words, but the action? Yet to be seen.</p><p>I feel called out</p><p>Then maybe it is not the best time to give away soldiers to Russia</p><p>I feel like they threaten whenever they are vulnerable. It’s like saying you’ll beat someone up while you’re taking a poop.</p><p>Days with even numbers: threaten war with SK</p><p>Days with odd numbers: threaten war with US</p><p>woah woah woah how did you get this classified information</p><p>Were they not at war already?</p><p><a>🌎🌍🌏</a></p><p>Anyone can view, post, and comment to this community</p><h1>More posts you may like</h1><p>A place for major news from around the world, excluding US-internal news.</p><h3>IDF does not intend to conquer South Lebanon, U.S. approves</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>IDF tanks cross into Syria - The Jerusalem post</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Iran: We have a counter-response ready if Israel attacks</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Netanyahu tells U.S. that Israel will strike Iranian military, not nuclear or oil, targets, officials say</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>IDF Arabic spokesperson warns Lebanese of imminent action against Hezbollah</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Israeli defense minister Gallant says next phase of the war will begin soon</h3><p>Come here to talk about fictional characters, fictional events, concepts, objects, etc. Join our Discord! https://discord.gg/E92zdkH</p><h3>There should be more instances of stories with Male MCs and female main rivals/arch enemies</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Israel warns of 'serious consequences' after Iran fires 200 missiles</h3><p>Why watch many shows when one show do trick?</p><h3>What do you think were some of the biggest fireable offenses of the series?</h3><p>Sovereign Citizen was created to provide a resource for like-minded individuals to learn about (and laugh at) people who have declared themselves 'sovereign citizens', especially those who run afoul of the law.</p><h3>Found my first one!</h3><p>This subreddit is a place to share news, information, resources, and support that relate to the novel coronavirus SARS-CoV-2 and the disease it causes called COVID-19. The primary focus of this sub is to actively monitor the situation in Australia and New Zealand, but all posts on international news and other virus-related topics are welcome, to the extent they are beneficial in keeping those down under informed.</p><h3>Kappa Delta - Working together to keep Melbourne locked down.</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>US threatens Israel: Resolve humanitarian crisis in Gaza or face arms embargo - report</h3><p>/r/EarthBound is a subreddit dedicated to Shigesato Itoi's cult classic JRPG series, EarthBound / MOTHER!</p><h3>the disrespect is crazy</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Former Iranian President Says 'the highest person in charge of the counter-Israel unit at the Iranian Intelligence Ministry was an Israeli Mossad agent'</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Lebanese army withdraws from positions on southern border with Israel, sources say</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Israel begins ground offensive in Lebanon</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Israeli Troops Killed in Hezbollah Ambush in Lebanon</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Israeli tanks push deeper into Jabalia in northern Gaza, residents say</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>US and EU call for 21-day ceasefire across Lebanon-Israel border</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>'Declaration of War': Israeli Leaders React to Massive Iranian Assault</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Hezbollah calls for unconditional cease-fire regardless of fighting in Gaza</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Iran says it will not send forces to confront Israel</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>US urges Israel to stop shooting at UN peacekeepers in Lebanon</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>Iran says it will respond 'decisively' if Israel attacks, asks UN to intervene</h3><p>A place for major news from around the world, excluding US-internal news.</p><h3>CIA seeks informants in China, North Korea and Iran, recruiting online</h3><h1>Log In</h1><p>By continuing, you agree to our <a>User Agreement</a> and acknowledge that you understand the <a>Privacy Policy</a>.</p><h1>Enter the 6-digit code from your authenticator app</h1><p>You’ve set up two-factor authentication for this account.</p><h1>Enter a 6-digit backup code</h1><p>You’ve set up two-factor authentication for this account.</p><h1>Sign Up</h1><p>By continuing, you agree to our <a>User Agreement</a> and acknowledge that you understand the <a>Privacy Policy</a>.</p><h1>Create your username and password</h1><p>Reddit is anonymous, so your username is what you’ll go by here. Choose wisely—because once you get a name, you can’t change it.</p><h1>Reset your password</h1><p>Enter your email address or username and we’ll send you a link to reset your password</p><p><faceplate-tracker><a>Need help?</a></faceplate-tracker></p><h1>Check your inbox</h1><p>An email with a link to reset your password was sent to the email address associated with your account</p><h1>Choose a Reddit account to continue</h1><h1>Reset your password</h1>"},
                 {"role": "assistant", "content": "<h3>Get the Reddit app</h3><p><a>🌎🌍🌏</a></p><p>A place for major news from around the world, excluding US-internal news.</p><h1>North Korea Threatens To Declare War With South Korea</h1><p>Users often report submissions from this site for sensationalized articles. Readers have a responsibility to be skeptical, check sources, and comment on any flaws.</p><p>You can help improve this thread by linking to media that verifies or questions this article's claims. Your link could help readers better understand this issue.</p><p><em>I am a bot, and this action was performed automatically. Please </em><a>contact the moderators of this subreddit</a><em> if you have any questions or concerns.</em></p><p>The Korean war officially never ended, so...</p><p>It’ll be a double-war?</p><p>At this point, it feels like North Korea threatens war as often as some of us threaten to quit our jobs... big words, but the action? Yet to be seen.</p><p>I feel called out</p><p>Then maybe it is not the best time to give away soldiers to Russia</p><p>I feel like they threaten whenever they are vulnerable. It’s like saying you’ll beat someone up while you’re taking a poop.</p><p>Days with even numbers: threaten war with SK</p><p>Days with odd numbers: threaten war with US</p><p>woah woah woah how did you get this classified information</p><p>Were they not at war already?</p>"},
                
                {"role": "user", "content": f"Clean the following HTML content, removing any unnecessary elements nto related to the content and focusing on the main text content related to the subject, make sure you output in html aswell:\n\n{html_content}"}
            ],
            max_tokens=5000,
            n=1,
            stop=None,
            temperature=0.8,
        )
        
        cleaned_content = response.choices[0].message.content
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

        wait = WebDriverWait(driver, timeout=2)

        # wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        #   # LETS IMPLEMENT THIS LOGIC. If the website is a redit url. Then we shoud add this 

        if "reddit.com" in url:
              wait.until(EC.presence_of_element_located((By.ID, "comment-tree")))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
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
        cleaned_html = ''.join(str(tag) for tag in content_tags).replace("\n", "")
        cleaned_html = re.sub(r"\s+", " ", cleaned_html)  # Replace multiple spaces with a single space

        # Clean the HTML content using OpenAI
        # final_cleaned_content = clean_html_with_openai(cleaned_html)

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