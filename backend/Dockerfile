FROM python:3.11-slim

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# Sistema (inclui ffmpeg libsndfile1 e libsndfile para áudio/librosa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential ffmpeg libsndfile1 libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Ambiente e porta
ENV FLASK_APP=src.main:app FLASK_ENV=production PYTHONPATH=/app
EXPOSE 8000

# Start (gunicorn em produção)
CMD ["gunicorn","--bind","0.0.0.0:8000","--workers","4","--timeout","120","src.main:app"]

