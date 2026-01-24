FROM python:3.13-slim

# Installer les dépendances système pour WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
   # libgdk-pixbuf2.0-0 \
    libffi-dev \
    libssl-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app
COPY requirements.txt /app

EXPOSE 8000
