"""
Módulo para convertir videos a audio MP3
"""
import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoConverter:
    """
    Clase para convertir archivos de video a audio MP3.
    Usa FFmpeg para la conversión.
    Soporta videos largos dividiéndolos en segmentos.
    """
    
    def __init__(self, output_dir: str = "./uploads", chunk_duration: int = 600):
        """
        Inicializa el convertidor de video.
        
        Args:
            output_dir: Directorio donde guardar archivos convertidos
            chunk_duration: Duración en segundos de cada segmento para videos largos (default: 10 min)
        """
        self.output_dir = output_dir
        self.chunk_duration = chunk_duration  # Duración máxima por segmento
        os.makedirs(output_dir, exist_ok=True)
        
        # Verificar que FFmpeg esté instalado
        if not self.check_ffmpeg():
            logger.warning("FFmpeg no está instalado o no está en el PATH")
    
    def check_ffmpeg(self) -> bool:
        """
        Verifica si FFmpeg está instalado.
        
        Returns:
            True si FFmpeg está disponible, False si no
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def convert_video_to_mp3(
        self,
        video_path: str,
        output_filename: str = None,
        bitrate: str = "192k",
        sample_rate: int = 44100,
        max_duration: int = None
    ) -> str:
        """
        Convierte un archivo de video a MP3.
        Para videos largos (>10 min), considera usar convert_long_video_to_mp3()
        
        Args:
            video_path: Ruta al archivo de video
            output_filename: Nombre del archivo de salida (opcional)
            bitrate: Bitrate del audio (ej: "128k", "192k", "320k")
            sample_rate: Frecuencia de muestreo (ej: 44100, 48000)
            max_duration: Duración máxima en segundos (None = sin límite)
        
        Returns:
            Ruta al archivo MP3 generado
        
        Raises:
            FileNotFoundError: Si el video no existe
            RuntimeError: Si FFmpeg falla
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
        if not self.check_ffmpeg():
            raise RuntimeError(
                "FFmpeg no está instalado. Instálalo desde: https://ffmpeg.org/download.html"
            )
        
        # Verificar duración del video
        video_info = self.get_video_info(video_path)
        duration = video_info.get('duration', 0)
        
        # Advertencia para videos muy largos
        if duration > 1800:  # 30 minutos
            logger.warning(f"Video largo detectado ({duration/60:.1f} minutos). Considera usar procesamiento por chunks.")
        
        # Generar nombre de salida si no se proporciona
        if output_filename is None:
            video_name = Path(video_path).stem
            output_filename = f"{video_name}.mp3"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        logger.info(f"Convirtiendo video a MP3: {video_path} -> {output_path}")
        
        try:
            # Comando FFmpeg para extraer audio
            command = [
                'ffmpeg',
                '-i', video_path,           # Input file
                '-vn',                       # Sin video
                '-acodec', 'libmp3lame',    # Codec MP3
                '-b:a', bitrate,            # Bitrate
                '-ar', str(sample_rate),    # Sample rate
            ]
            
            # Limitar duración si se especifica
            if max_duration:
                command.extend(['-t', str(max_duration)])
            
            command.extend(['-y', output_path])  # Sobrescribir y output
            
            # Calcular timeout dinámico basado en duración
            timeout = max(300, int(duration * 2) if duration > 0 else 600)
            
            # Ejecutar FFmpeg
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"Error al convertir video: {error_msg}")
            
            logger.info(f"Conversión exitosa: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"La conversión tardó demasiado tiempo (>{timeout}s). Usa convert_long_video_to_mp3() para videos largos.")
        except Exception as e:
            logger.error(f"Error durante la conversión: {e}")
            raise
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Obtiene información del video usando FFprobe.
        
        Args:
            video_path: Ruta al archivo de video
        
        Returns:
            Diccionario con información del video
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
        try:
            command = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout.decode('utf-8'))
                
                # Extraer información relevante
                format_info = info.get('format', {})
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'format': format_info.get('format_name', 'unknown'),
                    'has_audio': audio_stream is not None,
                    'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                    'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else 0
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener información del video: {e}")
            return {}
    
    def convert_long_video_to_mp3(
        self,
        video_path: str,
        output_filename: str = None,
        bitrate: str = "192k",
        sample_rate: int = 44100,
        chunk_duration: int = None
    ) -> str:
        """
        Convierte videos largos a MP3 procesándolos en segmentos (chunks).
        Recomendado para videos >30 minutos.
        
        Args:
            video_path: Ruta al archivo de video
            output_filename: Nombre del archivo de salida
            bitrate: Bitrate del audio
            sample_rate: Frecuencia de muestreo
            chunk_duration: Duración de cada chunk en segundos (default: self.chunk_duration)
        
        Returns:
            Ruta al archivo MP3 final
        """
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
        
        video_info = self.get_video_info(video_path)
        total_duration = video_info.get('duration', 0)
        
        if total_duration == 0:
            logger.warning("No se pudo determinar la duración del video, usando método estándar")
            return self.convert_video_to_mp3(video_path, output_filename, bitrate, sample_rate)
        
        logger.info(f"Video largo detectado: {total_duration/60:.1f} minutos")
        logger.info(f"Procesando en chunks de {chunk_duration/60:.1f} minutos")
        
        # Generar nombre de salida
        if output_filename is None:
            video_name = Path(video_path).stem
            output_filename = f"{video_name}.mp3"
        
        output_path = os.path.join(self.output_dir, output_filename)
        temp_chunks = []
        
        try:
            # Dividir en chunks
            num_chunks = int(total_duration / chunk_duration) + 1
            
            for i in range(num_chunks):
                start_time = i * chunk_duration
                
                # No procesar más allá de la duración total
                if start_time >= total_duration:
                    break
                
                chunk_filename = f"chunk_{i}_{output_filename}"
                chunk_path = os.path.join(self.output_dir, chunk_filename)
                temp_chunks.append(chunk_path)
                
                logger.info(f"Procesando chunk {i+1}/{num_chunks} (desde {start_time}s)")
                
                command = [
                    'ffmpeg',
                    '-ss', str(start_time),      # Inicio
                    '-t', str(chunk_duration),   # Duración
                    '-i', video_path,
                    '-vn',
                    '-acodec', 'libmp3lame',
                    '-b:a', bitrate,
                    '-ar', str(sample_rate),
                    '-y',
                    chunk_path
                ]
                
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=chunk_duration * 2 + 60  # Timeout dinámico
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    raise RuntimeError(f"Error en chunk {i}: {error_msg}")
            
            # Concatenar chunks si hay más de uno
            if len(temp_chunks) > 1:
                logger.info(f"Concatenando {len(temp_chunks)} chunks...")
                self._concatenate_audio_files(temp_chunks, output_path)
            elif len(temp_chunks) == 1:
                # Solo un chunk, renombrar
                os.rename(temp_chunks[0], output_path)
            
            logger.info(f"Video largo convertido exitosamente: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error al procesar video largo: {e}")
            raise
        
        finally:
            # Limpiar chunks temporales
            for chunk in temp_chunks:
                if os.path.exists(chunk) and chunk != output_path:
                    try:
                        os.remove(chunk)
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar chunk temporal {chunk}: {e}")
    
    def _concatenate_audio_files(self, input_files: list, output_path: str):
        """
        Concatena múltiples archivos de audio en uno solo.
        
        Args:
            input_files: Lista de rutas a archivos de audio
            output_path: Ruta del archivo de salida
        """
        # Crear archivo de lista para FFmpeg
        list_file = os.path.join(self.output_dir, "concat_list.txt")
        
        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for file_path in input_files:
                    # FFmpeg necesita rutas con formato específico
                    escaped_path = file_path.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Concatenar usando FFmpeg
            command = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"Error al concatenar archivos: {error_msg}")
            
        finally:
            # Limpiar archivo de lista
            if os.path.exists(list_file):
                try:
                    os.remove(list_file)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo de lista: {e}")
    
    def convert_with_progress(
        self,
        video_path: str,
        output_filename: str = None,
        progress_callback=None
    ) -> str:
        """
        Convierte video a MP3 con callback de progreso.
        
        Args:
            video_path: Ruta al archivo de video
            output_filename: Nombre del archivo de salida
            progress_callback: Función para reportar progreso (recibe porcentaje)
        
        Returns:
            Ruta al archivo MP3 generado
        """
        # Obtener duración del video
        info = self.get_video_info(video_path)
        duration = info.get('duration', 0)
        
        if output_filename is None:
            video_name = Path(video_path).stem
            output_filename = f"{video_name}.mp3"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-ar', '44100',
            '-progress', 'pipe:1',  # Reportar progreso a stdout
            '-y',
            output_path
        ]
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Leer progreso
            for line in process.stdout:
                if line.startswith('out_time_ms='):
                    time_ms = int(line.split('=')[1])
                    time_sec = time_ms / 1000000
                    
                    if duration > 0 and progress_callback:
                        progress = min(100, (time_sec / duration) * 100)
                        progress_callback(progress)
            
            process.wait()
            
            if process.returncode != 0:
                raise RuntimeError("Error en la conversión")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error durante la conversión: {e}")
            raise


def get_supported_video_formats() -> list:
    """
    Retorna la lista de formatos de video soportados.
    
    Returns:
        Lista de extensiones de video soportadas
    """
    return [
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm',
        'm4v', 'mpg', 'mpeg', '3gp', 'ogv'
    ]


def is_video_file(filename: str) -> bool:
    """
    Verifica si un archivo es un video soportado.
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        True si es un video soportado, False si no
    """
    extension = Path(filename).suffix.lower().lstrip('.')
    return extension in get_supported_video_formats()


# Ejemplo de uso
if __name__ == "__main__":
    converter = VideoConverter()
    
    # Verificar FFmpeg
    if converter.check_ffmpeg():
        print("✅ FFmpeg está instalado")
    else:
        print("❌ FFmpeg NO está instalado")
    
    # Ejemplo de conversión
    # video_file = "ejemplo.mp4"
    # if os.path.exists(video_file):
    #     mp3_file = converter.convert_video_to_mp3(video_file)
    #     print(f"Audio extraído: {mp3_file}")
