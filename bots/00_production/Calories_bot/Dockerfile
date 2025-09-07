# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY calories_bot.py ./bot.py
COPY chart_generator.py .
COPY logger_config.py .
COPY monthly_report.py .
COPY notion_data_reader.py .
COPY scheduler.py .
COPY ground_truth_foods.json .

# Create necessary directories
RUN mkdir -p logs/errors logs/food_analysis logs/monthly_reports logs/system logs/user_activity reports

# Create a non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "bot.py"]