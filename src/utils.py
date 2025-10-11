"""
Utilidades para combinar transcripción con diarización
"""
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def renumber_speakers(diarization_segments: List[Dict]) -> List[Dict]:
    """
    Renumera los hablantes para que comiencen desde SPEAKER_01 en lugar de SPEAKER_00.
    
    Args:
        diarization_segments: Lista de segmentos con nombres de hablantes originales
    
    Returns:
        Lista de segmentos con hablantes renumerados (SPEAKER_01, SPEAKER_02, etc.)
    """
    # Obtener todos los hablantes únicos en orden de aparición
    unique_speakers = []
    for seg in diarization_segments:
        speaker = seg["speaker"]
        if speaker not in unique_speakers:
            unique_speakers.append(speaker)
    
    # Crear mapeo de nombres antiguos a nuevos (comenzando desde 01)
    speaker_mapping = {}
    for idx, old_speaker in enumerate(unique_speakers, start=1):
        speaker_mapping[old_speaker] = f"SPEAKER_{idx:02d}"
    
    # Aplicar el mapeo a todos los segmentos
    renumbered_segments = []
    for seg in diarization_segments:
        new_seg = seg.copy()
        new_seg["speaker"] = speaker_mapping[seg["speaker"]]
        renumbered_segments.append(new_seg)
    
    logger.info(f"Hablantes renumerados: {speaker_mapping}")
    return renumbered_segments


def align_transcription_with_diarization(
    transcription_segments: List[Dict],
    diarization_segments: List[Dict]
) -> List[Dict]:
    """
    Combina segmentos de transcripción con información de hablantes.
    
    Args:
        transcription_segments: Lista de segmentos de Whisper con timestamps
        diarization_segments: Lista de segmentos de pyannote con hablantes
    
    Returns:
        Lista de segmentos combinados con texto y hablante
    """
    # Renombrar hablantes para que comiencen desde SPEAKER_01
    diarization_segments = renumber_speakers(diarization_segments)
    
    aligned_segments = []
    
    for trans_seg in transcription_segments:
        trans_start = trans_seg["start"]
        trans_end = trans_seg["end"]
        trans_text = trans_seg["text"]
        
        # Encontrar el hablante con mayor overlap
        speaker = find_speaker_for_segment(
            trans_start, 
            trans_end, 
            diarization_segments
        )
        
        aligned_segments.append({
            "start": trans_start,
            "end": trans_end,
            "text": trans_text,
            "speaker": speaker,
            "duration": trans_end - trans_start
        })
    
    return aligned_segments


def find_speaker_for_segment(
    start: float, 
    end: float, 
    diarization_segments: List[Dict]
) -> str:
    """
    Encuentra el hablante con mayor overlap temporal con el segmento dado.
    
    Args:
        start: Tiempo de inicio del segmento
        end: Tiempo de fin del segmento
        diarization_segments: Segmentos de diarización
    
    Returns:
        Identificador del hablante
    """
    max_overlap = 0
    speaker = "UNKNOWN"
    
    for dia_seg in diarization_segments:
        overlap = calculate_overlap(
            start, end,
            dia_seg["start"], dia_seg["end"]
        )
        
        if overlap > max_overlap:
            max_overlap = overlap
            speaker = dia_seg["speaker"]
    
    return speaker


def calculate_overlap(start1: float, end1: float, start2: float, end2: float) -> float:
    """
    Calcula el tiempo de solapamiento entre dos intervalos.
    
    Args:
        start1, end1: Primer intervalo
        start2, end2: Segundo intervalo
    
    Returns:
        Duración del solapamiento en segundos
    """
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    return max(0, overlap_end - overlap_start)


def format_transcript(aligned_segments: List[Dict], format_type: str = "text") -> str:
    """
    Formatea la transcripción alineada en diferentes formatos.
    
    Args:
        aligned_segments: Segmentos con transcripción y hablante
        format_type: Tipo de formato ('text', 'srt', 'json', 'detailed')
    
    Returns:
        Transcripción formateada
    """
    if format_type == "text":
        return format_as_text(aligned_segments)
    elif format_type == "srt":
        return format_as_srt(aligned_segments)
    elif format_type == "detailed":
        return format_as_detailed(aligned_segments)
    else:
        raise ValueError(f"Formato no soportado: {format_type}")


