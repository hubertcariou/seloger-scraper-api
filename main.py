from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "Missing 'url' in request body"}), 400

        input_url = data["url"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Go to the page
            page.goto(input_url, wait_until="domcontentloaded", timeout=60000)

            # Handle GDPR consent if present
            try:
                gdpr_button = page.locator("button:has-text('Accepter')")
                if gdpr_button.is_visible():
                    gdpr_button.click()
                    page.wait_for_timeout(2000)
            except:
                pass

            # Wait for main content
            page.wait_for_selector("main", timeout=10000)

            # Get final redirected URL
            final_url = page.url

            # Expand "voir plus" if present
            try:
                more_button = page.locator("button:has-text('voir plus')")
                if more_button.is_visible():
                    more_button.click()
                    page.wait_for_timeout(1500)
            except:
                pass

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Helper to extract text safely
            def select_text(selector):
                el = soup.select_one(selector)
                return el.get_text(strip=True) if el else None

            # Extract fields using your selectors
            extracted_data = {
                "url": final_url,
                "price": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-1rt48lp > span.css-otf0vo"),
                "total_rooms": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(1) > span"),
                "bedrooms": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(2) > span:nth-child(2)"),
                "internal_surface": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(3) > span:nth-child(2)"),
                "external_surface": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(4) > span:nth-child(2)"),
                "city_zip": select_text("#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1tn1yel > button.css-8tb8om > div > span"),
                "full_description": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section.css-13o7eu2.Section.Description > div > div > div.css-85qpxe.DescriptionTexts"),
                "characteristics": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(4) > div"),
                "energy_performance": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > div.css-1fobf8d > div > div:nth-child(1) > div"),
                "construction_date": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(1) > div > span:nth-child(2)"),
                "heating_type": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(3) > div > span:nth-child(2)"),
                "heating_source": select_text("#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(4) > div > span:nth-child(2)")
            }

            browser.close()

        return jsonify(extracted_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
