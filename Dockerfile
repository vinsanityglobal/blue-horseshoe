FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create artifact store directory
RUN mkdir -p /tmp/bh_artifacts

# Expose default port (Railway overrides with $PORT)
EXPOSE 8000

# Run the application — use $PORT if set (Railway), else default to 8000
CMD ["python3", "-c", "import os,uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))"]
