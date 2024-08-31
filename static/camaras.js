let mediaRecorder;
let recordedBlobs;
let gumStream;
let processId = null;
let isProcessing = false;

function startRecording() {
    recordedBlobs = [];
    const constraints = {
        video: true,
        audio: true
    };

    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => {
            gumStream = stream;
            const gumVideo = document.querySelector('video#videoPlayer');
            gumVideo.srcObject = stream;
            gumVideo.style.display = 'block';

            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.onstop = (event) => {
                const videoBuffer = new Blob(recordedBlobs, { type: 'video/webm' });
                const videoURL = window.URL.createObjectURL(videoBuffer);
                gumVideo.srcObject = null;
                gumVideo.src = videoURL;
                gumVideo.controls = true;
                gumVideo.play();
            };
            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    recordedBlobs.push(event.data);
                }
            };
            mediaRecorder.start(10); // Grab chunks of 10ms

            document.getElementById('startButton').disabled = true;
            document.getElementById('stopButton').disabled = false;
            document.getElementById('uploadButton').disabled = true;
            document.getElementById('saveRecordsButton').disabled = true;
            document.getElementById('dateInput').disabled = true;
        })
        .catch(error => {
            console.error('Error accessing user media', error);
            alert('Error: Unable to access camera and microphone.');
        });
}

function stopRecording() {
    mediaRecorder.stop();
    gumStream.getTracks().forEach(track => track.stop());

    // Activar botón de grabar y desactivar botón de parar
    document.getElementById('startButton').disabled = false;
    document.getElementById('stopButton').disabled = true;
    document.getElementById('uploadButton').disabled = false;
    document.getElementById('saveButton').disabled = false;
}


function selectVideo() {
    document.getElementById('videoFileInput').click();
    document.getElementById('saveButton').disabled = false;
    document.getElementById('dateInput').disabled = true;
}

function getVideoDurationInSeconds() {
    const videoPlayer = document.getElementById('videoPlayer');
    return Math.floor(videoPlayer.duration);
}

function enableSendRecordsButton() {
    const dateInput = document.getElementById('dateInput');
    dateInput.addEventListener('input', () => {
        document.getElementById('saveRecordsButton').disabled = false;
    });
}

enableSendRecordsButton();

function loadVideo(event) {
    const file = event.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = url;

        const fileNameInput = document.getElementById('fileNameInput');
        fileNameInput.value = file.name;
        document.getElementById('saveButton').disabled = false;
        document.getElementById('saveRecordsButton').disabled = true;
    }
}

function saveVideo() {
    const videoFileInput = document.getElementById('videoFileInput');
    const videoPlayer = document.getElementById('videoPlayer');
    const currentDate = new Date();
    const dateTimeStr = `${String(currentDate.getDate()).padStart(2, '0')}${String(currentDate.getMonth() + 1).padStart(2, '0')}${currentDate.getFullYear()}-${String(currentDate.getHours()).padStart(2, '0')}${String(currentDate.getMinutes()).padStart(2, '0')}${String(currentDate.getSeconds()).padStart(2, '0')}`;
    const videoOutputTitle = `${dateTimeStr}.mp4`;
    let file = videoFileInput.files[0];
    let formData = new FormData();

    if (!file && videoPlayer.src) {
        fetch(videoPlayer.src)
            .then(response => response.blob())
            .then(blob => {
                file = new File([blob], videoOutputTitle, { type: 'video/mp4' });
                processFile(file);
            })
            .catch(error => {
                console.error('Error al convertir el video:', error);
            });
    } else if (file) {
        processFile(file);
    } else {
        alert('No hay video cargado para guardar.');
    }

    function processFile(file) {
        if (file) {
            const fileNameInput = document.getElementById('fileNameInput');
            let fileName = fileNameInput.value.trim();
            if (!fileName) {
                fileName = file.name;
            }
            if (!fileName.endsWith('.mp4')) {
                fileName += '.mp4';
            }

            formData.append('file', file);
            formData.append('filename', fileName);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/save', true);

            xhr.onload = function () {
                if (xhr.status === 200) {
                    alert('Video guardado exitosamente');
                    document.getElementById('saveButton').disabled = true;
                    document.getElementById('sendButton').disabled = false;

                    registerLogArchivo(fileName);
                } else {
                    console.error('Error al guardar el video');
                }
            };
            xhr.send(formData);
        }
    }
}


function updateLabel() {
    const dateInput = document.getElementById('dateInput');
    const dateLabel = document.getElementById('dateLabel');
    dateLabel.textContent = dateInput.value;
}


