FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libsndfile1 espeak-ng && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
ENV PORT=8000
EXPOSE $PORT
CMD uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300
