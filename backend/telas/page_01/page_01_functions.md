### 🧩 Script de Inteligência do Dashboard (v1)

```javascript
// Configurações Iniciais (Simulando vinda do Banco de Dados)
const config = {
    pulseDuration: 60, // em minutos (30 ou 60)
    totalBatches: 24,
    completedBatches: 8,
    lunchStart: "12:00",
    lunchEnd: "13:00"
};

let timeLeft = config.pulseDuration * 60; // converter para segundos
let timerInterval;

function startTimer() {
    timerInterval = setInterval(() => {
        const now = new Date();
        const currentTime = now.getHours() + ":" + now.getMinutes().toString().padStart(2, '0');

        // Lógica de Calendário de Turnos: Pausa no Almoço
        if (currentTime >= config.lunchStart && currentTime < config.lunchEnd) {
            updateUI("EM INTERVALO", "bg-gray-500");
            return; // Pausa a contagem
        }

        if (timeLeft > 0) {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Se o tempo estiver acabando (menos de 5 min), fica amarelo
            const color = timeLeft < 300 ? "bg-yellow-500" : "bg-blue-600";
            updateUI(display, color);
        } else {
            // Pulso Vencido: Alerta Vermelho
            updateUI("00:00", "bg-red-600 animate-pulse");
        }
    }, 1000);
}

function updateUI(text, bgColor) {
    const timerElement = document.getElementById('main-timer');
    const timerCard = document.getElementById('timer-card');
    if(timerElement) timerElement.innerText = text;
    if(timerCard) timerCard.className = `p-6 rounded-xl shadow-lg text-white transition-colors duration-500 ${bgColor}`;
}

// Função para o Botão "Check" da Facilitadora
function completeBatch() {
    config.completedBatches++;
    timeLeft = config.pulseDuration * 60; // Reseta o pulso
    alert("Lote concluído! Cronômetro resetado.");
    // Aqui no futuro dispararia o PATCH /api/cart/finish/{id}
}

// Iniciar ao carregar a tela
window.onload = startTimer;

```