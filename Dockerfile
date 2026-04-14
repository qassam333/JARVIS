FROM python:3.11-slim

LABEL maintainer="JARVIS"
LABEL description="JARVIS - Local AI Assistant"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN mkdir -p /app/data /app/voices /app/whisper.cpp/models

ENV JARVIS_DATA_DIR=/app/data
ENV JARVIS_DB_PATH=/app/data/jarvis.db

EXPOSE 8000

VOLUME ["/app/data", "/app/voices", "/app/whisper.cpp/models"]

ENTRYPOINT ["python", "-m", "jarvis.main"]
CMD ["--help"]
