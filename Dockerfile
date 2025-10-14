FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Herramientas mínimas para construir ruedas
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar sólo requirements para aprovechar la cache de Docker
ARG REQUIREMENTS=config/requirements.txt
COPY ${REQUIREMENTS} /app/config/requirements.txt

# Instalar dependencias Python directamente en /usr/local (sitio esperado por el runtime)
RUN python -m pip install --upgrade pip setuptools wheel --root-user-action=ignore \
    && pip install --no-cache-dir --prefix=/usr/local --root-user-action=ignore -r /app/config/requirements.txt


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de sistema necesarias para runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg libsndfile1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes Python instalados desde el builder
COPY --from=builder /install /usr/local

# Copiar la aplicacion (usa .dockerignore para reducir contexto)
COPY . /app

# Directorio para uploads
RUN mkdir -p /app/uploads && chown -R root:root /app/uploads
ENV UPLOAD_DIR=/app/uploads

# Asegurar que pip/entrypoints estén en PATH
ENV PATH=/usr/local/bin:$PATH

EXPOSE 8888

# Ejecutar con uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8888} --workers 1 --log-level info"]
