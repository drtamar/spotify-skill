FROM python:3.11-slim

WORKDIR /app

# System deps for cairosvg (optional, skip if not needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY spotify-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# App source
COPY spotify-api/ ./spotify-api/

# Entrypoint
WORKDIR /app/spotify-api/scripts
ENV PYTHONPATH=/app/spotify-api
ENV PORT=8080

CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60 \
    "party_dj_server:app"
