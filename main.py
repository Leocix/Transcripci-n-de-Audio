from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import uuid
import logging
from datetime import datetime
import aiofiles
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / "config" / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    logger_setup = logging.getLogger(__name__)
    logger_setup.warning(f"Archivo .env no encontrado en: {ENV_FILE}")

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.transcriber import AudioTranscriber
from src.diarizer import SpeakerDiarizer
from src.video_converter import VideoConverter, is_video_file
from src.utils import (
    align_transcription_with_diarization,
    format_transcript,
    get_speaker_statistics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Transcription & Diarization API",
    description="API para transcribir audio e identificar hablantes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = PROJECT_ROOT / "web"
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "uploads"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
HF_TOKEN = os.getenv("HF_TOKEN")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))

os.makedirs(UPLOAD_DIR, exist_ok=True)

transcriber = None
diarizer = None
video_converter = None


def get_transcriber():
    global transcriber
    if transcriber is None:
        logger.info(f"Cargando modelo Whisper: {WHISPER_MODEL}")
        transcriber = AudioTranscriber(model_name=WHISPER_MODEL)
    return transcriber


def get_diarizer():
    global diarizer
    if diarizer is None:
        logger.info("Cargando pipeline de diarización")
        diarizer = SpeakerDiarizer(hf_token=HF_TOKEN)
    return diarizer


def get_video_converter():
    global video_converter
    if video_converter is None:
        logger.info("Inicializando convertidor de video")
        video_converter = VideoConverter(output_dir=UPLOAD_DIR)
    return video_converter


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


class TranscriptionResponse(BaseModel):
    job_id: str
    text: str
    language: str
    segments: List[dict]
    statistics: Optional[dict] = None
    formatted_transcript: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    whisper_model: str
    device: str


@app.get("/", response_class=HTMLResponse, tags=["General"])
async def root():
    html_file = WEB_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return HTMLResponse(
            content="<h1>Error: No se encontró index.html</h1>",
            status_code=404
        )


@app.get("/api", tags=["General"])
async def api_info():
    return {
        "message": "API de Transcripción de Audio con Diarización",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "transcribe": "/transcribe",
            "transcribe_with_diarization": "/transcribe-diarize",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    transcriber_instance = get_transcriber()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        whisper_model=WHISPER_MODEL,
        device=str(transcriber_instance.device)
    )


@app.get("/debug", tags=["General"])
async def debug_info():
    import torch
    return {
        "status": "ok",
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "whisper_model": WHISPER_MODEL,
        "hf_token_configured": bool(HF_TOKEN),
        "hf_token_length": len(HF_TOKEN) if HF_TOKEN else 0,
        "upload_dir": UPLOAD_DIR,
        "upload_dir_exists": os.path.exists(UPLOAD_DIR),
        "web_dir": str(WEB_DIR),
        "web_dir_exists": WEB_DIR.exists(),
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024
    }


@app.post("/transcribe", tags=["Transcription"])
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe"),
    output_format: str = Form("text")
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    job_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_extension}")
    
    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Procesando transcripción para job_id: {job_id}")
        
        transcriber_instance = get_transcriber()
        result = transcriber_instance.transcribe(
            temp_path,
            language=language,
            task=task
        )
        
        return {
            "job_id": job_id,
            "text": result["text"],
            "language": result["language"],
            "segments": result["segments"],
            "model": result["model"]
        }
        
    except Exception as e:
        logger.error(f"Error en transcripción: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error al transcribir: {type(e).__name__}: {str(e)}"
        )
    
    finally:
         archivo temporal
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


