# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Create necessary directories
RUN mkdir -p /app/input /app/output

# Set the default command
CMD ["python", "app.py"]