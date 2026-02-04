### 🧩 Script de Inteligência para o Balanceamento (JavaScript)

Este script garante que o layout seja reativo e os cálculos de tempo acompanhem cada movimento:

```javascript
// Dados iniciais baseados na sua planilha (Ex: CL.5982)
const state = {
    pulseDuration: 60,
    tl: 20,
    availableOps: [
        { id: 10, desc: "UNIR OMBRO", time: 0.45, machine: "over" },
        { id: 20, desc: "PESPONTAR GOLA", time: 1.20, machine: "reta" }
    ],
    workstations: [[], [], [], []] // As 4 colunas
};

function calculateColumnTime(colIndex) {
    const totalOpsTime = state.workstations[colIndex].reduce((sum, op) => sum + op.time, 0);
    // Tempo Total = Soma dos tempos das ops * Tamanho do Lote (TL)
    return totalOpsTime * state.tl;
}

function updateTermometers() {
    state.workstations.forEach((ws, index) => {
        const time = calculateColumnTime(index);
        const percent = (time / state.pulseDuration) * 100;
        
        const bar = document.getElementById(`bar-${index}`);
        const label = document.getElementById(`label-${index}`);
        
        bar.style.width = `${Math.min(percent, 100)}%`;
        label.innerText = `${time.toFixed(1)} / ${state.pulseDuration} min`;
        
        // Troca de cores do termômetro
        if (percent > 100) bar.className = "h-full bg-red-600";
        else if (percent > 80) bar.className = "h-full bg-green-500";
        else bar.className = "h-full bg-yellow-500";
    });
}

// Lógica de Drop (Simplificada para instrução do Stitch)
function onDrop(opId, targetColIndex) {
    // 1. Remove de onde estava
    // 2. Adiciona na nova workstation
    // 3. Chama updateTermometers()
}

```
