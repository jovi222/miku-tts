FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Port yang digunakan HF Spaces
EXPOSE 7860

# Jalankan server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
