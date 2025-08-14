from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests
import logging

# -------------------- Logging setup --------------------
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# -------------------- Flask app --------------------
app = Flask(__name__)

# -------------------- Helper functions --------------------
def resolve_real_url(short_url):
    logging.info(f"Resolving URL: {short_url}")
    try:
        response = requests.get(short_url, allow_redirects=True, timeout=10)
        logging.info(f"Resolved redirect: {short_url} → {response.url}")
        return response.url
    except Exception as e:
        logging.error(f"Failed to resolve URL: {short_url} — {e}")
        return short_url  # fallback if redirect fails

def extract_data(url):
    logging.info(f"Starting scrape for: {url}")
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
        real_url = resolve_real_url(url)

        with sync_playwright() as p:
            logging.info("Launching Chromium browser...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",  # prevent shared memory issues
                    "--no-sandbox",             # required on Render free plan
                    "--single-process",         # reduce RAM usage
                    "--disable-gpu"
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                java_script_enabled=True
            )

            page = context.new_page()
            logging.info(f"Navigating to {real_url}...")
            try:
                page.goto(real_url, timeout=60000)
            except PlaywrightTimeout:
                logging.warning("Page load timed out, continuing...")

            # Click GDPR consent if visible
            try:
                consent_button = page.locator("button:has-text('Tout accepter')")
                if consent_button.is_visible():
                    logging.info("GDPR popup detected — clicking 'Tout accepter'")
                    consent_button.click()
                    page.wait_for_timeout(1000)
            except Exception as e:
                logging.info(f"No GDPR popup detected or failed to click: {e}")

            page.wait_for_timeout(2000)

            # Extract price
            try:
                data["Price"] = page.locator(".Price__Label").first.text_content().strip()
                logging.info(f"Price found: {data['Price']}")
            except:
                logging.info("Price not found")

            # Click 'Voir plus' if exists
            try:
                button = page.locator("button", has_text="Voir plus")
                if button:
                    logging.info("Clicking 'Voir plus' button")
                    button.click()
                    page.wait_for_timeout(1000)
            except:
                logging.info("'Voir plus' button not found")

            # Extract description
            try:
                desc = page.locator(".Text__StyledText-sc-10o2fdq-0").first.text_content()
                data["Description"] = desc.strip()
                logging.info("Description extracted")
            except:
                logging.info("Description not found")

            # Extract characteristics
            try:
                items = page.locator(".TitleValueRow__Container")
                count = items.count()
                logging.info(f"Found {count} characteristic rows")
                for i in range(count):
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
            except Exception as e:
                logging.info(f"Failed to extract characteristics: {e}")

            browser.close()
            logging.info("Browser closed, scraping complete.")

    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        data["error"] = str(e)

    return data

# -------------------- Flask routes --------------------
@app.route('/extract', methods=['POST'])
def extract():
    body = request.json
    if not body or 'url' not in body:
        logging.warning('Missing "url" field in request')
        return jsonify({'error': 'Missing "url" field'}), 400

    url = body['url']
    result = extract_data(url)
    return jsonify(result)

@app.route('/')
def health():
    return "Seloger scraper is running", 200

# -------------------- Main --------------------
if __name__ == '__main__':
    logging.info("Starting Seloger scraper API...")
    app.run(host='0.0.0.0', port=5000)
