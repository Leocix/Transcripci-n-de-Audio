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
import threading
import concurrent.futures

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = os.getenv('UPLOAD_DIR', str(PROJECT_ROOT / 'uploads'))

# Intentar importar ensure_upload_dirs desde src.utils para asegurarnos de que las carpetas existen
try:
    from src.utils import ensure_upload_dirs
except Exception:
    ensure_upload_dirs = None

if ensure_upload_dirs:
    paths = ensure_upload_dirs(UPLOAD_DIR)
    JOBS_DIR = paths.get('jobs_dir')
    FAILED_DIR = paths.get('failed_dir')
else:
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

# Configurables
POLL_INTERVAL = int(os.getenv('WORKER_POLL_INTERVAL', '5'))
MAX_ATTEMPTS = int(os.getenv('WORKER_MAX_ATTEMPTS', '3'))
# Número de workers concurrentes para procesar jobs (1 = secuencial)
WORKER_MAX_WORKERS = int(os.getenv('WORKER_MAX_WORKERS', '1'))

# Singletons para reutilizar cargas de modelos pesados
_transcriber_singleton = None
_diarizer_singleton = None
_singleton_lock = threading.Lock()


def download_to_path(url: str, out_path: str):
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return out_path


def _load_job(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"No se pudo leer job file {path}: {e}")
        return None


def _move_to_failed(job: dict, src_path: str, error: str = None):
    os.makedirs(FAILED_DIR, exist_ok=True)
    try:
        job['last_error'] = error
        job['attempts'] = job.get('attempts', 0)
        failed_name = os.path.basename(src_path) + '.failed'
        failed_path = os.path.join(FAILED_DIR, failed_name)
        with open(failed_path, 'w', encoding='utf-8') as ff:
            json.dump(job, ff, ensure_ascii=False, indent=2)
        try:
            os.remove(src_path)
        except Exception:
            pass
        logger.info(f"[JOB {job.get('job_id')}] Movido a failed: {failed_path}")
    except Exception as mv_e:
        logger.error(f"[JOB {job.get('job_id')}] Error moviendo a failed: {mv_e}")


