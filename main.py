from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

def get_text_or_none(page, selector):
    try:
        page.wait_for_selector(selector, timeout=5000)
        return page.locator(selector).inner_text().strip()
    except:
        return None

@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL parameter is missing"}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the page
        page.goto(url, wait_until="domcontentloaded")

        # Accept GDPR consent if button exists
        try:
            consent_button = page.locator('button:has-text("Accepter")')
            if consent_button.is_visible():
                consent_button.click()
                page.wait_for_timeout(1000)
        except:
            pass

        # Save redirected URL
        redirected_url = page.url

        # Click "voir plus" if present
        try:
            voir_plus = page.locator('button:has-text("voir plus")')
            if voir_plus.is_visible():
                voir_plus.click()
                page.wait_for_timeout(5000)
        except:
            pass

        data = {
            "url": redirected_url,
            "price": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-1rt48lp > span.css-otf0vo"),
            "total_rooms": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(1) > span"),
            "bedrooms": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(2) > span:nth-child(2)"),
            "internal_surface": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(3) > span:nth-child(2)"),
            "external_surface": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(4) > span:nth-child(2)"),
            "city_zipcode": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1tn1yel > button.css-8tb8om > div > span"),
            "full_description": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section.css-13o7eu2.Section.Description > div > div > div.css-85qpxe.DescriptionTexts"),
            "characteristics": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(4) > div"),
            "energy_performance": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > div.css-1fobf8d > div > div:nth-child(1) > div"),
            "construction_date": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(1) > div > span:nth-child(2)"),
            "heating_type": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(3) > div > span:nth-child(2)"),
            "heating_source": get_text_or_none(page, "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(4) > div > span:nth-child(2)")
        }

        browser.close()

        return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
