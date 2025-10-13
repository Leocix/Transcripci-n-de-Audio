"""
Módulo de diarización de hablantes usando pyannote.audio
"""
import os
from typing import List, Dict, Optional
import logging

# Import heavy libs lazily inside the class to avoid import-time overhead
try:
    import torch
except Exception:
    torch = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeakerDiarizer:
    """
    Clase para realizar diarización de hablantes (identificar quién habla cuándo).
    Usa pyannote.audio para segmentar audio por hablante.
    """
    
    def __init__(self, hf_token: Optional[str] = None):
        """
        Inicializa el diarizador.
        
        Args:
            hf_token: Token de Hugging Face para acceder al modelo
                     Obtener en: https://huggingface.co/settings/tokens
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        if not self.hf_token:
            raise ValueError(
                "Se requiere un token de Hugging Face. "
                "Configúralo en HF_TOKEN o pásalo como argumento.\n"
                "Obtén uno en: https://huggingface.co/settings/tokens"
            )
        
        # Determinar dispositivo si torch está disponible
        if torch is None:
            try:
                import importlib
                torch = importlib.import_module('torch')
            except Exception:
                torch = None

        self.device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
        logger.info(f"Inicializando diarizador en dispositivo '{self.device}'")

        # Desactivar symlinks en Windows
        os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

        # Cargar librerías pesadas de forma perezosa
        try:
            import importlib
            Pipeline = importlib.import_module('pyannote.audio').Pipeline
            librosa = importlib.import_module('librosa')
        except Exception as e:
            logger.error(f"No se pudieron importar pyannote.audio o librosa: {e}")
            raise

        try:
            # Cargar pipeline de diarización
            logger.info("Descargando/cargando modelo de diarización...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.hf_token
            )

            # Mover a GPU si está disponible
            if self.device == "cuda":
                self.pipeline = self.pipeline.to(torch.device("cuda"))

            logger.info("Pipeline de diarización cargado exitosamente")

        except Exception as e:
            logger.error(f"Error al cargar pipeline de diarización: {e}", exc_info=True)
            if "401" in str(e) or "403" in str(e):
                logger.error(
                    "Error de autenticación. Verifica:\n"
                    "1. Tu HF_TOKEN en el archivo .env\n"
                    "2. Que aceptaste los términos en:\n"
                    "   - https://huggingface.co/pyannote/speaker-diarization-3.1\n"
                    "   - https://huggingface.co/pyannote/segmentation-3.0"
                )
            elif "Failed to resolve" in str(e) or "getaddrinfo failed" in str(e):
                logger.error(
                    "Error de conexión a Internet. Verifica:\n"
                    "1. Que tienes conexión a Internet\n"
                    "2. Que Python puede acceder a la red (firewall/proxy)\n"
                    "3. Intenta descargar los modelos manualmente con:\n"
                    "   - Ejecuta PowerShell como Administrador\n"
                    "   - cd 'D:\\Transcripción de Audio'\n"
                    "   - .\\DESCARGAR_MODELOS.bat"
                )
            raise
    
    def diarize(
        self, 
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> List[Dict]:
        """
        Realiza diarización del audio.
        
        Args:
            audio_path: Ruta al archivo de audio
            num_speakers: Número exacto de hablantes (opcional)
            min_speakers: Número mínimo de hablantes (opcional)
            max_speakers: Número máximo de hablantes (opcional)
        
        Returns:
            Lista de segmentos con información de hablante
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")
        
        logger.info(f"Iniciando diarización de: {audio_path}")
        
        try:
            # Configurar parámetros
            params = {}
            if num_speakers:
                params["num_speakers"] = num_speakers
            if min_speakers:
                params["min_speakers"] = min_speakers
            if max_speakers:
                params["max_speakers"] = max_speakers
            
            # Pre-cargar el audio usando librosa (soporta más formatos vía FFmpeg)
            # Esto evita el error de AudioDecoder y soporta webm, mp3, wav, etc.
            logger.info("Cargando audio con librosa...")
            
            # librosa.load devuelve (waveform, sample_rate)
            # waveform es mono por defecto, necesitamos convertir a stereo si es necesario
            waveform, sample_rate = librosa.load(audio_path, sr=None, mono=False)
            
            # Convertir a tensor de PyTorch
            waveform = torch.from_numpy(waveform).float()
            
            # Ajustar dimensiones según lo que devuelva librosa
            # Si es mono: (samples,) -> (1, samples)
            # Si es stereo: (2, samples) -> ya está bien
            if waveform.ndim == 1:
                waveform = waveform.unsqueeze(0)
            
            logger.info(f"Audio cargado: shape={waveform.shape}, sample_rate={sample_rate}")
            
            # Crear diccionario de audio para pyannote
            audio_dict = {
                "waveform": waveform,
                "sample_rate": sample_rate
            }
            
            # Ejecutar diarización con audio pre-cargado
            logger.info("Ejecutando pipeline de diarización...")
            diarization_output = self.pipeline(audio_dict, **params)
            
            # En pyannote.audio 3.x, la pipeline devuelve un DiarizeOutput
            # que contiene un Annotation en .speaker_diarization
            if hasattr(diarization_output, 'speaker_diarization'):
                # Nuevo formato (pyannote.audio 3.x)
                diarization = diarization_output.speaker_diarization
            else:
                # Formato antiguo o directo
                diarization = diarization_output
            
            # Convertir a formato estructurado usando itertracks
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                    "duration": turn.end - turn.start
                })
            
            # Obtener número de hablantes únicos
            unique_speakers = len(set(seg["speaker"] for seg in segments))
            logger.info(f"Diarización completada. Hablantes detectados: {unique_speakers}")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error durante la diarización: {e}")
            raise
    
    def get_speaker_segments(self, audio_path: str, **kwargs) -> Dict[str, List[Dict]]:
        """
        Organiza los segmentos por hablante.
        
        Args:
            audio_path: Ruta al archivo de audio
            **kwargs: Argumentos para diarize()
        
        Returns:
            Diccionario con segmentos agrupados por hablante
        """
        segments = self.diarize(audio_path, **kwargs)
        
        speaker_segments = {}
        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append({
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["duration"]
            })
        
        return speaker_segments
    
    def get_speaker_stats(self, audio_path: str, **kwargs) -> Dict:
        """
        Calcula estadísticas de participación por hablante.
        
        Args:
            audio_path: Ruta al archivo de audio
            **kwargs: Argumentos para diarize()
        
        Returns:
            Estadísticas por hablante
        """
        segments = self.diarize(audio_path, **kwargs)
        
        stats = {}
        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in stats:
                stats[speaker] = {
                    "total_time": 0.0,
                    "num_segments": 0,
                    "segments": []
                }
            
            stats[speaker]["total_time"] += seg["duration"]
            stats[speaker]["num_segments"] += 1
            stats[speaker]["segments"].append({
                "start": seg["start"],
                "end": seg["end"]
            })
        
        # Calcular porcentajes
        total_speaking_time = sum(s["total_time"] for s in stats.values())
        for speaker in stats:
            stats[speaker]["percentage"] = (
                stats[speaker]["total_time"] / total_speaking_time * 100
                if total_speaking_time > 0 else 0
            )
        
        return stats


# Ejemplo de uso
if __name__ == "__main__":
    # Requiere token de Hugging Face
    # diarizer = SpeakerDiarizer(hf_token="tu_token_aqui")
    # segments = diarizer.diarize("example.wav", min_speakers=2, max_speakers=5)
    # print(segments)
    pass
