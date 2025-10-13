Guía rápida para configurar variables de entorno en RenderDespliegue en Render

====================

Recomendación: configura estas variables en el panel de Environment (Service > Environment > Environment Variables) o como Secrets si contienen valores sensibles.

Esta guía explica cómo desplegar la API de Transcripción en Render usando Docker. También cubre recomendaciones para usar GPU y una opción para separar la inferencia en una máquina con GPU.

Variables sugeridas

Requisitos

- WHISPER_MODEL----------

  - Descripción: Modelo Whisper a usar para transcripción.- Cuenta en Render (https://render.com)

  - Recomendado para Render (CPU): "small" o "base". Evita "large-v3" en entornos con memoria limitada.- Repositorio con este proyecto conectado a Render o subir Dockerfile

  - Ejemplo: WHISPER_MODEL=small- Secrets / Variables de entorno: HF_TOKEN (Hugging Face)



- HF_TOKENPasos rápidos

  - Descripción: Token de Hugging Face necesario para la diarización (pyannote).-------------

  - Seguro: marcar como secret.1. En el repositorio encontrarás un `Dockerfile` preparado para Render y un `render.yaml` de ejemplo.

  - Ejemplo: HF_TOKEN=hf_xxx...2. Conecta el repositorio a Render y crea un nuevo servicio tipo "Web Service" usando Docker.

3. En la configuración del servicio agrega variables de entorno:

- MAX_FILE_SIZE   - `WHISPER_MODEL` (ej: `base`, `small`, `medium`)

  - Descripción: Tamaño máximo de archivo permitido (bytes).   - `HF_TOKEN` (token de Hugging Face) — marcar como secreto.

  - Recomendado: 500 MB = 524288000   - `MAX_FILE_SIZE` (bytes) — por defecto 524288000 (500MB) en `render.yaml`.

  - Ejemplo: MAX_FILE_SIZE=5242880004. Despliega y revisa logs. El servicio expondrá la API en el puerto configurado.



- UPLOAD_DIRNotas sobre GPU

  - Descripción: Ruta donde se guardan archivos subidos dentro del contenedor.---------------

  - Recomendado: "/app/uploads"- Render no ofrece GPUs en planes básicos. Para usar GPU necesitas:

  - Ejemplo: UPLOAD_DIR=/app/uploads  - Desplegar la inferencia en una instancia con GPU (AWS, GCP, Paperspace, etc.) y exponer un endpoint seguro.

  - O usar servicios especializados (Hugging Face Inference, Lambda con GPU, etc.).

- HOST (opcional)- Si vas a usar GPU local o en la nube, instala una versión de PyTorch compatible con la versión de CUDA del host (ver https://pytorch.org/get-started/locally/).

  - Descripción: Host a bindear. Ya por defecto está en 0.0.0.0, no es necesario cambiar.

  - Ejemplo: HOST=0.0.0.0Arquitectura recomendada para producción con GPU

------------------------------------------------

- PORT- Opción A (Rápida): Desplegar toda la app en un equipo con GPU (no soportado por Render). Requiere Docker con drivers CUDA.

  - Render provee la variable $PORT automáticamente en el entorno; no necesitas fijarla.- Opción B (Recomendada): Separar la web (Render) y la inferencia (servidor GPU):

  1. Web en Render (maneja uploads, UI, almacenamiento temporal).

Notas y recomendaciones  2. Servidor de inferencia en una VM GPU: servicio REST protegido que reciba archivos (o rutas S3) y devuelva transcripción.

  3. Web en Render hace peticiones al servidor GPU para procesar archivos grandes.

1. Modelos grandes

   - Evita usar modelos "large" o "large-v3" en Render si tu instancia es pequeña. El peso del modelo (2–3GB) puede agotar disco/tiempo de build.Seguridad

   - Si necesitas accuracy alta, considera usar:---------

     - Un servicio separado con GPU (VM o cloud provider) que exponga una API, o- Protege el endpoint de inferencia con autenticación (tokens o IP allowlist).

     - Procesamiento por lotes local con subida a S3 y una instancia dedicada.- No publiques `HF_TOKEN` como valor plano; usa secretos en Render.



2. Persistencia de uploadsArchivos incluidos

   - Render ofrece discos persistentes; si quieres conservar subidas, habilita Persistent Disk y apunta `UPLOAD_DIR` allí.------------------

   - Alternativa: usar S3 y modificar la app para leer/guardar desde S3.- `Dockerfile` — Dockerfile preparado para renderizar la app en CPU.

- `render.yaml` — ejemplo de configuración para Render.

3. Diarización

   - Requiere `HF_TOKEN`. Si no lo configuras, los endpoints de diarización devolverán error 503.Si quieres, puedo:

- Generar un `docker-compose.yml` para pruebas locales con ffmpeg.

4. Seguridad- Crear un ejemplo de servidor de inferencia GPU (FastAPI + Dockerfile con CUDA base) y detallarte cómo comunicarlo con la app en Render.

   - Marca `HF_TOKEN` como secret.
   - Si la API queda pública, considera añadir una API key o autenticación para limitar el uso.

Pasos rápidos

1. Ve al dashboard de tu servicio en Render > Environment.
2. Añade las variables arriba (marca secrets). Ejemplo mínimo:
   - WHISPER_MODEL=small
   - HF_TOKEN=<tu_token>
   - MAX_FILE_SIZE=524288000
   - UPLOAD_DIR=/app/uploads
3. Despliega o reinicia el servicio.
4. Revisa logs y abre la URL pública para comprobar `/health` y la UI.
