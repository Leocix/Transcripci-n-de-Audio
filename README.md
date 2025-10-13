# 🎤 Transcripción de Audio con Diarización# Transcripción de Audio# 🎤 Transcripción de Audio con Diarización



Sistema de transcripción de audio y video con identificación automática de hablantes.



## ✨ CaracterísticasSistema de transcripción de audio y video con identificación de hablantes.Sistema de transcripción de audio y video con identificación automática de hablantes usando **Whisper** y **pyannote.audio**.



- ✅ Transcripción precisa con OpenAI Whisper (modelo large-v2)

- ✅ Identificación de hablantes con pyannote.audio

- ✅ **Numeración de hablantes desde SPEAKER_01** (mejorado)## Características---

- ✅ Conversión de video a audio (MP3)

- ✅ Procesamiento de videos largos por segmentos

- ✅ API REST con FastAPI

- ✅ Interfaz web amigable- Transcripción de audio usando OpenAI Whisper (modelo large-v2)## ✨ Características



## 🚀 Inicio Rápido

Este repositorio está preparado para deploy en DigitalOcean (DOCR + App Platform). A continuación las instrucciones rápidas para CI y despliegue.

### CI / Deploy (DOCR)

Usamos un workflow de GitHub Actions (`.github/workflows/ci-docr.yml`) que construye y empuja imágenes a DO Container Registry (DOCR). Por defecto construye una imagen "minimal" usando `config/requirements.txt`. Opcionalmente puede construir una imagen "full" con dependencias pesadas si configuras el secreto `DO_FULL_IMAGE=true`.

Secrets necesarios en GitHub:
- `DIGITALOCEAN_ACCESS_TOKEN` — token con permisos para DOCR y App Platform.
- `DOCR_REGISTRY` — nombre de tu registry en DOCR (ej: my-registry).
- `DOCR_REPOSITORY` — nombre del repo de imagen en DOCR (ej: transcripcion-audio).
- (Opcional) `DO_FULL_IMAGE=true` — si quieres también construir la imagen con `requirements-optional.txt`.
- (Opcional) `DO_APP_ID` — ID de la App Platform si quieres que el workflow actualice la app automáticamente.

El workflow etiqueta la imagen con el SHA y con `latest`. Para usar la imagen en App Platform, edita `do_app_spec.yaml` con la ruta correcta del registry/repositorio.

### Dependencias: minimal vs full

Instala solo lo mínimo en producción para reducir el tamaño de la imagen:

Minimal (recomendado para App Platform):
```
pip install -r config/requirements.txt
```

Full (GPU / máquinas con suficiente RAM):
```
pip install -r config/requirements-optional.txt
```

Continúa con el README existente...



```powershell- Conversión de video a audio- ✅ Transcripción de audio con Whisper (OpenAI)

# 1. Activar entorno virtual

.\venv\Scripts\Activate.ps1- Procesamiento de videos largos por segmentos- ✅ Identificación de hablantes (diarización)



# 2. Configurar token de Hugging Face en config/.env- API REST con FastAPI- ✅ Conversión de videos a audio (MP3)

# HF_TOKEN=tu_token_aqui

- Interfaz web incluida- ✅ Soporte para videos largos (procesamiento por chunks)

# 3. Iniciar servidor

python main.py- ✅ API REST con FastAPI

```

## Instalación- ✅ Interfaz web amigable

Abre **http://127.0.0.1:8888** en tu navegador.

- ✅ Múltiples idiomas soportados

## 📦 Instalación Completa

```powershell- ✅ Configuración flexible de modelos

```powershell

# Crear entorno virtualpython -m venv venv

python -m venv venv

.\venv\Scripts\Activate.ps1.\venv\Scripts\Activate.ps1---



# Instalar dependenciaspip install -r config\requirements.txt

pip install -r config\requirements.txt

```## 🚀 Inicio Rápido

# Configurar .env

Copy-Item "config\.env.example" "config\.env"

notepad "config\.env"  # Editar y agregar HF_TOKEN

```## Configuración### 1. **Configurar el proyecto**



## 🎯 Configuración```powershell



Edita `config/.env`:Copia `config/.env.example` a `config/.env` y configura:# Ejecutar script de configuración automática



```env.\setup.ps1

# Token de Hugging Face (OBLIGATORIO para diarización)

HF_TOKEN=tu_token_de_huggingface```env```



# Modelo de WhisperWHISPER_MODEL=large-v2

WHISPER_MODEL=large-v2

HF_TOKEN=tu_token_de_huggingface### 2. **Configurar HF_TOKEN**

# Límites

MAX_FILE_SIZE=524288000  # 500MBMAX_FILE_SIZE=524288000Edita `config/.env` y agrega tu token de Hugging Face:

```

``````env

**Obtén tu token:** https://huggingface.co/settings/tokens  

**Acepta términos:** https://huggingface.co/pyannote/speaker-diarization-3.1HF_TOKEN=hf_tu_token_aquí



## 📡 API Endpoints## Uso```



- `POST /transcribe` - Transcribir audio sin identificar hablantes

- `POST /transcribe-diarize` - Transcribir con identificación de hablantes

- `POST /convert-video` - Convertir video a audio MP3```powershell> **Obtén tu token:** https://huggingface.co/settings/tokens  

- `POST /convert-and-transcribe` - Convertir y transcribir en un paso

python main.py> **Acepta términos:** https://huggingface.co/pyannote/speaker-diarization-3.1

**Documentación completa:** http://127.0.0.1:8888/docs

```

