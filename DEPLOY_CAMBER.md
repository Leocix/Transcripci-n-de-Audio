# Deploy en Camber (Student Tier) — Guía rápida

Estos pasos asumen que usarás la build Docker del proyecto y la imagen será desplegada en Camber. Las recomendaciones son para el plan para estudiantes (recursos limitados).

Requisitos previos
- Tener Docker instalado.
- Cuenta en Camber (student tier activada).
- HF_TOKEN (si vas a usar diarización) — maneja como secret.

Variables recomendadas (en Camber Service env vars)
- WHISPER_MODEL=small
- HOST=0.0.0.0
- PORT=8888
- UPLOAD_DIR=/app/uploads
- MAX_FILE_SIZE=209715200  # 200MB
- HF_TOKEN=<tu_hf_token_aqui> (marcar como secreto)

Build y push de la imagen Docker
1. Construir la imagen localmente:

```powershell
# Desde la raíz del repo
docker build -t transcripcion-audio:latest .
```

2. Etiquetar y subir a DockerHub (o al registry que uses):

```powershell
docker tag transcripcion-audio:latest <tu-dockerhub-usuario>/transcripcion-audio:latest
docker push <tu-dockerhub-usuario>/transcripcion-audio:latest
```

Desplegar en Camber
1. En el panel de Camber, crear un nuevo servicio y seleccionar "Docker image".
2. Introduce la URL de la imagen en DockerHub y configura:
   - CMD/Entrypoint: `python main.py` o el CMD del Dockerfile
   - PORT: 8888 (o dejar que el contenedor use la variable interna)
3. Agrega las environment variables listadas arriba. Marca `HF_TOKEN` como secreto.
4. Revisa asignación de recursos: en Student tier, usa 1-2 vCPU y 4-8GB RAM si está disponible.

Pruebas post-deploy
- Health check:

```powershell
curl https://<tu-servicio-camber>/health
```

- Job de debug (no carga modelos):

```powershell
curl -X POST "https://<tu-servicio-camber>/debug/create_test_job" -d "duration_seconds=5"
```

- Subida de archivo pequeño (async):

```powershell
curl -F "file=@test.wav" -F "async_process=true" https://<tu-servicio-camber>/transcribe
```

Notas y recomendaciones
- Monitoriza logs para detectar descargas de modelos o OOM.
- Si necesitas modelos más grandes o rendimiento, considera usar una instancia con GPU o servicios de inferencia externos.

