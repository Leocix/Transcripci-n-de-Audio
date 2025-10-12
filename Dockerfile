# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de sistema necesarias (incluye ffmpeg para procesamiento de audio/video)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ffmpeg git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY config/requirements.txt /app/config/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r /app/config/requirements.txt

# Copiar el código de la aplicación
COPY . /app

# Crear directorio de uploads y asegurar permisos
RUN mkdir -p /app/uploads
ENV UPLOAD_DIR=/app/uploads

EXPOSE 8888

# Usar la variable PORT provista por Render o 8888 por defecto
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8888} --workers 1 --log-level info"]
# Dockerfile para desplegar en Render
# Usa una imagen ligera de Python, instala ffmpeg y dependencias

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /app

# Copiar requirements y código
COPY config/requirements.txt ./config/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r config/requirements.txt

# Copiar el resto del proyecto
COPY . /app

# Exponer puerto (Render utiliza $PORT)
ENV PORT=8888
EXPOSE 8888

CMD ["python", "main.py"]
