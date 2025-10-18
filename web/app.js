// Configuración
// Usar el mismo origen del navegador en producción y
// fallback a localhost para desarrollo local.
const API_BASE_URL = (typeof window !== 'undefined' && window.location && window.location.origin)
    ? window.location.origin
    : 'http://127.0.0.1:8888';

// Variables globales
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;
let currentAudioBlob = null;
let audioContext = null;
let analyser = null;
let animationId = null;
let lastTranscriptionResult = null; // Almacenar último resultado para descarga

// Elementos del DOM
const btnRecord = document.getElementById('btnRecord');
const btnStop = document.getElementById('btnStop');
const btnProcess = document.getElementById('btnProcess');
const btnCopy = document.getElementById('btnCopy');
const btnDownload = document.getElementById('btnDownload');
const btnDownloadPDF = document.getElementById('btnDownloadPDF');
const btnDownloadWord = document.getElementById('btnDownloadWord');
const btnClear = document.getElementById('btnClear');
const timerDisplay = document.getElementById('timer');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileInfo = document.getElementById('fileInfo');
const resultContent = document.getElementById('resultContent');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const canvas = document.getElementById('waveform');
const canvasCtx = canvas ? canvas.getContext('2d') : null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initRecording();
    initFileUpload();
    initResultActions();
    checkAPIHealth();
});

// Gestión de pestañas
function initTabs() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            navTabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// Verificar estado de la API
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        showToast('success', `API conectada correctamente - Modelo: ${data.whisper_model}`);
    } catch (error) {
        showToast('error', 'No se pudo conectar con la API. Asegúrate de que el servidor esté corriendo.');
    }
}

// Inicializar grabación
function initRecording() {
    btnRecord.addEventListener('click', toggleRecording);
    btnStop.addEventListener('click', stopRecording);
}

async function toggleRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            currentAudioBlob = audioBlob;
            
            showToast('success', 'Grabación completada. Procesando audio...');
            await processAudioWithDiarization(audioBlob, 'grabacion');
        };

        mediaRecorder.start();
        
        // Iniciar visualización de audio
        initAudioVisualization(stream);

        // Actualizar UI
        btnRecord.textContent = 'Grabando...';
        btnRecord.classList.add('recording');
        btnStop.disabled = false;

        // Iniciar temporizador
        recordingSeconds = 0;
        updateTimer();
        recordingTimer = setInterval(updateTimer, 1000);

        showToast('info', 'Grabación iniciada');

    } catch (error) {
        console.error('Error al iniciar grabación:', error);
        showToast('error', 'No se pudo acceder al micrófono. Verifica los permisos.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        
        // Detener todas las pistas de audio
        mediaRecorder.stream.getTracks().forEach(track => track.stop());

        // Detener visualización
        if (animationId) {
            cancelAnimationFrame(animationId);
        }

        // Actualizar UI
        btnRecord.textContent = '🎙️ Iniciar grabación';
        btnRecord.classList.remove('recording');
        btnStop.disabled = true;

        // Detener temporizador
        clearInterval(recordingTimer);
    }
}

function updateTimer() {
    recordingSeconds++;
    const hours = Math.floor(recordingSeconds / 3600);
    const minutes = Math.floor((recordingSeconds % 3600) / 60);
    const seconds = recordingSeconds % 60;

    timerDisplay.textContent = 
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Visualización de audio
function initAudioVisualization(stream) {
    if (!canvas || !canvasCtx) return;

    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    source.connect(analyser);
    analyser.fftSize = 256;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    function draw() {
        animationId = requestAnimationFrame(draw);

        analyser.getByteFrequencyData(dataArray);

        canvasCtx.fillStyle = 'rgb(255, 255, 255)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height;

            canvasCtx.fillStyle = `rgb(${91 + dataArray[i] / 2}, ${78 + dataArray[i] / 3}, ${150})`;
            canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    draw();
}

// Subida de archivos
function initFileUpload() {
    // Click en el área de carga
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Selección de archivo
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            const isAudio = file.type.startsWith('audio/');
            const isVideo = file.type.startsWith('video/');
            
            if (isAudio || isVideo) {
                handleFileSelect({ target: { files } });
            } else {
                showToast('error', 'Por favor, selecciona un archivo de audio o video válido');
            }
        }
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentAudioBlob = file;
        const isVideo = file.type.startsWith('video/');
        
        fileInfo.textContent = `${isVideo ? '🎬' : '📁'} ${file.name} (${formatFileSize(file.size)})`;
        
        // Mostrar preview de audio o video
        const mediaPreview = document.getElementById('mediaPreview');
        mediaPreview.innerHTML = '';
        
        if (isVideo) {
            const video = document.createElement('video');
            video.src = URL.createObjectURL(file);
            video.controls = true;
            video.style.width = '100%';
            video.style.maxHeight = '300px';
            video.style.borderRadius = '8px';
            mediaPreview.appendChild(video);
            
            // Mostrar opción de bitrate
            const bitrateContainer = document.getElementById('videoBitrateContainer');
            if (bitrateContainer) {
                bitrateContainer.style.display = 'block';
            }
        } else {
            const audio = document.createElement('audio');
            audio.src = URL.createObjectURL(file);
            audio.controls = true;
            audio.style.width = '100%';
            mediaPreview.appendChild(audio);
            
            // Ocultar opción de bitrate
            const bitrateContainer = document.getElementById('videoBitrateContainer');
            if (bitrateContainer) {
                bitrateContainer.style.display = 'none';
            }
        }
        
        btnProcess.disabled = false;
        showToast('success', `${isVideo ? 'Video' : 'Audio'} cargado correctamente`);
    }
}

