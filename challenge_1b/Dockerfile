FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    PyMuPDF==1.23.14 \
    nltk==3.8.1

# Copy the solution script
COPY main.py /app/

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the default command
CMD ["python", "main.py"]