def process_job_file(path: str):
    """Procesa un job JSON. La función asume que el archivo ya fue renombrado a .processing"""
    job = _load_job(path)
    if not job:
        return False

    job_id = job.get('job_id')
    source_url = job.get('source_url')
    task = job.get('task', 'transcribe-diarize')
    whisper_model = job.get('whisper_model')
    num_speakers = job.get('num_speakers')
    attempts = int(job.get('attempts', 0))

    if not source_url:
        logger.error(f"[JOB {job_id}] no tiene source_url")
        _move_to_failed(job, path, error='missing_source_url')
        return False

    filename = os.path.basename(source_url.split('?')[0])
    local_path = os.path.join(UPLOAD_DIR, f"{job_id}_{filename}")

    try:
        logger.info(f"[JOB {job_id}] Descargando {source_url} -> {local_path}")
        download_to_path(source_url, local_path)
    except Exception as e:
        status = None
        if hasattr(e, 'response') and getattr(e, 'response') is not None:
            try:
                status = int(getattr(e, 'response').status_code)
            except Exception:
                status = None

        logger.error(f"[JOB {job_id}] Error descargando source_url: {e} (status={status})")
        attempts = attempts + 1
        job['attempts'] = attempts

        if attempts >= MAX_ATTEMPTS or status == 404:
            _move_to_failed(job, path, error=str(e))
            return False

        # actualizar contador y renombrar de vuelta para reintento
        try:
            with open(path, 'w', encoding='utf-8') as wf:
                json.dump(job, wf, ensure_ascii=False)
        except Exception as wfe:
            logger.error(f"[JOB {job_id}] No se pudo actualizar intentos en job file: {wfe}")

        return False

    # Obtener singletons de modelos con bloqueo
    global _transcriber_singleton, _diarizer_singleton
    with _singleton_lock:
        if _transcriber_singleton is None:
            _transcriber_singleton = AudioTranscriber(model_name=whisper_model) if whisper_model else AudioTranscriber()
        if _diarizer_singleton is None:
            # crear diarizer solo si será necesario
            if task != 'transcribe':
                _diarizer_singleton = SpeakerDiarizer()

    transcriber = _transcriber_singleton

    try:
        if task == 'transcribe':
            logger.info(f"[JOB {job_id}] Ejecutando transcripción")
            res = transcriber.transcribe(local_path)
            logger.info(f"[JOB {job_id}] Transcripción completada: {len(res.get('text',''))} chars")
        else:
            logger.info(f"[JOB {job_id}] Ejecutando transcripción + diarización")
            trans_result = transcriber.transcribe_with_timestamps(local_path)
            try:
                diarizer = _diarizer_singleton or SpeakerDiarizer()
                dia = diarizer.diarize(local_path)
                logger.info(f"[JOB {job_id}] Diarización completada: {len(dia)} segments")
            except Exception as e:
                logger.exception(f"[JOB {job_id}] Error en diarización: {e}")
    except Exception as e:
        logger.exception(f"[JOB {job_id}] Error procesando job: {e}")
        # mover a failed si falla la transcripción gravemente
        _move_to_failed(job, path, error=str(e))
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass
        return False

    # Procesado exitoso: eliminar job file y archivo local
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"[JOB {job_id}] No se pudo eliminar job file: {e}")

    try:
        if os.path.exists(local_path):
            os.remove(local_path)
    except Exception:
        pass

    # Guardar resultados en disco para que la UI/usuarios puedan descargarlos
    try:
        results_dir = os.path.join(UPLOAD_DIR, 'results')
        os.makedirs(results_dir, exist_ok=True)

        job_result = {
            'job_id': job_id,
            'task': task,
            'whisper_model': whisper_model,
            'transcription': trans_result.get('text') if 'trans_result' in locals() and isinstance(trans_result, dict) else (res.get('text') if 'res' in locals() and isinstance(res, dict) else None),
            'segments': trans_result.get('segments') if 'trans_result' in locals() and isinstance(trans_result, dict) else (res.get('segments') if 'res' in locals() and isinstance(res, dict) else None),
            'diarization': dia if 'dia' in locals() else None,
            'timestamp': datetime.utcnow().isoformat()
        }

        json_path = os.path.join(results_dir, f"{job_id}.json")
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(job_result, jf, ensure_ascii=False, indent=2)

        # Guardar sólo el texto en un archivo .txt para descarga rápida
        txt_path = os.path.join(results_dir, f"{job_id}.txt")
        try:
            text_out = job_result.get('transcription') or ''
            with open(txt_path, 'w', encoding='utf-8') as tf:
                tf.write(text_out)
        except Exception:
            pass

        logger.info(f"[JOB {job_id}] Resultados guardados en: {json_path}")
    except Exception as e:
        logger.warning(f"[JOB {job_id}] No se pudieron guardar resultados: {e}")

    return True


def main_loop():
    logger.info("Worker arrancando, escaneando jobs en: %s" % JOBS_DIR)
    # Asegurar directorios antes de arrancar el loop principal (por si no se ejecut f3 startup de FastAPI)
    try:
        if ensure_upload_dirs:
            ensure_upload_dirs(UPLOAD_DIR)
        else:
            os.makedirs(JOBS_DIR, exist_ok=True)
            os.makedirs(FAILED_DIR, exist_ok=True)
            os.makedirs(os.path.join(UPLOAD_DIR, 'results'), exist_ok=True)
    except Exception:
        logger.exception("No se pudieron asegurar los directorios de uploads en worker")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=WORKER_MAX_WORKERS)
    futures = set()

    while True:
        try:
            os.makedirs(JOBS_DIR, exist_ok=True)
            os.makedirs(FAILED_DIR, exist_ok=True)

            # Limpiar futures completados
            done = {f for f in futures if f.done()}
            futures -= done

            # Recolectar archivos .json disponibles
            for fname in os.listdir(JOBS_DIR):
                if not fname.endswith('.json'):
                    continue

                # Limit concurrency
                if len(futures) >= WORKER_MAX_WORKERS:
                    break

                full = os.path.join(JOBS_DIR, fname)
                processing_path = full + '.processing'

                try:
                    # Intentar renombrar atómicamente para marcar como tomado
                    os.replace(full, processing_path)
                except FileNotFoundError:
                    # Otro proceso ya lo tomó
                    continue
                except Exception as e:
                    logger.error(f"[JOBFILE] No se pudo mover {full} a processing: {e}")
                    continue

                # Enviar a executor
                fut = executor.submit(process_job_file, processing_path)
                futures.add(fut)

        except FileNotFoundError:
            logger.info("JOBS_DIR no encontrado, creando...")
            os.makedirs(JOBS_DIR, exist_ok=True)
        except Exception as e:
            logger.exception(f"Error en el loop del worker: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main_loop()
