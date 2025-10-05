# Transcripción de Audio# 🎤 Transcripción de Audio con Diarización



Sistema de transcripción de audio y video con identificación de hablantes.Sistema de transcripción de audio y video con identificación automática de hablantes usando **Whisper** y **pyannote.audio**.



## Características---



- Transcripción de audio usando OpenAI Whisper (modelo large-v2)## ✨ Características

- Identificación de hablantes con pyannote.audio

- Conversión de video a audio- ✅ Transcripción de audio con Whisper (OpenAI)

- Procesamiento de videos largos por segmentos- ✅ Identificación de hablantes (diarización)

- API REST con FastAPI- ✅ Conversión de videos a audio (MP3)

- Interfaz web incluida- ✅ Soporte para videos largos (procesamiento por chunks)

- ✅ API REST con FastAPI

## Instalación- ✅ Interfaz web amigable

- ✅ Múltiples idiomas soportados

```powershell- ✅ Configuración flexible de modelos

python -m venv venv

.\venv\Scripts\Activate.ps1---

pip install -r config\requirements.txt

```## 🚀 Inicio Rápido



## Configuración### 1. **Configurar el proyecto**

```powershell

Copia `config/.env.example` a `config/.env` y configura:# Ejecutar script de configuración automática

.\setup.ps1

```env```

WHISPER_MODEL=large-v2

HF_TOKEN=tu_token_de_huggingface### 2. **Configurar HF_TOKEN**

MAX_FILE_SIZE=524288000Edita `config/.env` y agrega tu token de Hugging Face:

``````env

HF_TOKEN=hf_tu_token_aquí

## Uso```



```powershell> **Obtén tu token:** https://huggingface.co/settings/tokens  

python main.py> **Acepta términos:** https://huggingface.co/pyannote/speaker-diarization-3.1

```

### 3. **Iniciar servidor**

Abre http://127.0.0.1:8888 en tu navegador.```powershell

python main.py

## API Endpoints```



- `POST /transcribe` - Transcribir audioEl servidor estará en: http://127.0.0.1:8888

- `POST /transcribe-diarize` - Transcribir con identificación de hablantes

- `POST /convert-video` - Convertir video a audio---

- `POST /convert-and-transcribe` - Convertir y transcribir en un solo paso

## 📦 Instalación Manual

## Requisitos

```powershell

- Python 3.13+# Crear entorno virtual

- FFmpeg (para conversión de video)python -m venv venv

- Token de Hugging Face (para diarización).\venv\Scripts\Activate.ps1


# Instalar dependencias
pip install -r config/requirements.txt

# Configurar .env
Copy-Item "config\.env.example" "config\.env"
notepad "config\.env"  # Agregar HF_TOKEN

# Iniciar
python main.py
```

---

## 🎯 Modelos de Whisper

Cambia el modelo en `config/.env`:

| Modelo | Precisión | Velocidad | Recomendado Para |
|--------|-----------|-----------|------------------|
| `tiny` | ⭐⭐ | ⚡⚡⚡⚡⚡ | Pruebas rápidas |
| `base` | ⭐⭐⭐ | ⚡⚡⚡⚡ | Uso general |
| `small` | ⭐⭐⭐⭐ | ⚡⚡⚡ | **Balance ideal** |
| `medium` | ⭐⭐⭐⭐⭐ | ⚡⚡ | **Español (recomendado)** |
| `large-v2` | ⭐⭐⭐⭐⭐ | ⚡ | Máxima precisión |

```env
WHISPER_MODEL=medium  # Para mejor precisión en español
```

📖 **Guía completa:** Ver `MODELOS_WHISPER.md`

---

## 🎬 Procesamiento de Videos Largos

El sistema ahora divide automáticamente videos largos en chunks para evitar timeouts:

- ✅ Videos >30 min se procesan automáticamente por segmentos
- ✅ Timeout dinámico basado en duración
- ✅ Concatenación automática de resultados
- ✅ Sin límite de duración (solo límite de tamaño de archivo)