function updateTable() {
    document.getElementById('sendButton').disabled = true;
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSrc = videoPlayer.src;
    const manualStartTime = document.getElementById('manualStartTimeInput').value;
    const currentDate = new Date();
    const dateTimeStr = `${String(currentDate.getDate()).padStart(2, '0')}${String(currentDate.getMonth() + 1).padStart(2, '0')}${currentDate.getFullYear()}-${String(currentDate.getHours()).padStart(2, '0')}${String(currentDate.getMinutes()).padStart(2, '0')}${String(currentDate.getSeconds()).padStart(2, '0')}`;
    const videoOutputTitle = `${dateTimeStr}.mp4`;
    let manualStartSeconds = 0;

    if (manualStartTime) {
        const [hours, minutes, seconds] = manualStartTime.split(':').map(Number);
        manualStartSeconds = (hours * 3600) + (minutes * 60) + (seconds || 0);
    }

    if (videoSrc) {
        fetch(videoSrc)
            .then(response => response.blob())
            .then(blob => {
                const formData = new FormData();
                formData.append('file', blob, videoOutputTitle);

                fetch('/upload', {
                    method: 'POST',
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('dataTable').getElementsByTagName('tbody')[0];
                    tbody.innerHTML = ''; // Limpiar filas existentes
                    const events = data.events || []; // Asegúrate de que 'events' siempre sea un arreglo

                    events.forEach(event => {
                        const row = tbody.insertRow();
                        const startCell = row.insertCell(0);
                        const endCell = row.insertCell(1);

                        // Ajustar las horas de inicio y final agregando el tiempo personalizado
                        const adjustedStartTime = adjustTime(event.start_time, manualStartSeconds);
                        const adjustedEndTime = adjustTime(event.end_time, manualStartSeconds);

                        startCell.textContent = adjustedStartTime;
                        endCell.textContent = adjustedEndTime;

                        row.addEventListener('click', () => {
                            const timeParts = adjustedStartTime.split(':');
                            const seconds = parseInt(timeParts[0], 10) * 3600 + parseInt(timeParts[1], 10) * 60 + parseInt(timeParts[2], 10);
                            const videoTime = seconds - manualStartSeconds;  // Restar el tiempo personalizado para ajustar el video
                            videoPlayer.currentTime = videoTime >= 0 ? videoTime : 0;
                            videoPlayer.play();
                        });
                    });
                    alert("Video procesado correctamente");
                    document.getElementById('sendButton').disabled = false;
                    document.getElementById('dateInput').disabled = false;
                })
                .catch(error => {
                    console.error('Error al enviar video:', error);
                });
            })
            .catch(error => {
                console.error('Error al obtener el blob del video:', error);
            });
    } else {
        alert('Por favor seleccione un archivo de video primero.');
    }
}

function adjustTime(originalTime, manualStartSeconds) {
    const [hours, minutes, seconds] = originalTime.split(':').map(Number);
    const originalSeconds = (hours * 3600) + (minutes * 60) + (seconds || 0);
    const adjustedSeconds = originalSeconds + manualStartSeconds;

    const adjustedHours = Math.floor(adjustedSeconds / 3600).toString().padStart(2, '0');
    const adjustedMinutes = Math.floor((adjustedSeconds % 3600) / 60).toString().padStart(2, '0');
    const adjustedSecondsFinal = (adjustedSeconds % 60).toString().padStart(2, '0');

    return `${adjustedHours}:${adjustedMinutes}:${adjustedSecondsFinal}`;
}

document.getElementById('manualStartCheckbox').addEventListener('change', function () {
    const manualStartTimeDiv = document.getElementById('manualStartTimeDiv');
    if (this.checked) {
        manualStartTimeDiv.style.display = 'block';
    } else {
        manualStartTimeDiv.style.display = 'none';
        document.getElementById('manualStartTimeInput').value = '';  // Limpiar el valor cuando se deselecciona
    }
});


function cancelProcessing() {
    if (isProcessing && processId) {
        fetch('/cancel_process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ process_id: processId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Procesamiento de video cancelado.');
                document.getElementById('sendButton').disabled = true;
                document.getElementById('cancelButton').disabled = true;
                document.getElementById('saveButton').disabled = true;
                document.getElementById('saveRecordsButton').disabled = true;
            } else {
                alert('Error al cancelar el procesamiento del video.');
            }
        })
        .catch(error => {
            console.error('Error al cancelar el procesamiento del video:', error);
        });
    }
}

function saveRecords() {
    const dateInput = document.getElementById('dateInput').value;
    const cameraSelect = document.getElementById('cameraSelect').value;
    const rows = document.getElementById('dataTable').getElementsByTagName('tbody')[0].rows;
    const records = [];
    const currentDate = new Date();
    const selectedDate = new Date(dateInput);
    const manualStartTime = document.getElementById('manualStartTimeInput').value;
    const videoDuration = getVideoDurationInSeconds(); // Debes implementar esta función para obtener la duración del video en segundos

    // Verificar que la fecha no sea posterior a la fecha actual
    if (selectedDate > currentDate) {
        alert('La fecha seleccionada no puede ser después de la fecha actual.');
        return;
    }

    // Verificar si el ajuste manual de hora está activado y si es válido
    if (manualStartTime) {
        const [hours, minutes, seconds] = manualStartTime.split(':').map(Number);
        const startTimeInSeconds = hours * 3600 + minutes * 60 + (seconds || 0);
        const endTimeInSeconds = startTimeInSeconds + videoDuration;

        if (endTimeInSeconds > 86400) { // 86400 segundos es igual a 24 horas
            alert('La duración del video excede el tiempo disponible antes de la medianoche. Por favor, selecciona otro video.');
            return;
        }
    }

    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].cells;
        const horaInicio = cells[0].innerText;
        const horaFinal = cells[1].innerText;
        records.push({ hora_inicio: horaInicio, hora_final: horaFinal });
    }

    if (!dateInput) {
        alert('Por favor, selecciona una fecha.');
        return;
    }

    fetch('/save_records', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fecha: dateInput, camara_id: cameraSelect, registros: records, hora_inicio_manual: manualStartTime })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Registros guardados exitosamente.');
        } else {
            alert('Error al guardar los registros.');
        }
    })
    .catch(error => console.error('Error:', error));
}


function refreshTable() {
    const eventData = JSON.parse(window.localStorage.getItem('eventData'));
    if (eventData) {
        updateEventTable(eventData);
    } else {
        alert('No hay datos de eventos para mostrar');
    }
}

function registerLogArchivo(fileName) {
    const token = getCookie('token'); // Obtén el token desde las cookies

    fetch('/log_archivo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` // Añade el token al encabezado de autorización
        },
        body: JSON.stringify({ nombre_archivo: fileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Registro de archivo guardado exitosamente.');
        } else {
            console.error('Error al registrar el archivo:', data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}


function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}