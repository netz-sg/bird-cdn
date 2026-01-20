FROM python:3.12-slim

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    git \
    docker.io \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application Code
COPY . .

# Make scripts executable
RUN chmod +x /app/cron_aggregate_logs.py && \
    chmod +x /app/setup_tracking_cron.sh && \
    chmod +x /app/start.sh

# Create cache and log directories
RUN mkdir -p /var/cache/nginx /var/log

# Expose Port
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run Application
CMD ["/app/start.sh"]
