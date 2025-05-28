FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5280 \
    PYTHONPATH=/app \
    TMPDIR=/app/tmp \
    GUNICORN_CMD_ARGS="--bind=0.0.0.0:5280 --workers=2 --threads=4 --worker-class=gthread"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Create necessary directories and set permissions
RUN mkdir -p logs tmp && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod 1777 /app/tmp

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5280

# Command to run the application with gunicorn
CMD ["gunicorn", "wsgi:app"] 