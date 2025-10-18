#!/usr/bin/env python3
"""
Script para verificar que todas las configuraciones estén correctas
"""
import sys
from pathlib import Path

def check_configuration():
    """Verifica la configuración del proyecto"""
    issues = []
    warnings = []
    
    print("🔍 Verificando configuración del proyecto...\n")
    print("=" * 60)
    
    # 1. Verificar Python
    print(f"\n✓ Python {sys.version}")
    
    # 2. Verificar directorio src
    src_dir = Path("src")
    if src_dir.exists():
        print(f"✓ Directorio src/ encontrado")
    else:
        issues.append("❌ Directorio src/ NO encontrado")
    
    # 3. Verificar archivos principales
    required_files = [
        "main.py",
        "src/transcriber.py",
        "src/diarizer.py",
        "src/video_converter.py",
        "src/utils.py"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            issues.append(f"❌ {file} NO encontrado")
    
    # 4. Verificar archivo .env
    env_file = Path("config/.env")
    if env_file.exists():
        print(f"✓ config/.env encontrado")
        
        # Leer y verificar variables importantes
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'HF_TOKEN=' in content and 'hf_' in content:
                print(f"✓ HF_TOKEN configurado")
            else:
                warnings.append("⚠️  HF_TOKEN no configurado o inválido")
            
            if 'WHISPER_MODEL=' in content:
                print(f"✓ WHISPER_MODEL configurado")
            else:
                warnings.append("⚠️  WHISPER_MODEL no configurado")
    else:
        issues.append("❌ config/.env NO encontrado")
        print("   Copia config/.env.example a config/.env")
    
    # 5. Verificar FFmpeg
    print("\n🎬 Verificando FFmpeg...")
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ FFmpeg instalado y disponible")
        else:
            warnings.append("⚠️  FFmpeg encontrado pero hay problemas")
    except FileNotFoundError:
        warnings.append("⚠️  FFmpeg NO instalado o no está en el PATH")
        print("   Instala FFmpeg: https://ffmpeg.org/download.html")
    except Exception as e:
        warnings.append(f"⚠️  Error al verificar FFmpeg: {e}")
    
    # 6. Verificar dependencias
    print("\n📦 Verificando dependencias...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'whisper',
        'pyannote.audio',
        'torch'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('.', '_'))
            print(f"✓ {package}")
        except ImportError:
            issues.append(f"❌ {package} NO instalado")
    
    # 7. Verificar directorio uploads
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        print(f"\n✓ Directorio uploads/ existe")
    else:
        warnings.append("⚠️  Directorio uploads/ no existe, se creará automáticamente")
    
    # 8. Verificar caché de Python
    print("\n🐍 Verificando caché de Python...")
    pycache_dirs = list(Path("src").rglob("__pycache__"))
    if pycache_dirs:
        warnings.append(f"⚠️  Encontradas {len(pycache_dirs)} carpetas __pycache__ (se recomienda limpiar)")
    else:
        print("✓ No se encontró caché de Python")
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    if not issues and not warnings:
        print("\n✅ ¡Todo está configurado correctamente!")
        print("\nPuedes iniciar el servidor con:")
        print("   python src/main.py")
        return True
    else:
        if issues:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(issues)}):")
            for issue in issues:
                print(f"   {issue}")
        
        if warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
            for warning in warnings:
                print(f"   {warning}")
        
        print("\n🔧 Soluciones sugeridas:")
        if any("HF_TOKEN" in w for w in warnings):
            print("   1. Configura HF_TOKEN en config/.env")
            print("      Obtén tu token en: https://huggingface.co/settings/tokens")
        
        if any("FFmpeg" in w for w in warnings):
            print("   2. Instala FFmpeg:")
            print("      choco install ffmpeg")
        
        if any("__pycache__" in w for w in warnings):
            print("   3. Limpia el caché de Python:")
            print("      .\\cleanup.ps1")
        
        if issues:
            print("\n❌ Corrige los problemas críticos antes de continuar")
            return False
        else:
            print("\n⚠️  Puedes continuar, pero se recomienda corregir las advertencias")
            return True

if __name__ == "__main__":
    success = check_configuration()
    sys.exit(0 if success else 1)
