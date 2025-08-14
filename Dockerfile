# Use the official Playwright Python image (already includes Chromium)
FROM mcr.microsoft.com/playwright/python:v1.54.0

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port used by your Flask app
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
