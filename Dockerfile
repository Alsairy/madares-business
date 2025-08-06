FROM python:3.11-slim

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create upload directories
RUN mkdir -p uploads/property-deed uploads/ownership-docs uploads/construction-plans \
    uploads/financial-docs uploads/legal-docs uploads/inspection-reports

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

