#!/usr/bin/env bash

# Install Python dependencies
pip install -r requirements.txt

# Set persistent Playwright browser path
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Install only Chromium (minimal footprint)
python -m playwright install chromium --with-deps

# Optional: Clean cache to save space
rm -rf /root/.cache/pip
rm -rf /root/.cache/ms-playwright
