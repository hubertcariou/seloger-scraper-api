#!/usr/bin/env bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright Chromium browser
python -m playwright install chromium
