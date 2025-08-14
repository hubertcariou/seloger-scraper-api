from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import requests
import logging
import os

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
        return short_url

def safe_text(locator):
    try:
        if locator and locator.is_visible():
            return locator.text_content().strip()
    except:
        pass
    return None

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
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox", "--single-process", "--disable-gpu"]
            )
            context = browser.new_context(
                viewport={"width": 1024, "height": 600},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Block unnecessary resources
            page.route("**/*", lambda route: route.abort()
                       if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                       else route.continue_())

            logging.info(f"Navigating to {real_url} ...")
            page.goto(real_url, timeout=60000)

            # GDPR consent
            try:
                consent = page.locator("button:has-text('Tout accepter')")
                if consent and consent.is_visible():
                    logging.info("Clicking GDPR consent button")
                    consent.click()
                    page.wait_for_timeout(500)
            except:
                pass

            # Price
            for sel in [".Price__Label", "span[data-testid='price']"]:
                price = safe_text(page.locator(sel))
                if price:
                    data["Price"] = price
                    logging.info(f"Price: {price}")
                    break

            # Total Rooms
            for sel in ["span:has-text('Pièces')", "span[data-testid='rooms']"]:
                rooms = safe_text(page.locator(sel))
                if rooms:
                    data["Total Rooms"] = rooms
                    break

            # Bedrooms
            for sel in ["span:has-text('Chambres')", "span[data-testid='bedrooms']"]:
                bedrooms = safe_text(page.locator(sel))
                if bedrooms:
                    data["Bedrooms"] = bedrooms
                    break

            # Internal Surface
            for sel in ["span:has-text('Surface')", "span[data-testid='surface']"]:
                surface = safe_text(page.locator(sel))
                if surface:
                    data["Internal Surface"] = surface
                    break

            # Field Surface
            for sel in ["span:has-text('Terrain')", "span[data-testid='field']"]:
                field = safe_text(page.locator(sel))
                if field:
                    data["Field Surface"] = field
                    break

            # Description
            try:
                voir_plus = page.locator("button:has-text('Voir plus')")
                if voir_plus and voir_plus.is_visible():
                    logging.info("Clicking 'Voir plus' to expand description")
                    voir_plus.click()
                    page.wait_for_timeout(500)

                desc = safe_text(page.locator(".Text__StyledText-sc-10o2fdq-0"))
                if desc:
                    data["Description"] = desc
            except:
                logging.info("Description not found")

            # Characteristics
            try:
                items = page.locator(".TitleValueRow__Container")
                for i in range(items.count()):
                    title = safe_text(items.nth(i).locator(".TitleValueRow__Title"))
                    value = safe_text(items.nth(i).locator(".TitleValueRow__Value"))
                    if title and value:
                        data["Characteristics"].append(f"{title}: {value}")
            except:
                logging.info("Characteristics not found")

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
    return jsonify(extract_data(body['url']))

@app.route('/')
def health():
    return "Seloger scraper is running", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
