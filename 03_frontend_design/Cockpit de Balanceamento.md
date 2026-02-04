### 🎴 Anatomia do Card de Operação

O card deve ser um componente compacto, porém rico em metadados. Ele precisa carregar o estado da operação e reagir visualmente às regras de negócio.

#### 1. Elementos Visuais (Front-end)

* **Borda de Identidade (Stroke):** Barra lateral de 4px com a cor da Máquina Macro (Roxo, Azul, etc.).
* **Identificador de Sequência:** Número da operação (ex: #10) em negrito no canto superior esquerdo.
* **Badge de Tipo:** Pequeno ícone ou etiqueta colorida se for **Preparatória** (P) ou **Dependente** (D).
* **Corpo de Texto:** Descrição da operação em caixa alta (ex: FECHAR OMBRO) para facilitar a leitura rápida.
* **Metadados de Tempo:** Tempo Final () exibido de forma proeminente no canto inferior direito.

#### 2. Comportamento e Estados (Lógica)

* **Estado: Dragging (Arrastando):** O card deve ficar levemente transparente (opacity: 0.7) e inclinado, para mostrar que está em movimento.
* **Estado: Invalid Drop (Proibido):** Se a Facilitadora tentar soltar o card em uma WS que viola a regra de precedência, o card deve "tremer" (shake animation) e retornar à posição de origem.
* **Estado: Fracionado:** Se o card for fruto de um fracionamento, ele deve exibir um ícone de "divisão" e a quantidade parcial que representa (ex: 8/16 peças).

---

### 🛠️ Estrutura de Dados do Objeto (JSON)

Para o programador, cada card é um objeto que deve conter estas propriedades para evitar consultas desnecessárias ao banco durante o arraste:

```json
{
  "op_id": 1025,
  "sequence": 10,
  "description": "UNIR LATERAIS",
  "machine_type": "overloque",
  "machine_color": "#9C27B0",
  "final_time": 0.85,
  "is_preparatory": false,
  "dependency_id": null,
  "is_fractioned": false,
  "original_quantity": 16,
  "current_quantity": 16
}

```

---

### 🎨 Protótipo de Layout (CSS Grid Interno)

Para manter o rigor visual, o card interno deve usar um micro-grid para que as informações não "pulem" de lugar se o texto for maior:

```css
.card-operacao {
  display: grid;
  grid-template-areas: 
    "seq type time"
    "desc desc desc";
  grid-template-columns: 1fr 1fr 1fr;
  padding: 8px;
  border-left: 4px solid var(--machine-color);
  min-height: 60px; /* Altura fixa para manter o rigor */
  user-select: none;
}

```

### 🚨 Regra de Ouro do "Arraste e Solte"

O sistema **não deve permitir** que o card seja solto em uma workstation se a `dependency_id` (operação anterior obrigatória) ainda estiver no "Banco de Operações" ou em uma workstation posterior na linha física. Isso blinda o processo contra erros de montagem.

