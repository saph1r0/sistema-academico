/**
 * Sistema de gráficos para el portal académico
 * Utiliza Chart.js para crear visualizaciones interactivas
 */

// Configuración global de Chart.js
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.color = '#374151';
Chart.defaults.borderColor = '#e5e7eb';

// Paleta de colores del sistema
const CHART_COLORS = {
    primary: '#3b82f6',
    secondary: '#10b981',
    accent: '#f59e0b',
    danger: '#ef4444',
    warning: '#f97316',
    info: '#06b6d4',
    success: '#22c55e',
    purple: '#8b5cf6',
    gray: '#6b7280'
};

// Gradientes para gráficos más atractivos
function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

/**
 * Clase base para gráficos
 */
class BaseChart {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas con ID '${canvasId}' no encontrado`);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
        this.options = options;
        this.isLoading = false;
        
        // Mostrar estado de carga inicial
        this.showLoading();
    }
    
    showLoading() {
        const container = this.canvas.parentElement;
        container.innerHTML = `
            <div class="chart-loading">
                <div class="spinner"></div>
                <p class="ml-3 text-gray-600">Cargando gráfico...</p>
            </div>
        `;
    }
    
    showError(message = 'Error al cargar el gráfico') {
        const container = this.canvas.parentElement;
        container.innerHTML = `
            <div class="chart-error">
                <svg class="w-12 h-12 mb-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                <p class="font-medium">${message}</p>
                <button onclick="location.reload()" class="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700">
                    Reintentar
                </button>
            </div>
        `;
    }
    
    async fetchData(url) {
        try {
            this.isLoading = true;
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.isLoading = false;
            return data;
        } catch (error) {
            this.isLoading = false;
            console.error('Error fetching chart data:', error);
            this.showError(`Error: ${error.message}`);
            throw error;
        }
    }
    
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

/**
 * Gráfico de distribución de notas
 */
class GradeDistributionChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, options);
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de Notas por Rangos',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${context.parsed.y} estudiantes (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: 'Número de Estudiantes'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Rangos de Notas'
                    }
                }
            }
        };
    }
    
    async loadAndRender(apiUrl) {
        try {
            const data = await this.fetchData(apiUrl);
            this.render(data);
        } catch (error) {
            // Error ya manejado en fetchData
        }
    }
    
    render(data) {
        // Restaurar canvas si fue reemplazado por loading/error
        if (!this.canvas || !this.canvas.getContext) {
            const container = this.canvas ? this.canvas.parentElement : document.getElementById(this.canvasId);
            container.innerHTML = `<canvas id="${this.canvasId}"></canvas>`;
            this.canvas = document.getElementById(this.canvasId);
            this.ctx = this.canvas.getContext('2d');
        }
        
        const chartData = {
            labels: ['0-5', '6-10', '11-15', '16-20'],
            datasets: [{
                label: 'Estudiantes',
                data: [
                    data.ranges?.['0-5'] || 0,
                    data.ranges?.['6-10'] || 0,
                    data.ranges?.['11-15'] || 0,
                    data.ranges?.['16-20'] || 0
                ],
                backgroundColor: [
                    CHART_COLORS.danger + '80',
                    CHART_COLORS.warning + '80',
                    CHART_COLORS.info + '80',
                    CHART_COLORS.success + '80'
                ],
                borderColor: [
                    CHART_COLORS.danger,
                    CHART_COLORS.warning,
                    CHART_COLORS.info,
                    CHART_COLORS.success
                ],
                borderWidth: 2
            }]
        };
        
        this.chart = new Chart(this.ctx, {
            type: 'bar',
            data: chartData,
            options: { ...this.defaultOptions, ...this.options }
        });
    }
}

/**
 * Gráfico de evolución de promedios
 */
class GradeEvolutionChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, options);
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Evolución de Promedios por Evaluación',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 20,
                    title: {
                        display: true,
                        text: 'Promedio'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Evaluaciones'
                    }
                }
            }
        };
    }
    
    async loadAndRender(apiUrl) {
        try {
            const data = await this.fetchData(apiUrl);
            this.render(data);
        } catch (error) {
            // Error ya manejado en fetchData
        }
    }
    
    render(data) {
        if (!this.canvas || !this.canvas.getContext) {
            const container = this.canvas ? this.canvas.parentElement : document.getElementById(this.canvasId);
            container.innerHTML = `<canvas id="${this.canvasId}"></canvas>`;
            this.canvas = document.getElementById(this.canvasId);
            this.ctx = this.canvas.getContext('2d');
        }
        
        const chartData = {
            labels: ['Parcial 1', 'Parcial 2', 'Parcial 3'],
            datasets: [{
                label: 'Promedio de Clase',
                data: [
                    data.averages?.parcial1 || 0,
                    data.averages?.parcial2 || 0,
                    data.averages?.parcial3 || 0
                ],
                borderColor: CHART_COLORS.primary,
                backgroundColor: CHART_COLORS.primary + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        };
        
        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: chartData,
            options: { ...this.defaultOptions, ...this.options }
        });
    }
}

/**
 * Gráfico de asistencia
 */
class AttendanceChart extends BaseChart {
    constructor(canvasId, type = 'bar', options = {}) {
        super(canvasId, options);
        this.chartType = type;
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Estadísticas de Asistencia',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Porcentaje (%)'
                    }
                }
            }
        };
    }
    
    async loadAndRender(apiUrl) {
        try {
            const data = await this.fetchData(apiUrl);
            this.render(data);
        } catch (error) {
            // Error ya manejado en fetchData
        }
    }
    
    render(data) {
        if (!this.canvas || !this.canvas.getContext) {
            const container = this.canvas ? this.canvas.parentElement : document.getElementById(this.canvasId);
            container.innerHTML = `<canvas id="${this.canvasId}"></canvas>`;
            this.canvas = document.getElementById(this.canvasId);
            this.ctx = this.canvas.getContext('2d');
        }
        
        let chartData;
        
        if (this.chartType === 'doughnut') {
            // Gráfico circular para resumen general
            chartData = {
                labels: ['Presente', 'Ausente', 'Tardanza'],
                datasets: [{
                    data: [
                        data.summary?.present || 0,
                        data.summary?.absent || 0,
                        data.summary?.late || 0
                    ],
                    backgroundColor: [
                        CHART_COLORS.success,
                        CHART_COLORS.danger,
                        CHART_COLORS.warning
                    ]
                }]
            };
        } else {
            // Gráfico de barras para asistencia por estudiante (top 10)
            const students = data.students?.slice(0, 10) || [];
            chartData = {
                labels: students.map(s => s.name?.split(' ').slice(0, 2).join(' ') || 'N/A'),
                datasets: [{
                    label: 'Asistencia (%)',
                    data: students.map(s => s.percentage || 0),
                    backgroundColor: students.map(s => {
                        const pct = s.percentage || 0;
                        if (pct >= 90) return CHART_COLORS.success + '80';
                        if (pct >= 75) return CHART_COLORS.info + '80';
                        if (pct >= 60) return CHART_COLORS.warning + '80';
                        return CHART_COLORS.danger + '80';
                    }),
                    borderColor: students.map(s => {
                        const pct = s.percentage || 0;
                        if (pct >= 90) return CHART_COLORS.success;
                        if (pct >= 75) return CHART_COLORS.info;
                        if (pct >= 60) return CHART_COLORS.warning;
                        return CHART_COLORS.danger;
                    }),
                    borderWidth: 2
                }]
            };
        }
        
        this.chart = new Chart(this.ctx, {
            type: this.chartType,
            data: chartData,
            options: { ...this.defaultOptions, ...this.options }
        });
    }
}

/**
 * Utilidades para manejo de gráficos
 */
const ChartUtils = {
    // Destruir todos los gráficos en una página
    destroyAll() {
        Chart.helpers.each(Chart.instances, function(instance) {
            instance.destroy();
        });
    },
    
    // Redimensionar todos los gráficos
    resizeAll() {
        Chart.helpers.each(Chart.instances, function(instance) {
            instance.resize();
        });
    },
    
    // Exportar gráfico como imagen
    exportChart(chartInstance, filename = 'chart.png') {
        const url = chartInstance.toBase64Image();
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        link.click();
    }
};

// Redimensionar gráficos cuando cambie el tamaño de ventana
window.addEventListener('resize', function() {
    setTimeout(() => {
        ChartUtils.resizeAll();
    }, 100);
});

// Exportar clases para uso global
window.GradeDistributionChart = GradeDistributionChart;
window.GradeEvolutionChart = GradeEvolutionChart;
window.AttendanceChart = AttendanceChart;
window.ChartUtils = ChartUtils;
window.CHART_COLORS = CHART_COLORS;