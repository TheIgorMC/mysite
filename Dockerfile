# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Cache busting - change CACHE_BUST value in docker-compose.yml to force rebuild from this point
ARG CACHE_BUST=1
RUN echo "Cache bust: ${CACHE_BUST}"

# Copy application code (this layer will be rebuilt when CACHE_BUST changes)
COPY site01/ ./site01/

# Make entrypoint script executable
RUN chmod +x /app/site01/entrypoint.sh

# Clear Python bytecode cache to ensure fresh templates
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type f -name "*.pyc" -delete 2>/dev/null || true

# Set Python path to include site01 directory
ENV PYTHONPATH=/app:/app/site01

# Create necessary directories
RUN mkdir -p /app/site01/instance /app/site01/logs /app/data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Set working directory to site01 for proper imports
WORKDIR /app/site01

# Use entrypoint script to run migrations and start app
ENTRYPOINT ["/app/site01/entrypoint.sh"]
