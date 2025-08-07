# Use Python 3.11 slim image for ARM64 (Raspberry Pi)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot files
COPY . .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Create a non-root user for security and set proper ownership
RUN useradd --create-home --shell /bin/bash botuser && \
    chown -R botuser:botuser /app && \
    chmod -R 755 /app/logs

# Switch to non-root user
USER botuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=20s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/tmp/bots_running') else 1)"

# Default command - start both bot runner and dashboard
CMD ["python", "start_services.py"] 