## 📝 Ejemplo de Salida

### 3. **Iniciar servidor**

```

[SPEAKER_01]: ¿Cómo estarán en la encenada? al viejo ceibal, Abre http://127.0.0.1:8888 en tu navegador.```powershell

los jazmineros y orquídeas en flor...

python main.py

[SPEAKER_02]: Amor, no llores, veo luz en tus males, 

siguiéndote al corazón, bailando en un canto de solsales.## API Endpoints```



[SPEAKER_01]: Niño, soy un hombre con tristeza, sé del peso 

en tu verdad, de escaparte por robar porque robas para cenar.

```- `POST /transcribe` - Transcribir audioEl servidor estará en: http://127.0.0.1:8888



## 💡 Mejora Reciente- `POST /transcribe-diarize` - Transcribir con identificación de hablantes



Los hablantes ahora se numeran desde **SPEAKER_01** (en lugar de SPEAKER_00), haciendo la lectura más natural e intuitiva.- `POST /convert-video` - Convertir video a audio---



Ver detalles completos en: **MEJORA_SPEAKERS.md**- `POST /convert-and-transcribe` - Convertir y transcribir en un solo paso



## 🔧 Requisitos del Sistema## 📦 Instalación Manual



- **Python:** 3.13+## Requisitos

- **FFmpeg:** Instalado y en PATH

- **RAM:** 8GB recomendado```powershell

- **Espacio:** ~5GB para modelos

- **Internet:** Para descarga inicial de modelos- Python 3.13+# Crear entorno virtual



## 📁 Estructura del Proyecto- FFmpeg (para conversión de video)python -m venv venv



```- Token de Hugging Face (para diarización).\venv\Scripts\Activate.ps1

├── main.py                    # Servidor FastAPI

├── config/

│   ├── .env                   # Configuración# Instalar dependencias

│   └── requirements.txt       # Dependenciaspip install -r config/requirements.txt

├── src/

│   ├── transcriber.py         # Whisper# Configurar .env

│   ├── diarizer.py            # pyannoteCopy-Item "config\.env.example" "config\.env"

│   ├── video_converter.py     # FFmpegnotepad "config\.env"  # Agregar HF_TOKEN

│   └── utils.py               # Utilidades

└── web/                       # Interfaz web# Iniciar

```python main.py

```

## 🐛 Solución de Problemas

---

**Error: HF_TOKEN no configurado**

```powershell## 🎯 Modelos de Whisper

notepad config\.env  # Agregar HF_TOKEN

```Cambia el modelo en `config/.env`:



**FFmpeg no encontrado**| Modelo | Precisión | Velocidad | Recomendado Para |

```powershell|--------|-----------|-----------|------------------|

choco install ffmpeg  # Windows con Chocolatey| `tiny` | ⭐⭐ | ⚡⚡⚡⚡⚡ | Pruebas rápidas |

```| `base` | ⭐⭐⭐ | ⚡⚡⚡⚡ | Uso general |

| `small` | ⭐⭐⭐⭐ | ⚡⚡⚡ | **Balance ideal** |

**Transcripción con errores**| `medium` | ⭐⭐⭐⭐⭐ | ⚡⚡ | **Español (recomendado)** |

- Usa modelo `medium` o `large-v2` para español| `large-v2` | ⭐⭐⭐⭐⭐ | ⚡ | Máxima precisión |

- Asegúrate de tener buena calidad de audio

```env

## 📚 DocumentaciónWHISPER_MODEL=medium  # Para mejor precisión en español

```

- **MEJORA_SPEAKERS.md** - Detalles de numeración de hablantes

- **ESTADO.md** - Estado actual del proyecto📖 **Guía completa:** Ver `MODELOS_WHISPER.md`

- **/docs** - Documentación interactiva de la API

---

## 🙏 Créditos

## 🎬 Procesamiento de Videos Largos

- [OpenAI Whisper](https://github.com/openai/whisper)

- [pyannote.audio](https://github.com/pyannote/pyannote-audio)El sistema ahora divide automáticamente videos largos en chunks para evitar timeouts:

- [FastAPI](https://fastapi.tiangolo.com/)

- [FFmpeg](https://ffmpeg.org/)- ✅ Videos >30 min se procesan automáticamente por segmentos

- ✅ Timeout dinámico basado en duración

---- ✅ Concatenación automática de resultados

- ✅ Sin límite de duración (solo límite de tamaño de archivo)

**Versión:** 2.0.0  

**Última actualización:** 5 de octubre de 2025  Para ajustar el tamaño de chunks, edita `config/.env`:

**Estado:** ✅ Funcionando```env

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

## 📄 Exportar a DOCX / PDF

Puedes pedir que la transcripción se devuelva como archivo Word (.docx) o PDF (.pdf) directamente desde los endpoints de transcripción.

- Parámetro (form): `download_format` — valores aceptados: `docx`, `pdf`.
- Si incluyes `background_tasks` en la petición (FastAPI BackgroundTasks), el archivo exportado se eliminará automáticamente después de la respuesta.

Ejemplo (curl):

```bash
curl -X POST "http://127.0.0.1:8888/transcribe" \
	-F "file=@mi_audio.wav" \
	-F "download_format=docx" \
	-o resultado.docx
```

Requisitos adicionales: instala `python-docx` y `reportlab` para habilitar las exportaciones:

```powershell
pip install python-docx reportlab
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
