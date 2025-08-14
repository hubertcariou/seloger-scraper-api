from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import signal

app = Flask(__name__)

# Optional: Flask-level timeout safeguard (in seconds)
REQUEST_TIMEOUT = 40

def timeout_handler(signum, frame):
    raise TimeoutError("Request took too long and was aborted.")
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
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            page = browser.new_page()

            # Block heavy resources for speed & memory
            page.route("**/*", lambda route: route.abort()
                       if route.request.resource_type in ["image", "stylesheet", "font"]
                       else route.continue_())

            # Go directly to the URL (Playwright will handle redirects)
            page.goto(url, timeout=30000)  # 30s max

            # Handle GDPR popup if present
            try:
                consent_button = page.locator("button:has-text('Tout accepter')")
                if consent_button.is_visible(timeout=2000):
                    print("GDPR popup detected — clicking 'Tout accepter'")
                    consent_button.click()
                    page.wait_for_timeout(500)
            except:
                pass

            # Price
            try:
                page.wait_for_selector(".Price__Label", timeout=5000)
                data["Price"] = page.locator(".Price__Label").first.text_content().strip()
            except:
                pass

            # Expand "Voir plus" if available
            try:
                voir_plus_button = page.locator("button:has-text('Voir plus')")
                if voir_plus_button.is_visible(timeout=2000):
                    voir_plus_button.click()
                    page.wait_for_timeout(500)
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

    except TimeoutError as te:
        print(f"[TIMEOUT] {te}")
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

    url = body['url']

    # Start Flask request timeout
    signal.alarm(REQUEST_TIMEOUT)

    try:
        result = extract_data(url)
    finally:
        signal.alarm(0)  # Disable timeout after request

    return jsonify(result)


@app.route('/')
def health():
    return "Seloger scraper is running", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
