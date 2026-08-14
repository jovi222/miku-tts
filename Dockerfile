FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libsndfile1 espeak-ng curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from kokoro_onnx import Kokoro; Kokoro.from_pretrained()"
COPY app.py .
ENV PORT=8000
EXPOSE $PORT
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
