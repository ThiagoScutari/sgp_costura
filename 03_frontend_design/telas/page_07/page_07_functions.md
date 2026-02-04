### 🧩 Script de Inteligência para o BI (JavaScript)

Este script utiliza a biblioteca Chart.js para renderizar os dados de performance:

```javascript
// Dados simulados para o gráfico de eficiência
const efficiencyData = {
    labels: ['WS 1', 'WS 2', 'WS 3', 'WS 4'],
    datasets: [{
        label: '% de Eficiência',
        data: [92, 78, 85, 60], // WS 4 está com gargalo
        backgroundColor: [
            '#4CAF50', '#4CAF50', '#4CAF50', '#F44336'
        ]
    }]
};

function renderCharts() {
    const ctx = document.getElementById('efficiencyChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: efficiencyData,
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100 } },
            plugins: {
                title: { display: true, text: 'Eficiência por Workstation' }
            }
        }
    });
}

// Iniciar ao carregar
window.onload = renderCharts;

```
