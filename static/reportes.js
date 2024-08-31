document.addEventListener('DOMContentLoaded', function() {
    var ctx = document.getElementById('incidenceChart').getContext('2d');
    window.incidenceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}:00`),
            datasets: [{
                label: 'Promedio de Incidencias a lo largo del día',
                data: Array(24).fill(0),
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Hora'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Incidencias'
                    }
                }
            }
        }
    });

    function updateChart(days) {
        const camara_id = document.getElementById('cameraSelect').value;
        selectedRange = days;
        fetch(`/get_report/${camara_id}/${days}`)
            .then(response => response.json())
            .then(data => {
                const newData = data.map(row => row[1]); // Assuming row[1] is the incident count
                window.incidenceChart.data.datasets[0].data = newData;
                window.incidenceChart.update();
            });
    }

    function updateChartRange(camara_id) {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (!startDate || !endDate) {
            alert("Por favor, seleccione ambas fechas.");
            return;
        }

        const start = new Date(startDate);
        const end = new Date(endDate);
        const today = new Date();

        if (start > end) {
            alert("La fecha de inicio no puede ser mayor que la fecha de fin.");
            return;
        }

        if (start > today || end > today) {
            alert("Las fechas no pueden estar en el futuro.");
            return;
        }

        fetch(`/get_report_range/${camara_id}?start_date=${startDate}&end_date=${endDate}`)
            .then(response => response.json())
            .then(data => {
                const newData = data.map(row => row[1]); // Assuming row[1] is the incident count
                window.incidenceChart.data.datasets[0].data = newData;
                window.incidenceChart.update();
            });
    }

    window.generatePDF = function() {
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF();

        const canvas = document.getElementById('incidenceChart');
        const imgData = canvas.toDataURL('image/png');

        const currentDate = new Date();
        const dateStr = currentDate.toLocaleDateString();
        const timeStr = currentDate.toLocaleTimeString();
        const dateTimeStr = `${String(currentDate.getDate()).padStart(2, '0')}${String(currentDate.getMonth() + 1).padStart(2, '0')}${currentDate.getFullYear()}-${String(currentDate.getHours()).padStart(2, '0')}${String(currentDate.getMinutes()).padStart(2, '0')}${String(currentDate.getSeconds()).padStart(2, '0')}`;
        const reportTitle = `Reporte-${dateTimeStr}`;

        const userName = "{{ session['username'] }}";

        // Rango de fechas
        let rangeStr = "";
        if (selectedRange === 1) {
            rangeStr = `Del ${getYesterdayDateString()}`;
        } else if (selectedRange === 7) {
            rangeStr = `Del ${getPastDateString(7)} al ${getYesterdayDateString()}`;
        } else if (selectedRange === 30) {
            rangeStr = `Del ${getPastDateString(30)} al ${getYesterdayDateString()}`;
        } else {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            rangeStr = `Del ${startDate} al ${endDate}`;
        }

        // Verificar si hay datos en el gráfico
        if (!chartHasData()) {
            alert("No hay datos para generar el reporte.");
            return;
        }

        pdf.setFontSize(18);
        pdf.text(reportTitle, 10, 10);
        pdf.setFontSize(12);
        pdf.text(`Generado por: ${userName}`, 10, 20);
        pdf.text(`Fecha y hora de generación: ${dateStr} ${timeStr}`, 10, 30);
        pdf.text(`Rango de fechas: ${rangeStr}`, 10, 40);

        // Añadir el gráfico
        pdf.addImage(imgData, 'PNG', 10, 50, 180, 90);

        // Guardar el PDF
        pdf.save(`${reportTitle}.pdf`);
    }

    function chartHasData() {
        const chart = Chart.getChart('incidenceChart'); // Obtén la instancia del gráfico
        if (chart.data.datasets.length > 0) {
            for (let dataset of chart.data.datasets) {
                if (dataset.data.length > 0) {
                    return true;
                }
            }
        }
        return false;
    }

    function getYesterdayDateString() {
        const date = new Date();
        date.setDate(date.getDate() - 1);
        return date.toISOString().split('T')[0];
    }

    function getPastDateString(days) {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return date.toISOString().split('T')[0];
    }

    // Variables para rango seleccionado
    let selectedRange = 1;

    window.updateChart = updateChart;
    window.updateChartRange = updateChartRange;


});
