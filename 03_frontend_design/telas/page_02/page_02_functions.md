### 🧩 Script de Inteligência para a Lista (JavaScript)

Para o Stitch integrar a lógica de dados, use este script que consome os dados da sua estrutura:

```javascript
const opListData = [
    { id: "2024-001", ref: "POLO PREMIUM CL.5982", status: "Em Produção", total: 240, current: 80, color: "blue" },
    { id: "2024-002", ref: "T-SHIRT BASIC", status: "Planejamento", total: 500, current: 0, color: "yellow" },
    { id: "2023-095", ref: "VESTIDO MIDI", status: "Finalizada", total: 150, current: 150, color: "green" }
];

function renderOPList() {
    const container = document.getElementById('op-list-container');
    container.innerHTML = opListData.map(op => {
        const percent = (op.current / op.total) * 100;
        return `
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200 hover:border-blue-500 cursor-pointer transition-all">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-xs font-bold text-gray-500">OP ${op.id}</span>
                    <span class="px-2 py-1 rounded-full text-xs font-semibold bg-${op.color}-100 text-${op.color}-700">
                        ${op.status}
                    </span>
                </div>
                <h3 class="font-bold text-gray-800 mb-3">${op.ref}</h3>
                <div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden mb-2">
                    <div class="bg-blue-500 h-full" style="width: ${percent}%"></div>
                </div>
                <div class="flex justify-between text-xs text-gray-500">
                    <span>${op.current} / ${op.total} Peças</span>
                    <span>${Math.round(percent)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

window.onload = renderOPList;

```
