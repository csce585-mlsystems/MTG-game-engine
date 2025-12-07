# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies with verbose output
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "echo 'MTG Game Engine Backend starting...' && echo 'Backend API available at: http://localhost:8000' && echo 'API Documentation available at: http://localhost:8000/docs' && echo 'Health check available at: http://localhost:8000/health' && DB_PATH=${SCRYFALL_DB_PATH:-data/scryfall.db} && if [ ! -f \"$DB_PATH\" ]; then echo 'Initializing Scryfall DB at' \"$DB_PATH\" 'from Scryfall bulk data...'; python app/scryfall_import.py --db \"$DB_PATH\" --mode bulk; fi && echo 'Starting FastAPI server...' && uvicorn app.api:app --host 0.0.0.0 --port 8000"]
