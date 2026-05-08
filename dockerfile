# Python image
FROM python:3.12.2-slim-bookworm

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV CONTAINER_MODE=true

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependency
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code (include folderul calculator_app, logs, etc.)
COPY . .

# Create necessary directories
RUN mkdir -p logs calculator_app/data

# Expose port Flask (5000)
EXPOSE 5000

# Run 
CMD ["python", "-m", "calculator_app.main"]

