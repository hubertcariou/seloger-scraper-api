# Use official Playwright image with Python and Chromium preinstalled
FROM mcr.microsoft.com/playwright:v1.54.0-focal

# Set working directory
WORKDIR /app

# Copy Python dependencies first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port that Flask uses
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]
