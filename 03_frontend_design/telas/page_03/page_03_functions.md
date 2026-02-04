### 🧩 Script de Inteligência para a Engenharia (JavaScript)

Este script lida com a lógica de cálculo do TP e a troca de cores dinâmica. Peça para o Stitch integrar:

```javascript
let psoData = [
    { id: 10, desc: "FECHAR OMBRO", machine: "over", time: 0.45, active: true },
    { id: 20, desc: "PESPONTAR GOLA", machine: "reta", time: 1.20, active: true }
];

function calculateTP() {
    const tp = psoData
        .filter(op => op.active)
        .reduce((sum, op) => sum + op.time, 0);
    document.getElementById('tp-display').innerText = tp.toFixed(2) + " min";
}

function updateMachineColor(selectElement, rowId) {
    const colors = {
        reta: 'bg-blue-100 border-blue-500',
        over: 'bg-purple-100 border-purple-500',
        cobertura: 'bg-orange-100 border-orange-500',
        catraca: 'bg-amber-900/10 border-amber-900'
    };
    const val = selectElement.value;
    const cell = selectElement.parentElement;
    cell.className = `p-2 border-l-4 ${colors[val] || 'bg-gray-50'}`;
}

// Renderizar a tabela dinamicamente para o Stitch
function renderPSOTable() {
    const tbody = document.getElementById('pso-body');
    tbody.innerHTML = psoData.map(op => `
        <tr class="${!op.active ? 'opacity-50' : ''}">
            <td class="p-2"><input type="number" value="${op.id}" class="w-12 border rounded"></td>
            <td class="p-2"><input type="text" value="${op.desc}" class="w-full border rounded"></td>
            <td class="p-2 border-l-4 border-blue-500 bg-blue-50">
                <select onchange="updateMachineColor(this, ${op.id})" class="bg-transparent w-full">
                    <option value="reta" ${op.machine === 'reta' ? 'selected' : ''}>Reta</option>
                    <option value="over" ${op.machine === 'over' ? 'selected' : ''}>Overloque</option>
                    <option value="cobertura" ${op.machine === 'cobertura' ? 'selected' : ''}>Cobertura</option>
                </select>
            </td>
            <td class="p-2"><input type="number" value="${op.time}" step="0.01" class="w-20 border rounded text-right"></td>
            <td class="p-2 text-center"><input type="checkbox" ${op.active ? 'checked' : ''}></td>
        </tr>
    `).join('');
    calculateTP();
}

```