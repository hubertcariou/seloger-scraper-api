from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import requests
import logging
import os
import re

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
        text = locator.first.text_content()
        return text.strip() if text else None
    except:
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

            # --- Block unnecessary resources ---
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
            price_selectors = [".Price__Label", "span[data-testid='price']"]
            for sel in price_selectors:
                price = safe_text(page.locator(sel))
                if price:
                    data["Price"] = price
                    logging.info(f"Price: {data['Price']}")
                    break

            # Total Rooms
            room_selectors = ["span:has-text('Pièces')", "span[data-testid='rooms']"]
            for sel in room_selectors:
                rooms = safe_text(page.locator(sel))
                if rooms:
                    data["Total Rooms"] = rooms
                    break

            # Bedrooms
            bedroom_selectors = ["span:has-text('Chambres')", "span[data-testid='bedrooms']"]
            for sel in bedroom_selectors:
                bedrooms = safe_text(page.locator(sel))
                if bedrooms:
                    data["Bedrooms"] = bedrooms
                    break

            # Internal Surface
            surface_selectors = ["span:has-text('Surface')", "span[data-testid='surface']"]
            for sel in surface_selectors:
                surface = safe_text(page.locator(sel))
                if surface:
                    data["Internal Surface"] = surface
                    break

            # Field Surface
            field_selectors = ["span:has-text('Terrain')", "span[data-testid='field']"]
            for sel in field_selectors:
                field = safe_text(page.locator(sel))
                if field:
                    data["Field Surface"] = field
                    break

            # Description
            try:
                # Click "Voir plus" if present
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

            # Extra fallback: parse numeric info from characteristics
            for char in data["Characteristics"]:
                if not data["Total Rooms"] and re.search(r"Pièces\s*:\s*(\d+)", char):
                    data["Total Rooms"] = re.search(r"Pièces\s*:\s*(\d+)", char).group(1)
                if not data["Be]()
