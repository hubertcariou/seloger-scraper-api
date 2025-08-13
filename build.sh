#!/usr/bin/env bash
# Install Python dependencies
pip install -r requirements.txt

# Export persistent browser path
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Install Chromium only
python -m playwright install chromium
