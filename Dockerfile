 # Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # PostgreSQL client
    postgresql-client \
    # Tesseract OCR and dependencies
    tesseract-ocr \
    libtesseract-dev \
    # PDF processing
    poppler-utils \
    # Image processing
    libmagickwand-dev \
    # Build essentials
    gcc \
    g++ \
    make \
    # Networking tools
    curl \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/schema/ || exit 1

# Default command
CMD ["gunicorn", "procure.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]



