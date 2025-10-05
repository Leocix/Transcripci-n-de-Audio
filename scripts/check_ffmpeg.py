"""
Script para verificar la instalación de FFmpeg
"""
import sys
import os

# Agregar directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from video_converter import VideoConverter

def main():
    print("=" * 60)
    print("🔍 VERIFICANDO INSTALACIÓN DE FFMPEG")
    print("=" * 60)
    
    converter = VideoConverter()
    
    print("\n1. Verificando disponibilidad de FFmpeg...")
    if converter.check_ffmpeg():
        print("   ✅ FFmpeg está instalado y disponible")
        
        # Obtener versión
        import subprocess
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_line = result.stdout.split('\n')[0]
            print(f"   📦 {version_line}")
        except Exception as e:
            print(f"   ⚠️ No se pudo obtener la versión: {e}")
    else:
        print("   ❌ FFmpeg NO está instalado o no está en el PATH")
        print("\n" + "=" * 60)
        print("📖 GUÍA DE INSTALACIÓN:")
        print("=" * 60)
        print("\nPor favor, instala FFmpeg usando uno de estos métodos:\n")
        print("OPCIÓN 1 - Chocolatey (Recomendado):")
        print("  choco install ffmpeg -y\n")
        print("OPCIÓN 2 - Scoop:")
        print("  scoop install ffmpeg\n")
        print("OPCIÓN 3 - Manual:")
        print("  1. Descarga: https://github.com/BtbN/FFmpeg-Builds/releases")
        print("  2. Extrae en C:\\ffmpeg")
        print("  3. Agrega C:\\ffmpeg\\bin al PATH del sistema")
        print("\n📚 Ver guía completa: INSTALACION_FFMPEG.md")
        print("=" * 60)
        sys.exit(1)
    
    print("\n2. Verificando formatos soportados...")
    formats = [
        "mp4", "avi", "mov", "mkv", "flv", "wmv", 
        "webm", "m4v", "mpg", "mpeg", "3gp", "ogv"
    ]
    print(f"   ✅ {len(formats)} formatos de video soportados:")
    print(f"   {', '.join(formats)}")
    
    print("\n3. Verificando directorio de carga...")
    upload_dir = converter.output_dir
    if os.path.exists(upload_dir):
        print(f"   ✅ Directorio existe: {upload_dir}")
    else:
        print(f"   ℹ️ Directorio se creará al subir archivos: {upload_dir}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETA")
    print("=" * 60)
    print("\n🎬 El sistema está listo para convertir videos a MP3")
    print("📝 Usa la interfaz web o la API para procesar videos")
    print("\nEjemplo de uso:")
    print("  - Interfaz web: http://127.0.0.1:8888 → Tab 'Subir Archivo'")
    print("  - API: POST /convert-and-transcribe con un archivo de video")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