btnProcess.addEventListener('click', async () => {
    if (currentAudioBlob) {
        await processAudioWithDiarization(currentAudioBlob, 'archivo');
    }
});

// Procesar audio con diarización
async function processAudioWithDiarization(audioBlob, source) {
    // Detectar si es video y preparar metadatos
    const isVideo = audioBlob.type.startsWith('video/');
    const fileName = audioBlob.name || (isVideo ? 'video.mp4' : 'audio.webm');

    const language = document.getElementById(source === 'grabacion' ? 'language' : 'fileLanguage').value;
    const minSpeakers = document.getElementById(source === 'grabacion' ? 'minSpeakers' : 'fileMinSpeakers').value;
    const maxSpeakers = document.getElementById(source === 'grabacion' ? 'maxSpeakers' : 'fileMaxSpeakers').value;
    const outputFormat = document.getElementById(source === 'grabacion' ? 'outputFormat' : 'fileOutputFormat').value;

    const endpoint = isVideo ? '/convert-and-transcribe' : '/transcribe-diarize';
    const message = isVideo ? 
        'Convirtiendo video y procesando audio...\nEsto puede tomar varios minutos.' :
        'Procesando audio con diarización...\nEsto puede tomar varios minutos.';

    showLoading(message);

    // 1) Intentar flujo presign -> upload directo a storage -> crear job
    try {
        const presignFd = new FormData();
        presignFd.append('filename', fileName);
        const presignResp = await fetch(`${API_BASE_URL}/presign`, { method: 'POST', body: presignFd });

        if (presignResp.ok) {
            const presignData = await presignResp.json();
            const uploadUrl = presignData.upload_url;
            // presignData may include a presigned GET URL (get_url) for worker download
            const objectUrl = presignData.get_url || presignData.object_url;

            // Subir directamente al storage (PUT)
            const putResp = await fetch(uploadUrl, {
                method: 'PUT',
                body: audioBlob,
                headers: {
                    'Content-Type': audioBlob.type || 'application/octet-stream'
                }
            });

            if (!putResp.ok) {
                throw new Error(`Upload failed: ${putResp.status} ${putResp.statusText}`);
            }

            // Crear job indicando la URL del objeto
            const createResp = await fetch(`${API_BASE_URL}/jobs/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_url: objectUrl, task: 'transcribe-diarize', whisper_model: null })
            });

            if (!createResp.ok) {
                throw new Error(`Create job failed: ${createResp.status} ${createResp.statusText}`);
            }

            const createData = await createResp.json();
            if (createData.job_id) {
                const jobId = createData.job_id;
                showLoading(`Trabajo encolado (job: ${jobId}). Esperando inicio...`);
                // Poll cada 3s
                const pollInterval = 3000;
                const poll = setInterval(async () => {
                    try {
                        const st = await fetch(`${API_BASE_URL}/status/${jobId}`);
                        if (!st.ok) throw new Error(`Status ${st.status}`);
                        const sdata = await st.json();

                        const progress = sdata.progress || 0;
                        const etaText = sdata.eta_seconds ? formatDuration(sdata.eta_seconds) : '';
                        showLoading(sdata.message || 'Procesando...');
                        updateProgress(progress, etaText ? `Tiempo restante: ${etaText}` : '');

                        if (sdata.state === 'done') {
                            clearInterval(poll);
                            hideLoading();
                            if (sdata.result) {
                                displayResults(sdata.result);
                                showToast('success', 'Transcripción completada.');
                                document.querySelector('[data-tab="resultados"]').click();
                            } else {
                                showToast('error', 'Job completado pero sin resultado');
                            }
                        } else if (sdata.state === 'error') {
                            clearInterval(poll);
                            hideLoading();
                            showToast('error', `Error en el job: ${sdata.error || sdata.message}`);
                        }

                    } catch (err) {
                        clearInterval(poll);
                        hideLoading();
                        console.error('Error al consultar status del job:', err);
                        showToast('error', 'No se pudo obtener el estado del job');
                    }
                }, pollInterval);

                return;
            }
        }

        // Si presign no es soportado o algo falló, caeremos al flujo convencional
    } catch (err) {
        console.warn('Presign flow failed, falling back to direct upload:', err);
    }

    // 2) Fallback: comportamiento existente (subir al backend y encolar async)
    try {
        const fd = new FormData();
        fd.append('file', audioBlob, fileName);
        fd.append('language', language);
        fd.append('min_speakers', minSpeakers);
        fd.append('max_speakers', maxSpeakers);
        fd.append('output_format', outputFormat);
        if (isVideo) {
            const bitrate = document.getElementById('videoBitrate')?.value || '192k';
            fd.append('bitrate', bitrate);
        }

        // Enviar como job asíncrono
        fd.append('async_process', 'true');

        const response = await fetch(`${API_BASE_URL}${endpoint}`, { method: 'POST', body: fd });
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();

        if (data.job_id) {
            const jobId = data.job_id;
            showLoading(`Trabajo encolado (job: ${jobId}). Esperando inicio...`);
            const pollInterval = 3000;
            const poll = setInterval(async () => {
                try {
                    const st = await fetch(`${API_BASE_URL}/status/${jobId}`);
                    if (!st.ok) throw new Error(`Status ${st.status}`);
                    const sdata = await st.json();

                    const progress = sdata.progress || 0;
                    const etaText = sdata.eta_seconds ? formatDuration(sdata.eta_seconds) : '';
                    showLoading(sdata.message || 'Procesando...');
                    updateProgress(progress, etaText ? `Tiempo restante: ${etaText}` : '');

                    if (sdata.state === 'done') {
                        clearInterval(poll);
                        hideLoading();
                        if (sdata.result) {
                            displayResults(sdata.result);
                            showToast('success', 'Transcripción completada.');
                            document.querySelector('[data-tab="resultados"]').click();
                        } else {
                            showToast('error', 'Job completado pero sin resultado');
                        }
                    } else if (sdata.state === 'error') {
                        clearInterval(poll);
                        hideLoading();
                        showToast('error', `Error en el job: ${sdata.error || sdata.message}`);
                    }

                } catch (err) {
                    clearInterval(poll);
                    hideLoading();
                    console.error('Error al consultar status del job:', err);
                    showToast('error', 'No se pudo obtener el estado del job');
                }
            }, pollInterval);

            return;
        }

        // Si la API devolvió el resultado directamente (sin job), mostrarlo
        displayResults(data);
        showToast('success', `Transcripción completada. ${data.num_speakers || 0} hablantes detectados.`);
        document.querySelector('[data-tab="resultados"]').click();

    } catch (error) {
        console.error('Error al procesar (fallback):', error);
        showToast('error', `Error al procesar el archivo: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Mostrar resultados
function displayResults(result) {
    // Guardar resultado para descarga
    lastTranscriptionResult = result;
    
    // Extraer texto de diferentes formatos que puede devolver el backend
    const extractText = (r) => {
        if (!r) return '';
        if (typeof r === 'string') return r;
        // Priorizar campos comunes
        if (r.text) return r.text;
        if (r.transcription) return r.transcription;
        if (r.transcribed) return r.transcribed;
        // Si hay segments, concatenar sus textos
        if (Array.isArray(r.segments) && r.segments.length) {
            return r.segments.map(s => s.text || s.transcription || '').filter(Boolean).join(' ');
        }
        // Fall back a JSON string
        try { return JSON.stringify(r); } catch (e) { return '' }
    };

    const text = extractText(result);
    // Reemplazar el contenido del contenedor (mantener estilo simple)
    if (text) {
        // Usar pre para conservar saltos de línea
        resultContent.innerHTML = '<pre style="white-space:pre-wrap;word-break:break-word">' + escapeHtml(text) + '</pre>';
    } else {
        resultContent.innerHTML = '<p class="empty-state">En esta sección se mostrará el texto transcrito...</p>';
    }
    
    // Mostrar estadísticas si están disponibles
    if (result.statistics) {
        const statsDiv = document.getElementById('statistics');
        const speakerStatsDiv = document.getElementById('speakerStats');
        
        statsDiv.style.display = 'block';
        speakerStatsDiv.innerHTML = '';

        Object.entries(result.statistics).forEach(([speaker, stats]) => {
            const speakerCard = document.createElement('div');
            speakerCard.className = 'speaker-stat';
            speakerCard.innerHTML = `
                <h4>${speaker}</h4>
                <div class="stat-row">
                    <span>Tiempo total:</span>
                    <strong>${stats.total_time.toFixed(1)}s</strong>
                </div>
                <div class="stat-row">
                    <span>Palabras:</span>
                    <strong>${stats.total_words}</strong>
                </div>
                <div class="stat-row">
                    <span>Participación:</span>
                    <strong>${stats.time_percentage.toFixed(1)}%</strong>
                </div>
                <div class="stat-row">
                    <span>Segmentos:</span>
                    <strong>${stats.segment_count}</strong>
                </div>
            `;
            speakerStatsDiv.appendChild(speakerCard);
        });
    }
}

// pequeño helper para escapar HTML antes de insertar en innerHTML
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, '&amp;')
         .replace(/</g, '&lt;')
         .replace(/>/g, '&gt;')
         .replace(/"/g, '&quot;')
         .replace(/'/g, '&#039;');
}

// Acciones de resultados
function initResultActions() {
    btnCopy.addEventListener('click', () => {
        const text = resultContent.textContent;
        navigator.clipboard.writeText(text).then(() => {
            showToast('success', 'Texto copiado al portapapeles');
        });
    });

    btnDownload.addEventListener('click', () => {
        const text = resultContent.textContent;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcripcion_${new Date().getTime()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('success', 'Transcripción descargada');
    });

    btnDownloadPDF.addEventListener('click', async () => {
        if (!lastTranscriptionResult) {
            showToast('error', 'No hay transcripción disponible para descargar');
            return;
        }
        
        try {
            showLoading('Generando PDF...');
            const response = await fetch(`${API_BASE_URL}/download/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lastTranscriptionResult)
            });
            
            if (!response.ok) throw new Error(`Error ${response.status}`);
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcripcion_${new Date().getTime()}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('success', 'PDF descargado correctamente');
        } catch (error) {
            console.error('Error al descargar PDF:', error);
            showToast('error', `Error al generar PDF: ${error.message}`);
        } finally {
            hideLoading();
        }
    });

    btnDownloadWord.addEventListener('click', async () => {
        if (!lastTranscriptionResult) {
            showToast('error', 'No hay transcripción disponible para descargar');
            return;
        }
        
        try {
            showLoading('Generando documento Word...');
            const response = await fetch(`${API_BASE_URL}/download/word`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lastTranscriptionResult)
            });
            
            if (!response.ok) throw new Error(`Error ${response.status}`);
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcripcion_${new Date().getTime()}.docx`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('success', 'Documento Word descargado correctamente');
        } catch (error) {
            console.error('Error al descargar Word:', error);
            showToast('error', `Error al generar documento Word: ${error.message}`);
        } finally {
            hideLoading();
        }
    });

    btnClear.addEventListener('click', () => {
        resultContent.innerHTML = '<p class="empty-state">En esta sección se mostrará el texto transcrito...</p>';
        document.getElementById('statistics').style.display = 'none';
        lastTranscriptionResult = null;
        showToast('info', 'Resultados limpiados');
    });
}

// Utilidades
function showLoading(message) {
    loadingMessage.textContent = message;
    loadingOverlay.classList.add('active');
    updateProgress(0, '');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
    updateProgress(0, '');
}

function updateProgress(percent, eta) {
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const progressETA = document.getElementById('progressETA');
    
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressPercent) progressPercent.textContent = `${percent}%`;
    if (progressETA) progressETA.textContent = eta || '';
}

function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    }[type];

    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${icon}</span>
        <span>${message}</span>
    `;

    document.getElementById('toastContainer').appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return '0s';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs > 0 ? hrs + 'h ' : ''}${mins > 0 ? mins + 'm ' : ''}${secs}s`;
}
