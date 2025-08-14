from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import requests
import logging

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

app = Flask(__name__)

def resolve_real_url(short_url):
    logging.info(f"Resolving URL: {short_url}")
    try:
        response = requests.get(short_url, allow_redirects=True, timeout=10)
        logging.info(f"Resolved redirect: {short_url} → {response.url}")
        return response.url
    except Exception as e:
        logging.error(f"Failed to resolve URL: {short_url} — {e}")
        return short_url  # fallback

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
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            context = browser.new_context(viewport={"width": 1024, "height": 600})
            page = context.new_page()

            # Block images, fonts, media to save RAM
            page.route("**/*", lambda route: route.abort() 
                       if route.request.resource_type in ["image", "media", "font"] 
                       else route.continue_())

            logging.info(f"Navigating to {real_url} ...")
            page.goto(real_url, timeout=60000)

            # GDPR consent
            try:
                consent_button = page.locator("button:has-text('Tout accepter')")
                if consent_button and consent_button.is_visible():
                    logging.info("GDPR popup detected — clicking 'Tout accepter'")
                    consent_button.click()
                    page.wait_for_timeout(500)
            except Exception as e:
                logging.warning(f"GDPR popup handling failed: {e}")

            page.wait_for_timeout(1000)

            # Price
            try:
                price = page.locator(".Price__Label").first.text_content()
                if price:
                    data["Price"] = price.strip()
                    logging.info(f"Price found: {data['Price']}")
                else:
                    logging.info("Price not found")
            except Exception as e:
                logging.warning(f"Price extraction failed: {e}")

            # "Voir plus" button
            try:
                button = page.locator("button", has_text="Voir plus")
                if button:
                    logging.info("Clicking 'Voir plus' button")
                    button.click()
                    page.wait_for_timeout(500)
            except Exception as e:
                logging.warning(f"'Voir plus' click failed: {e}")

            # Description
            try:
                desc = page.locator(".Text__StyledText-sc-10o2fdq-0").first.text_content()
                if desc:
                    data["Description"] = desc.strip()
                    logging.info("Description extracted")
            except:
                logging.info("Description not found")

            # Characteristics
            try:
                items = page.locator(".TitleValueRow__Container")
                count = items.count()
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
                logging.info("Characteristics extracted")
            except Exception as e:
                logging.warning(f"Characteristics extraction failed: {e}")

            browser.close()
            logging.info("Browser closed")

    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        data["error"] = str(e)

    return data

@app.route('/extract', methods=['POST'])
def extract():
    body = request.json
    if not body or 'url' not in body:
        return jsonify({'error': 'Missing "url" field'}), 400

    url = body['url']
    result = extract_data(url)
    return jsonify(result)

@app.route('/')
def health():
    return "Seloger scraper is running", 200

if __name__ == '__main__':
    # Use port from Render env variable if available
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
