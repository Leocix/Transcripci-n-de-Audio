import osimport os

import whisperimport whisper

import torchimport torch

from typing import Dict, Optionalfrom typing import Dict, Optional

import loggingimport logging



logging.basicConfig(level=logging.INFO)logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)logger = logging.getLogger(__name__)





class AudioTranscriber:class AudioTranscriber:

        

    def __init__(self, model_name: str = "base"):    def __init__(self, model_name: str = "base"):

        self.model_name = model_name        self.model_name = model_name

        self.device = "cuda" if torch.cuda.is_available() else "cpu"        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Inicializando Whisper modelo '{model_name}' en dispositivo '{self.device}'")        logger.info(f"Inicializando Whisper modelo '{model_name}' en dispositivo '{self.device}'")

                

        try:        try:

            self.model = whisper.load_model(model_name, device=self.device)            self.model = whisper.load_model(model_name, device=self.device)

            logger.info(f"Modelo Whisper '{model_name}' cargado exitosamente")            logger.info(f"Modelo Whisper '{model_name}' cargado exitosamente")

        except Exception as e:        except Exception as e:

            logger.error(f"Error al cargar modelo Whisper: {e}")            logger.error(f"Error al cargar modelo Whisper: {e}")

            raise            raise

        

    def transcribe(    def transcribe(

        self,         self, 

        audio_path: str,         audio_path: str, 

        language: Optional[str] = None,        language: Optional[str] = None,

        task: str = "transcribe",        task: str = "transcribe",

        **kwargs        **kwargs

    ) -> Dict:    ) -> Dict:

        if not os.path.exists(audio_path):            **kwargs: Argumentos adicionales para whisper.transcribe()

            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")        

                Returns:

        logger.info(f"Iniciando transcripción de: {audio_path}")            Dict con la transcripción y metadatos

                """

        try:        if not os.path.exists(audio_path):

            options = {            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

                "task": task,        

                "verbose": False,        logger.info(f"Iniciando transcripción de: {audio_path}")

                **kwargs        

            }        try:

                        # Opciones de transcripción

            if language:            options = {

                options["language"] = language                "task": task,

                            "verbose": False,

            result = self.model.transcribe(audio_path, **options)                **kwargs

                        }

            logger.info(f"Transcripción completada. Texto: {len(result.get('text', ''))} caracteres")            

                        if language:

            return {                options["language"] = language

                "text": result.get("text", ""),            

                "segments": result.get("segments", []),            # Realizar transcripción

                "language": result.get("language", "unknown"),            result = self.model.transcribe(audio_path, **options)

                "model": self.model_name,            

                "device": self.device            logger.info(f"Transcripción completada. Texto: {len(result.get('text', ''))} caracteres")

            }            

                        return {

        except Exception as e:                "text": result.get("text", ""),

            logger.error(f"Error durante la transcripción: {e}")                "segments": result.get("segments", []),

            raise                "language": result.get("language", "unknown"),

                    "model": self.model_name,

    def transcribe_with_timestamps(self, audio_path: str, **kwargs) -> list:                "device": self.device

        result = self.transcribe(audio_path, **kwargs)            }

                    

        segments = []        except Exception as e:

        for seg in result.get("segments", []):            logger.error(f"Error durante la transcripción: {e}")

            segments.append({            raise

                "start": seg["start"],    

                "end": seg["end"],    def transcribe_with_timestamps(self, audio_path: str, **kwargs) -> list:

                "text": seg["text"].strip(),        """

                "confidence": seg.get("no_speech_prob", 0.0)        Transcribe audio y retorna segmentos con timestamps precisos.

            })        

                Args:

        return segments            audio_path: Ruta al archivo de audio

            **kwargs: Argumentos adicionales

        

def get_available_models() -> list:        Returns:

    return ["tiny", "base", "small", "medium", "large"]            Lista de segmentos con timestamps

        """

        result = self.transcribe(audio_path, **kwargs)

def estimate_model_memory(model_name: str) -> str:        

    memory_estimates = {        segments = []

        "tiny": "~1 GB",        for seg in result.get("segments", []):

        "base": "~1 GB",            segments.append({

        "small": "~2 GB",                "start": seg["start"],

        "medium": "~5 GB",                "end": seg["end"],

        "large": "~10 GB"                "text": seg["text"].strip(),

    }                "confidence": seg.get("no_speech_prob", 0.0)

    return memory_estimates.get(model_name, "Desconocido")            })

        
        return segments


def get_available_models() -> list:
    """
    Retorna la lista de modelos Whisper disponibles.
    
    Returns:
        Lista de nombres de modelos
    """
    return ["tiny", "base", "small", "medium", "large"]


def estimate_model_memory(model_name: str) -> str:
    """
    Estima el uso de memoria para un modelo.
    
    Args:
        model_name: Nombre del modelo
    
    Returns:
        Estimación de memoria en formato legible
    """
    memory_estimates = {
        "tiny": "~1 GB",
        "base": "~1 GB",
        "small": "~2 GB",
        "medium": "~5 GB",
        "large": "~10 GB"
    }
    return memory_estimates.get(model_name, "Desconocido")


# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar transcriptor
    transcriber = AudioTranscriber(model_name="base")
    
    # Transcribir un archivo de ejemplo
    # result = transcriber.transcribe("example.wav", language="es")
    # print(result["text"])
