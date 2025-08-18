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
    title: str
    price: str
    address: str
    description: str
    # Add more fields as needed

@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
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

            # --- Data Extraction (replace selectors as needed) ---
            try:
                title = await page.text_content("h1[data-testid='ad-title']") or ""
                price = await page.text_content("span[data-testid='ad-price']") or ""
                address = await page.text_content("div[data-testid='ad-address']") or ""
                description = await page.text_content("div[data-testid='ad-description']") or ""
            except Exception as e:
                logger.error(f"Error extracting fields: {e}")
                raise HTTPException(status_code=500, detail="Error extracting fields.")

            redirected_url = page.url

            logger.info(f"Extraction successful for {redirected_url}")

            return ExtractResponse(
                redirected_url=redirected_url,
                title=title.strip(),
                price=price.strip(),
                address=address.strip(),
                description=description.strip(),
                # Add more fields as needed
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