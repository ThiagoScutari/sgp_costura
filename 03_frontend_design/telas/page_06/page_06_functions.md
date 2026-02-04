### 🧩 Script de Inteligência para Configurações (JavaScript)

Este script organiza os dados de turnos e usuários para o Stitch:

```javascript
// Dados de Exemplo para a Aba de Usuários
const users = [
    { nome: "Thiago Scutari", email: "thiago@consultoria.com", role: "Owner" },
    { nome: "Elizandra Facilitadora", email: "elizandra@fabrica.com", role: "User" }
];

// Dados de Exemplo para a Aba de Turnos
let intervals = [
    { nome: "Café Manhã", inicio: "07:30", fim: "07:45" },
    { nome: "Almoço", inicio: "12:00", fim: "13:00" }
];

function renderUsers() {
    const list = document.getElementById('user-list');
    list.innerHTML = users.map(u => `
        <tr class="border-b">
            <td class="p-3">${u.nome}</td>
            <td class="p-3">${u.email}</td>
            <td class="p-3">
                <span class="px-2 py-1 rounded text-xs font-bold ${
                    u.role === 'Owner' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                }">${u.role}</span>
            </td>
        </tr>
    `).join('');
}

function renderIntervals() {
    const list = document.getElementById('interval-list');
    list.innerHTML = intervals.map((int, index) => `
        <tr class="border-b">
            <td class="p-3">${int.nome}</td>
            <td class="p-3">${int.inicio}</td>
            <td class="p-3">${int.fim}</td>
            <td class="p-3"><button class="text-red-500" onclick="removeInterval(${index})">Excluir</button></td>
        </tr>
    `).join('');
}

// Lógica de Troca de Abas
function switchTab(tabName) {
    document.getElementById('tab-turnos').classList.toggle('hidden', tabName !== 'turnos');
    document.getElementById('tab-usuarios').classList.toggle('hidden', tabName !== 'usuarios');
}

window.onload = () => {
    renderUsers();
    renderIntervals();
};

```