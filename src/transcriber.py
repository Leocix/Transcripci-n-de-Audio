import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioTranscriber:
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        # Importar torch y whisper de forma perezosa para evitar carga innecesaria
        try:
            import importlib
            torch = importlib.import_module('torch')
            whisper = importlib.import_module('whisper')
        except Exception as e:
            logger.error(f"No se pudieron importar torch/whisper: {e}")
            raise

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Inicializando Whisper modelo '{model_name}' en dispositivo '{self.device}'")
        try:
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info(f"Modelo Whisper '{model_name}' cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo Whisper: {e}")
            raise
    
    def transcribe(self, audio_path: str, language: Optional[str] = None, task: str = "transcribe", **kwargs) -> Dict:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")
        
        logger.info(f"Iniciando transcripción de: {audio_path}")
        
        try:
            options = {"task": task, "verbose": False, **kwargs}
            if language:
                options["language"] = language
            
            result = self.model.transcribe(audio_path, **options)
            logger.info(f"Transcripción completada. Texto: {len(result.get('text', ''))} caracteres")
            
            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown"),
                "model": self.model_name,
                "device": self.device
            }
        except Exception as e:
            logger.error(f"Error durante la transcripción: {e}")
            raise
    
    def transcribe_with_timestamps(self, audio_path: str, **kwargs) -> list:
        result = self.transcribe(audio_path, **kwargs)
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "confidence": seg.get("no_speech_prob", 0.0)
            })
        return segments


def get_available_models() -> list:
    return ["tiny", "base", "small", "medium", "large"]


def estimate_model_memory(model_name: str) -> str:
    memory_estimates = {
        "tiny": "~1 GB",
        "base": "~1 GB",
        "small": "~2 GB",
        "medium": "~5 GB",
        "large": "~10 GB"
    }
    return memory_estimates.get(model_name, "Desconocido")
