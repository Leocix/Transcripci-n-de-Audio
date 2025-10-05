"""
Script para descargar modelos de Hugging Face manualmente
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Desactivar symlinks de Hugging Face (problema en Windows)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("❌ ERROR: HF_TOKEN no encontrado en .env")
    exit(1)

print(f"✅ HF_TOKEN encontrado: {HF_TOKEN[:10]}...")
print("\n📥 Descargando modelos de pyannote.audio...")
print("Esto puede tardar varios minutos...\n")

from huggingface_hub import snapshot_download

try:
    # Descargar modelo de diarización
    print("1️⃣ Descargando pyannote/speaker-diarization-3.1...")
    snapshot_download(
        repo_id="pyannote/speaker-diarization-3.1",
        token=HF_TOKEN,
        local_files_only=False
    )
    print("✅ speaker-diarization-3.1 descargado\n")
    
    # Descargar modelos dependientes
    print("2️⃣ Descargando pyannote/segmentation-3.0...")
    snapshot_download(
        repo_id="pyannote/segmentation-3.0",
        token=HF_TOKEN,
        local_files_only=False
    )
    print("✅ segmentation-3.0 descargado\n")
    
    print("3️⃣ Descargando pyannote/speaker-diarization-3.0...")
    snapshot_download(
        repo_id="pyannote/speaker-diarization-3.0",
        token=HF_TOKEN,
        local_files_only=False
    )
    print("✅ speaker-diarization-3.0 descargado\n")
    
    print("4️⃣ Descargando speechbrain/spkrec-ecapa-voxceleb...")
    snapshot_download(
        repo_id="speechbrain/spkrec-ecapa-voxceleb",
        token=HF_TOKEN,
        local_files_only=False
    )
    print("✅ spkrec-ecapa-voxceleb descargado\n")
    
    print("\n🎉 ¡Todos los modelos descargados exitosamente!")
    print("Ahora puedes ejecutar el servidor sin conexión a Internet.")
    
except Exception as e:
    print(f"\n❌ Error al descargar modelos: {e}")
    print("\nAsegúrate de:")
    print("1. Tener acceso a Internet")
    print("2. Haber aceptado los términos en:")
    print("   - https://hf.co/pyannote/speaker-diarization-3.1")
    print("   - https://hf.co/pyannote/segmentation-3.0")
    print("3. Tu HF_TOKEN sea válido")
