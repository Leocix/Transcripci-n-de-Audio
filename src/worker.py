"""
Worker simple para procesar jobs en segundo plano.
- Escanea la carpeta uploads/jobs/ en busca de archivos JSON
- Descarga el objeto `source_url` usando requests
- Guarda el archivo en UPLOAD_DIR y ejecuta el job (transcribe o transcribe-diarize)

Este worker está pensado para correr como proceso separado (systemd, tmux, docker service, o App Platform worker service).
"""
import os
import time
import json
import logging
import requests
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = os.getenv('UPLOAD_DIR', str(PROJECT_ROOT / 'uploads'))
JOBS_DIR = os.path.join(UPLOAD_DIR, 'jobs')
FAILED_DIR = os.path.join(JOBS_DIR, 'failed')

# Asegurarse de que el path src esté en sys.path si se ejecuta desde el repo raíz
import sys
sys.path.insert(0, str(PROJECT_ROOT))

# Preferir imports relativos cuando se ejecuta como paquete `src`
try:
    from .transcriber import AudioTranscriber
    from .diarizer import SpeakerDiarizer
except Exception:
    # Fallback a imports absolutos (útil cuando se ejecuta el script directamente)
    from src.transcriber import AudioTranscriber
    from src.diarizer import SpeakerDiarizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('worker')

POLL_INTERVAL = int(os.getenv('WORKER_POLL_INTERVAL', '5'))
MAX_ATTEMPTS = int(os.getenv('WORKER_MAX_ATTEMPTS', '3'))


def download_to_path(url: str, out_path: str):
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return out_path


def process_job_file(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            job = json.load(f)
    except Exception as e:
        logger.error(f"No se pudo leer job file {path}: {e}")
        return False

    job_id = job.get('job_id')
    source_url = job.get('source_url')
    task = job.get('task', 'transcribe-diarize')
    whisper_model = job.get('whisper_model')
    num_speakers = job.get('num_speakers')
    attempts = int(job.get('attempts', 0))

    if not source_url:
        logger.error(f"Job {job_id} no tiene source_url")
        return False

    filename = os.path.basename(source_url.split('?')[0])
    local_path = os.path.join(UPLOAD_DIR, f"{job_id}_{filename}")

    try:
        logger.info(f"[JOB {job_id}] Descargando {source_url} -> {local_path}")
        download_to_path(source_url, local_path)
    except Exception as e:
        # Determinar si es un 404 (no existe) -> no tiene sentido reintentar
        is_http_err = isinstance(e, requests.HTTPError) or hasattr(e, 'response')
        status = None
        if hasattr(e, 'response') and getattr(e, 'response') is not None:
            try:
                status = int(getattr(e, 'response').status_code)
            except Exception:
                status = None

        logger.error(f"[JOB {job_id}] Error descargando source_url: {e} (status={status})")

        # Si es 404, marcar como intento final
        if status == 404:
            attempts = MAX_ATTEMPTS
        else:
            attempts += 1

        # Si excede intentos, mover job a carpeta failed con metadatos
        if attempts >= MAX_ATTEMPTS:
            os.makedirs(FAILED_DIR, exist_ok=True)
            try:
                # añadir metadatos
                job['attempts'] = attempts
                job['last_error'] = str(e)
                failed_name = os.path.basename(path) + '.failed'
                failed_path = os.path.join(FAILED_DIR, failed_name)
                with open(failed_path, 'w', encoding='utf-8') as ff:
                    json.dump(job, ff, ensure_ascii=False, indent=2)
                # eliminar job original
                try:
                    os.remove(path)
                except Exception:
                    pass
                logger.info(f"[JOB {job_id}] Movido a failed: {failed_path}")
            except Exception as mv_e:
                logger.error(f"[JOB {job_id}] Error moviendo a failed: {mv_e}")
            return False

        # actualizar contador en el mismo job file para reintentos posteriores
        try:
            job['attempts'] = attempts
            with open(path, 'w', encoding='utf-8') as wf:
                json.dump(job, wf, ensure_ascii=False)
        except Exception as wfe:
            logger.error(f"[JOB {job_id}] No se pudo actualizar intentos en job file: {wfe}")

        return False

    # Cargar o crear instancias
    transcriber = AudioTranscriber(model_name=whisper_model) if whisper_model else AudioTranscriber()

    if task == 'transcribe':
        logger.info(f"[JOB {job_id}] Ejecutando transcripción")
        res = transcriber.transcribe(local_path)
        logger.info(f"[JOB {job_id}] Transcripción completada: {len(res.get('text',''))} chars")
    else:
        logger.info(f"[JOB {job_id}] Ejecutando transcripción + diarización")
        trans_result = transcriber.transcribe_with_timestamps(local_path)
        try:
            diarizer = SpeakerDiarizer()
            dia = diarizer.diarize(local_path)
            logger.info(f"[JOB {job_id}] Diarización completada: {len(dia)} segments")
        except Exception as e:
            logger.error(f"[JOB {job_id}] Error en diarización: {e}")

    # Borrar el job file para marcarlo como procesado
    try:
        os.remove(path)
    except Exception:
        pass

    # Borrar archivo local descargado
    try:
        os.remove(local_path)
    except Exception:
        pass

    return True


def main_loop():
    logger.info("Worker arrancando, escaneando jobs en: %s" % JOBS_DIR)
    while True:
        try:
            os.makedirs(JOBS_DIR, exist_ok=True)
            os.makedirs(FAILED_DIR, exist_ok=True)
            for fname in os.listdir(JOBS_DIR):
                if not fname.endswith('.json'):
                    continue
                full = os.path.join(JOBS_DIR, fname)
                try:
                    process_job_file(full)
                except Exception as e:
                    logger.error(f"Error procesando job {full}: {e}")
        except FileNotFoundError:
            logger.info("JOBS_DIR no encontrado, creando...")
            os.makedirs(JOBS_DIR, exist_ok=True)
        except Exception as e:
            logger.error(f"Error en el loop del worker: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main_loop()
