from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

async def get_text_safe(page, selector: str, timeout: int = 2000):
    try:
        locator = page.locator(selector)
        if await locator.count() > 0:
            return (await locator.inner_text(timeout=timeout)).strip()
    except Exception as e:
        print(f"Error extracting with selector {selector}: {e}")
    return None

@app.post("/extract")
async def extract_data(req: ExtractRequest):
    url = req.url
    try:
        async with async_playwright() as p:
            # Step 2: Run in non-headless mode for debugging
            browser = await p.chromium.launch(headless=False, args=["--disable-dev-shm-usage"])
            page = await browser.new_page()

            # Step 1: Log navigation and HTTP status
            print("Initial URL:", url)
            response = await page.goto(url, timeout=60000)
            print("Final URL after navigation:", page.url)
            if response:
                print("HTTP status:", response.status)
            else:
                print("No response object returned.")

            # Step 3: Try to handle consent/cookie banners
            try:
                # Try common selectors for consent buttons
                consent_selectors = [
                    'button:has-text("Accepter")',
                    'button:has-text("J\'accepte")',
                    '[id*="consent"] button',
                    '[class*="cookie"] button'
                ]
                for sel in consent_selectors:
                    consent_button = page.locator(sel)
                    if await consent_button.count() > 0:
                        print(f"Clicking consent button: {sel}")
                        await consent_button.click()
                        await page.wait_for_timeout(1000)
                        break
            except Exception as e:
                print("Consent banner not found or error:", e)

            # Step 4: Dump HTML for inspection
            html = await page.content()
            with open("page_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML dumped to page_dump.html")

            # Step 5: Define selectors (update after inspecting HTML dump)
            selectors = {
                "price": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-1rt48lp > span.css-otf0vo",
                "total_rooms": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(1) > span",
                "bedrooms": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(2) > span:nth-child(2)",
                "internal_surface": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(3) > span:nth-child(2)",
                "external_surface": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(4) > span:nth-child(2)",
                "city_zipcode": "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1tn1yel > button.css-8tb8om > div > span",
                "full_description": "#root > div > main > div.css-18xl464.MainColumn > div > section.css-13o7eu2.Section.Description > div > div > div.css-85qpxe.DescriptionTexts",
                "characteristics": "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(4) > div",
                "energy_performance": "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > div.css-1fobf8d > div > div:nth-child(1) > div",
                "construction_date": "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(1) > div > span:nth-child(2)",
                "heating_type": "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(3) > div > span:nth-child(2)",
                "heating_source": "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(4) > div > span:nth-child(2)",
            }

            # Step 6: Print and extract each field
            data = {}
            for key, sel in selectors.items():
                value = await get_text_safe(page, sel)
                print(f"{key}: {value} (selector: {sel})")
                data[key] = value

            await page.close()
            await browser.close()
            # Add redirected URL to output
            data["redirected_url"] = page.url
            return data

    except Exception as e:
        print("Exception occurred:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)