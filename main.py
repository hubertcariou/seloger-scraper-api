from fastapi import FastAPI, Request
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import uvicorn

app = FastAPI()

# Input model for POST /extract
class ExtractRequest(BaseModel):
    url: str

@app.post("/extract")
async def extract_data(req: ExtractRequest):
    url = req.url
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to the URL
            page.goto(url, timeout=60000)

            # Try to wait for <main>, but don't fail if missing
            try:
                page.wait_for_selector("main", timeout=15000, state="attached")
            except:
                print("⚠️ Warning: <main> selector not found within 15s, continuing anyway.")
                page.wait_for_timeout(3000)  # small delay for safety

            # Now extract fields based on your provided selectors
            data = {
                "price": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-1rt48lp > span.css-otf0vo"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-1rt48lp > span.css-otf0vo"
                ).count() > 0 else None,

                "total_rooms": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(1) > span"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(1) > span"
                ).count() > 0 else None,

                "bedrooms": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(2) > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(2) > span:nth-child(2)"
                ).count() > 0 else None,

                "internal_surface": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(3) > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(3) > span:nth-child(2)"
                ).count() > 0 else None,

                "external_surface": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(4) > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1ez736g > div.css-o51ctb > div > div:nth-child(4) > span:nth-child(2)"
                ).count() > 0 else None,

                "city_zipcode": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1tn1yel > button.css-8tb8om > div > span"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > h1 > div.css-1tn1yel > button.css-8tb8om > div > span"
                ).count() > 0 else None,

                "full_description": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section.css-13o7eu2.Section.Description > div > div > div.css-85qpxe.DescriptionTexts"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section.css-13o7eu2.Section.Description > div > div > div.css-85qpxe.DescriptionTexts"
                ).count() > 0 else None,

                "characteristics": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(4) > div"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(4) > div"
                ).count() > 0 else None,

                "energy_performance": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > div.css-1fobf8d > div > div:nth-child(1) > div"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > div.css-1fobf8d > div > div:nth-child(1) > div"
                ).count() > 0 else None,

                "construction_date": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(1) > div > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(1) > div > span:nth-child(2)"
                ).count() > 0 else None,

                "heating_type": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(3) > div > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(3) > div > span:nth-child(2)"
                ).count() > 0 else None,

                "heating_source": page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(4) > div > span:nth-child(2)"
                ).inner_text(timeout=2000) if page.locator(
                    "#root > div > main > div.css-18xl464.MainColumn > div > section:nth-child(8) > div > ul > li:nth-child(4) > div > span:nth-child(2)"
                ).count() > 0 else None,
            }

            browser.close()
            return data

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
