import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SeLoger Scraper API",
    description="Extracts real estate data from SeLoger listings.",
    version="1.0.0"
)

# Enable CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str

class ExtractResponse(BaseModel):
    redirected_url: str
    price: str
    total_rooms: str
    bedrooms: str
    internal_surface: str
    external_surface: str
    city_zipcode: str
    full_description: str
    characteristics: str
    energy_performance: str
    construction_date: str
    heating_type: str
    heating_source: str

@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
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

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            context = await browser.new_context()
            page = await context.new_page()
            try:
                logger.info(f"Navigating to {request.url}")
                await page.goto(request.url, timeout=20000, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                logger.error("Timeout loading the page.")
                raise HTTPException(status_code=504, detail="Timeout loading the page.")

            # --- GDPR Consent Handling ---
            try:
                consent_button = await page.query_selector("button:has-text('Tout accepter')")
                if consent_button:
                    await consent_button.click()
                    logger.info("GDPR consent accepted.")
                    await page.wait_for_timeout(1000)  # Wait for UI update
            except Exception as e:
                logger.warning(f"GDPR consent button not found or could not be clicked: {e}")

            # --- Data Extraction ---
            extracted = {}
            for field, selector in selectors.items():
                try:
                    value = await page.text_content(selector)
                    extracted[field] = value.strip() if value else ""
                except Exception as e:
                    logger.warning(f"Could not extract '{field}': {e}")
                    extracted[field] = ""

            redirected_url = page.url
            logger.info(f"Extraction successful for {redirected_url}")

            return ExtractResponse(
                redirected_url=redirected_url,
                **extracted
            )
    except HTTPException:
        raise  # Already handled above
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# Optional: health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}