from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import signal

app = Flask(__name__)

# Timeout safeguard (per request)
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Request took too long")

signal.signal(signal.SIGALRM, timeout_handler)

def extract_data(url):
    data = {
        "URL": url,
        "Price": None,
        "Total Rooms": None,
        "Bedrooms": None,
        "Internal Surface": None,
        "Field Surface": None,
        "Description": None,
        "Characteristics": []
    }

    try:
        with sync_playwright() as p:
            # Firefox for lower RAM usage
            browser = p.firefox.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )

            page = browser.new_page(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                           "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
                           "Mobile/15E148 Safari/604.1"
            )
            page.set_viewport_size({"width": 375, "height": 812})  # Mobile viewport

            # Block heavy or non-essential resources
            def block_unneeded(route):
                if route.request.resource_type in [
                    "image", "stylesheet", "font", "media", "other", "script"
                ]:
                    # Allow only JS from Seloger's main domain
                    if "seloger.com" not in route.request.url:
                        return route.abort()
                return route.continue_()

            page.route("**/*", block_unneeded)

            # Go to URL (Firefox handles redirects)
            page.goto(url, timeout=20000)  # 20s max

            # Handle GDPR popup if present
            try:
                consent_button = page.locator("button:has-text('Tout accepter')")
                if consent_button.is_visible(timeout=1500):
                    consent_button.click()
                    page.wait_for_timeout(300)
            except:
                pass

            # Price
            try:
                page.wait_for_selector(".Price__Label", timeout=4000)
                data["Price"] = page.locator(".Price__Label").first.text_content().strip()
            except:
                pass

            # "Voir plus"
            try:
                voir_plus_btn = page.locator("button:has-text('Voir plus')")
                if voir_plus_btn.is_visible(timeout=1500):
                    voir_plus_btn.click()
                    page.wait_for_timeout(300)
            except:
                pass

            # Description
            try:
                desc = page.locator(".Text__StyledText-sc-10o2fdq-0").first.text_content()
                if desc:
                    data["Description"] = desc.strip()
            except:
                pass

            # Characteristics
            try:
                items = page.locator(".TitleValueRow__Container")
                for i in range(items.count()):
                    title = items.nth(i).locator(".TitleValueRow__Title").text_content().strip()
                    value = items.nth(i).locator(".TitleValueRow__Value").text_content().strip()
                    data["Characteristics"].append(f"{title}: {value}")

                    if "pièce" in title.lower():
                        data["Total Rooms"] = value
                    elif "chambre" in title.lower():
                        data["Bedrooms"] = value
                    elif "surface" in title.lower() and "habitable" in title.lower():
                        data["Internal Surface"] = value
                    elif "terrain" in title.lower():
                        data["Field Surface"] = value
            except:
                pass

            browser.close()

    except TimeoutException:
        data["error"] = "Scraping timed out"
    except Exception as e:
        print(f"[ERROR] Failed to scrape {url}: {e}")
        data["error"] = str(e)

    return data

@app.route('/extract', methods=['POST'])
def extract():
    body = request.json
    if not body or 'url' not in body:
        return jsonify({'error': 'Missing \"url\" field'}), 400

    signal.alarm(40)  # 40s max for request
    try:
        url = body['url']
        result = extract_data(url)
        return jsonify(result)
    except TimeoutException:
        return jsonify({'error': 'Processing took too long'}), 504
    finally:
        signal.alarm(0)

@app.route('/')
def health():
    return "Seloger scraper is running", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
