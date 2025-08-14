#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Export persistent browser path (keeps Playwright browser install cached between builds)
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Install Firefox (with all required OS-level deps) instead of Chromium
python -m playwright install --with-deps firefox