def format_as_text(segments: List[Dict]) -> str:
    """
    Formato simple de texto con hablantes.
    
    Ejemplo:
    [SPEAKER_00]: Hola, ¿cómo estás?
    [SPEAKER_01]: Muy bien, gracias.
    """
    lines = []
    current_speaker = None
    current_text = []
    
    for seg in segments:
        speaker = seg["speaker"]
        text = seg["text"].strip()
        
        if speaker != current_speaker:
            if current_text:
                lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
            current_speaker = speaker
            current_text = [text]
        else:
            current_text.append(text)
    
    # Agregar el último segmento
    if current_text:
        lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
    
    return "\n\n".join(lines)


def format_as_detailed(segments: List[Dict]) -> str:
    """
    Formato detallado con timestamps y hablantes.
    
    Ejemplo:
    [00:00:05 - 00:00:10] SPEAKER_00: Hola, ¿cómo estás?
    [00:00:10 - 00:00:15] SPEAKER_01: Muy bien, gracias.
    """
    lines = []
    
    for seg in segments:
        start_time = format_timestamp(seg["start"])
        end_time = format_timestamp(seg["end"])
        speaker = seg["speaker"]
        text = seg["text"].strip()
        
        lines.append(f"[{start_time} - {end_time}] {speaker}: {text}")
    
    return "\n".join(lines)


def format_as_srt(segments: List[Dict]) -> str:
    """
    Formato SRT (SubRip) para subtítulos.
    
    Ejemplo:
    1
    00:00:05,000 --> 00:00:10,000
    [SPEAKER_00]: Hola, ¿cómo estás?
    """
    srt_lines = []
    
    for i, seg in enumerate(segments, 1):
        start_time = format_srt_timestamp(seg["start"])
        end_time = format_srt_timestamp(seg["end"])
        speaker = seg["speaker"]
        text = seg["text"].strip()
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(f"[{speaker}]: {text}")
        srt_lines.append("")  # Línea en blanco
    
    return "\n".join(srt_lines)


def format_timestamp(seconds: float) -> str:
    """
    Convierte segundos a formato HH:MM:SS.
    
    Args:
        seconds: Tiempo en segundos
    
    Returns:
        Timestamp formateado
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_srt_timestamp(seconds: float) -> str:
    """
    Convierte segundos a formato SRT (HH:MM:SS,mmm).
    
    Args:
        seconds: Tiempo en segundos
    
    Returns:
        Timestamp SRT formateado
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def get_speaker_statistics(aligned_segments: List[Dict]) -> Dict:
    """
    Calcula estadísticas de participación por hablante.
    
    Args:
        aligned_segments: Segmentos alineados
    
    Returns:
        Estadísticas por hablante
    """
    stats = {}
    
    for seg in aligned_segments:
        speaker = seg["speaker"]
        duration = seg["duration"]
        word_count = len(seg["text"].split())
        
        if speaker not in stats:
            stats[speaker] = {
                "total_time": 0.0,
                "total_words": 0,
                "segment_count": 0
            }
        
        stats[speaker]["total_time"] += duration
        stats[speaker]["total_words"] += word_count
        stats[speaker]["segment_count"] += 1
    
    # Calcular porcentajes
    total_time = sum(s["total_time"] for s in stats.values())
    total_words = sum(s["total_words"] for s in stats.values())
    
    for speaker in stats:
        stats[speaker]["time_percentage"] = (
            stats[speaker]["total_time"] / total_time * 100 
            if total_time > 0 else 0
        )
        stats[speaker]["word_percentage"] = (
            stats[speaker]["total_words"] / total_words * 100 
            if total_words > 0 else 0
        )
    
    return stats


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de segmentos
    trans_segments = [
        {"start": 0.0, "end": 5.0, "text": "Hola, ¿cómo estás?"},
        {"start": 5.0, "end": 10.0, "text": "Muy bien, gracias."}
    ]
    
    dia_segments = [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
        {"start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"}
    ]
    
    aligned = align_transcription_with_diarization(trans_segments, dia_segments)
    print(format_as_text(aligned))
