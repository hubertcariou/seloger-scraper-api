from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI()

class ExtractRequest(BaseModel):
    url: str

async def get_text_safe(page, selector: str, timeout: int = 2000):
    try:
        locator = page.locator(selector)
        if await locator.count() > 0:
            return (await locator.inner_text(timeout=timeout)).strip()
    except Exception:
        pass
    return None

@app.post("/extract")
async def extract_data(req: ExtractRequest):
    url = req.url
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            try:
                await page.wait_for_selector("main", timeout=15000, state="attached")
            except:
                print("⚠️ <main> not found in time, continuing...")
                await page.wait_for_timeout(3000)

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

            data = {}
            for key, sel in selectors.items():
                data[key] = await get_text_safe(page, sel)

            await page.close()
            await browser.close()
            return data

    except Exception as e:
        return {"error": str(e)}
        