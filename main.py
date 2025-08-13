from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import requests

app = Flask(__name__)

def resolve_real_url(short_url):
    try:
        response = requests.get(short_url, allow_redirects=True, timeout=10)
        print(f"[INFO] Resolved redirect: {short_url} → {response.url}")
        return response.url
    except Exception as e:
        print(f"[ERROR] Failed to resolve URL: {short_url} — {e}")
        return short_url  # fallback if redirect fails

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
        real_url = resolve_real_url(url)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(real_url, timeout=60000)
        page.wait_for_timeout(3000)

        try:
            data["Price"] = page.locator(".Price__Label").first.text_content().strip()
        except:
            pass

        try:
            button = page.locator("button", has_text="Voir plus")
            if button:
                button.click()
                page.wait_for_timeout(1000)
        except:
            pass

        try:
            desc = page.locator(".Text__StyledText-sc-10o2fdq-0").first.text_content()
            data["Description"] = desc.strip()
        except:
            pass

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
        except:
            pass

        browser.close()
        
        except Exception as e:
            print(f"[ERROR] Failed to scrape URL: {url}")
            print(f"[EXCEPTION] {e}")
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