Para ajustar el tamaño de chunks, edita `config/.env`:
```env
VIDEO_CHUNK_DURATION=600  # segundos (10 minutos)
```

---

## 📡 API Endpoints

### **1. Transcribir Audio**
```bash
POST /transcribe
```

### **2. Transcribir con Diarización**
```bash
POST /transcribe-diarize
```

### **3. Convertir Video a Audio**
```bash
POST /convert-video
```

### **4. Convertir y Transcribir Video**
```bash
POST /convert-and-transcribe
```

📚 **Documentación completa:** http://127.0.0.1:8888/docs

---

## 🔧 Configuración

Archivo `config/.env`:

```env
# Token de Hugging Face (OBLIGATORIO)
HF_TOKEN=hf_tu_token

# Modelo de Whisper
WHISPER_MODEL=medium

# Servidor
HOST=127.0.0.1
PORT=8888

# Límites
MAX_FILE_SIZE=104857600  # 100MB
```

---

## 📁 Estructura del Proyecto

```
├── main.py              # Servidor FastAPI (RAÍZ)
├── config/
│   ├── .env             # Configuración
│   └── requirements.txt # Dependencias
├── src/
│   ├── transcriber.py   # Módulo Whisper
│   ├── diarizer.py      # Módulo pyannote
│   ├── video_converter.py  # Conversión de videos
│   └── utils.py         # Utilidades
├── web/
│   ├── index.html       # Interfaz web
│   ├── styles.css
│   └── app.js
├── uploads/             # Archivos temporales
├── scripts/             # Scripts de utilidad
├── setup.ps1            # Configuración automática
├── restart.ps1          # Reiniciar servidor
└── cleanup.ps1          # Limpiar archivos temporales
```

---

## 🐛 Solución de Problemas

### **Error: HF_TOKEN no configurado**
```powershell
# Editar .env y agregar tu token
notepad config\.env
```

### **Error: FFmpeg no encontrado**
```powershell
# Instalar FFmpeg
choco install ffmpeg
```

### **Video muy largo no se procesa**
El sistema ahora procesa automáticamente videos largos. Si aún falla:
1. Verifica espacio en disco
2. Aumenta `MAX_FILE_SIZE` en `.env`
3. Usa modelo más pequeño: `WHISPER_MODEL=small`

### **Transcripción con errores**
Usa un modelo más grande:
```env
WHISPER_MODEL=medium  # En lugar de base/tiny
```

📖 Lee `MODELOS_WHISPER.md` para más detalles

---

## 🧹 Mantenimiento

```powershell
# Limpiar archivos temporales
.\cleanup.ps1

# Reiniciar servidor limpiamente
.\restart.ps1

# Verificar configuración
python scripts/check_config.py
```

---

## 📊 Requisitos del Sistema

- **Python:** 3.8+
- **RAM:** 4GB mínimo (8GB recomendado para `medium`)
- **Espacio:** 5GB (modelos + dependencias)
- **FFmpeg:** Instalado y en PATH
- **Internet:** Para primera descarga de modelos

---

## 🎓 Uso desde la Interfaz Web

1. Abre http://127.0.0.1:8888
2. Arrastra tu archivo de audio/video
3. Selecciona opciones (idioma, hablantes)
4. Click en "Transcribir"
5. Descarga el resultado

---

## 🤝 Contribución

Este es un proyecto personal. Puedes:
- Reportar bugs
- Sugerir mejoras
- Hacer fork y personalizar

---

## 📝 Licencia

Uso libre para proyectos personales y comerciales.

---

## 🙏 Créditos

- [OpenAI Whisper](https://github.com/openai/whisper) - Transcripción
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Diarización
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [FFmpeg](https://ffmpeg.org/) - Procesamiento de video

---

## 📞 Soporte

- **Documentación de modelos:** `MODELOS_WHISPER.md`
- **API Docs:** http://127.0.0.1:8888/docs
- **Verificar config:** `python scripts/check_config.py`

---

**Versión:** 2.0.0  
**Última actualización:** 5 de octubre de 2025  
**Estado:** ✅ Funcionando
