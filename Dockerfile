FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create artifact store directory
RUN mkdir -p /tmp/bh_artifacts

# Make startup script executable
RUN chmod +x /app/start.sh

# Expose default port (Railway overrides with $PORT env var)
EXPOSE 8000

# Start via script that reads $PORT from environment
CMD ["/app/start.sh"]
