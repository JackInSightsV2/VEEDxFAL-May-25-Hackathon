FROM python:3.9-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy .env file first (this will be overridden by environment variables if provided)
COPY .env /app/.env

# Copy application code
COPY . .

# Create directory for Google credentials
RUN mkdir -p /app/credentials && \
    chmod 755 /app/credentials

# Copy Google credentials
COPY veedxfal-hackathon-2025-ea1537c41d2c.json /app/credentials/google-credentials.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json

# Expose port for the FastAPI application
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
