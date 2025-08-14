#!/usr/bin/env bash
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Keep browser install in Render's persistent storage to speed up builds
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Install Chromium only (works on free plan)
python -m playwright install chromium
