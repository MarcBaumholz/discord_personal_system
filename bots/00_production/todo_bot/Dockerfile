FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs and data directories with proper permissions
RUN mkdir -p /app/logs /app/data && chmod -R 755 /app/logs /app/data

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash todobot && \
    chown -R todobot:todobot /app

# Switch to non-root user
USER todobot

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check using simple health check script
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python simple_health.py

# Run the Todo bot
CMD ["python", "todo_agent.py"]