@app.post("/transcribe-diarize", tags=["Transcription"])
async def transcribe_with_diarization(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    num_speakers: Optional[int] = Form(None),
    min_speakers: Optional[int] = Form(None),
    max_speakers: Optional[int] = Form(None),
    output_format: str = Form("text")
):
    """
    Transcribe audio e identifica hablantes.
    
    Args:
        file: Archivo de audio
        language: Código de idioma
        num_speakers: Número exacto de hablantes (opcional)
        min_speakers: Número mínimo de hablantes (opcional)
        max_speakers: Número máximo de hablantes (opcional)
        output_format: Formato de salida ('text', 'detailed', 'srt')
    
    Returns:
        Transcripción con identificación de hablantes
    """
     HF_TOKEN
    if not HF_TOKEN:
        logger.error("HF_TOKEN no configurado")
        raise HTTPException(
            status_code=503,
            detail="HF_TOKEN no configurado. Se requiere para diarización."
        )
    
    # Leer contenido
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error al leer archivo: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer el archivo: {str(e)}"
        )
    
     tamaño
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío"
        )
    
     archivo
    job_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".webm"
    
    # Si no tiene extensión o es webm, convertir a wav
    if not file_extension or file_extension.lower() in ['.webm', '.ogg']:
        file_extension = '.wav'
    
    temp_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_extension}")
    
    logger.info(f"=== INICIANDO PROCESAMIENTO ===")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Archivo original: {file.filename}")
    logger.info(f"Tipo MIME: {file.content_type}")
    logger.info(f"Tamaño: {len(content) / 1024:.2f} KB")
    logger.info(f"Ruta temporal: {temp_path}")
    
    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Procesando transcripción + diarización para job_id: {job_id}")
        logger.info(f"Archivo guardado: {temp_path}")
        logger.info(f"Tamaño: {len(content) / 1024:.2f} KB")
        
        # 1. Transcribir
        logger.info("Paso 1/5: Cargando modelo Whisper...")
        transcriber_instance = get_transcriber()
        
        logger.info("Paso 2/5: Transcribiendo audio...")
        trans_result = transcriber_instance.transcribe_with_timestamps(
            temp_path,
            language=language
        )
        logger.info(f"Transcripción completada: {len(trans_result)} segmentos")
        
        # 2. Diarizar
        logger.info("Paso 3/5: Cargando modelo de diarización...")
        try:
            diarizer_instance = get_diarizer()
        except Exception as e:
            logger.error(f"Error al cargar diarizador: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error al cargar modelo de diarización: {str(e)}. Verifica tu HF_TOKEN y conexión a internet."
            )
        
        logger.info("Paso 4/5: Identificando hablantes...")
        dia_segments = diarizer_instance.diarize(
            temp_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        logger.info(f"Diarización completada: {len(dia_segments)} segmentos")
        
        # 3. Combinar
        logger.info("Paso 5/5: Combinando resultados...")
        aligned_segments = align_transcription_with_diarization(
            trans_result,
            dia_segments
        )
        
        # 4. Formatear
        formatted_text = format_transcript(aligned_segments, output_format)
        
        # 5. Estadísticas
        statistics = get_speaker_statistics(aligned_segments)
        
        return {
            "job_id": job_id,
            "text": formatted_text,
            "segments": aligned_segments,
            "statistics": statistics,
            "num_speakers": len(statistics),
            "output_format": output_format
        }
        
    except Exception as e:
        logger.error(f"Error en transcripción + diarización: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar: {type(e).__name__}: {str(e)}"
        )
    
    finally:
        
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")


@app.post("/convert-video", tags=["Video"])
async def convert_video_to_audio(
    file: UploadFile = File(...),
    bitrate: str = Form("192k"),
    sample_rate: int = Form(44100)
):
    """
    Convierte un archivo de video a MP3 (solo audio).
    
    Args:
        file: Archivo de video (mp4, avi, mov, mkv, etc.)
        bitrate: Bitrate del audio (ej: "128k", "192k", "320k")
        sample_rate: Frecuencia de muestreo (44100, 48000)
    
    Returns:
        Archivo MP3 con el audio extraído
    """
     que sea un video
    if not is_video_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un video (mp4, avi, mov, mkv, etc.)"
        )
    
     tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
     video temporalmente
    job_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    temp_video_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_extension}")
    
    try:
        async with aiofiles.open(temp_video_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Convirtiendo video a MP3 para job_id: {job_id}")
        
         video a MP3
        converter = get_video_converter()
        mp3_filename = f"{job_id}.mp3"
        mp3_path = converter.convert_video_to_mp3(
            temp_video_path,
            output_filename=mp3_filename,
            bitrate=bitrate,
            sample_rate=sample_rate
        )
        
        # Obtener información del video
        video_info = converter.get_video_info(temp_video_path)
        
        return {
            "job_id": job_id,
            "message": "Video convertido exitosamente a MP3",
            "mp3_filename": mp3_filename,
            "mp3_path": mp3_path,
            "video_info": {
                "duration": video_info.get("duration", 0),
                "had_audio": video_info.get("has_audio", False),
                "original_format": video_info.get("format", "unknown")
            },
            "audio_settings": {
                "bitrate": bitrate,
                "sample_rate": sample_rate
            }
        }
        
    except Exception as e:
        logger.error(f"Error al convertir video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
         archivo de video temporal
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Archivo temporal de video eliminado: {temp_video_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar video temporal: {e}")


@app.post("/convert-and-transcribe", tags=["Video"])
async def convert_video_and_transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    num_speakers: Optional[int] = Form(None),
    min_speakers: Optional[int] = Form(None),
    max_speakers: Optional[int] = Form(None),
    output_format: str = Form("text"),
    bitrate: str = Form("192k")
):
    """
    Convierte un video a audio y lo transcribe con diarización en un solo paso.
    
    Args:
        file: Archivo de video
        language: Código de idioma
        num_speakers: Número exacto de hablantes (opcional)
        min_speakers: Número mínimo de hablantes (opcional)
        max_speakers: Número máximo de hablantes (opcional)
        output_format: Formato de salida ('text', 'detailed', 'srt')
        bitrate: Bitrate del audio
    
    Returns:
        Transcripción con identificación de hablantes
    """
     HF_TOKEN
    if not HF_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="HF_TOKEN no configurado. Se requiere para diarización."
        )
    
     que sea un video
    if not is_video_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un video"
        )
    
     tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
     video
    job_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    temp_video_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_extension}")
    mp3_path = None  # Inicializar para evitar UnboundLocalError
    
    try:
        async with aiofiles.open(temp_video_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Procesando video completo para job_id: {job_id}")
        
        # 1. Convertir a MP3
        converter = get_video_converter()
        mp3_filename = f"{job_id}.mp3"
        mp3_path = converter.convert_video_to_mp3(
            temp_video_path,
            output_filename=mp3_filename,
            bitrate=bitrate
        )
        
        # 2. Transcribir
        transcriber_instance = get_transcriber()
        trans_result = transcriber_instance.transcribe_with_timestamps(
            mp3_path,
            language=language
        )
        
        # 3. Diarizar
        diarizer_instance = get_diarizer()
        dia_segments = diarizer_instance.diarize(
            mp3_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # 4. Combinar
        aligned_segments = align_transcription_with_diarization(
            trans_result,
            dia_segments
        )
        
        # 5. Formatear
        formatted_text = format_transcript(aligned_segments, output_format)
        
        # 6. Estadísticas
        statistics = get_speaker_statistics(aligned_segments)
        
        return {
            "job_id": job_id,
            "text": formatted_text,
            "segments": aligned_segments,
            "statistics": statistics,
            "num_speakers": len(statistics),
            "output_format": output_format,
            "source": "video_conversion"
        }
        
    except Exception as e:
        logger.error(f"Error al procesar video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
         archivos temporales
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Archivo temporal de video eliminado: {temp_video_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar video temporal: {e}")
        
        if mp3_path and os.path.exists(mp3_path):
            try:
                os.remove(mp3_path)
                logger.info(f"Archivo temporal MP3 eliminado: {mp3_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar MP3 temporal: {e}")


@app.get("/models", tags=["General"])
async def get_models_info():
    """Información sobre los modelos disponibles"""
    return {
        "whisper_models": ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        "current_whisper_model": WHISPER_MODEL,
        "diarization_model": "pyannote/speaker-diarization-3.1",
        "supported_languages": [
            "es", "en", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"
        ],
        "supported_video_formats": [
            "mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v", "mpg", "mpeg", "3gp", "ogv"
        ]
    }


# Manejo de errores
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8888))
    host = os.getenv("HOST", "127.0.0.1")
    
    print("=" * 60)
    print("🎤 API de Transcripción de Audio con Diarización")
    print("=" * 60)
    print(f"📡 Servidor: http://{host}:{port}")
    print(f"📚 Documentación: http://{host}:{port}/docs")
    print(f"🌐 Interfaz Web: http://{host}:{port}")
    print(f"🤖 Modelo Whisper: {WHISPER_MODEL}")
    print(f"🔑 HF Token: {'✅ Configurado' if HF_TOKEN else '❌ No configurado'}")
    print("=" * 60)
    print("Presiona Ctrl+C para detener el servidor\n")
    
    uvicorn.run(
        app,  # Pasar la app directamente (más rápido, sin reload)
        host=host, 
        port=port,
        log_level="info"
    )
