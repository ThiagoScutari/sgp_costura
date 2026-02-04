### 1. Definição de Tempo (O Pulso)

O sistema deve trabalhar com dois modos de visualização que o Owner alterna no cabeçalho. Isso muda o cálculo do  e a régua do termômetro:

* **Modo 30 min (Pulso Rápido):** Ideal para produtos de baixo . O termômetro de cada costureira tem o limite máximo de 30 minutos.
* **Modo 60 min (Pulso Longo):** Ideal para produtos complexos. O limite do termômetro expande para 60 minutos, permitindo lotes maiores.

---

### 2. Paleta de Cores Funcional (Máquinas Macro)

As cores serão aplicadas na **borda lateral esquerda** de cada Card de Operação e no **ícone da máquina**. Use estes códigos Hexadecimais exatos no CSS:

| Máquina Macro | Cor | Hex Code | Significado Visual |
| --- | --- | --- | --- |
| **Overloque** | Roxo | `#9C27B0` | Identificação imediata da máquina de fechamento. |
| **Reta** | Azul | `#2196F3` | Máquina de pesponto e etiquetas. |
| **Cobertura** | Laranja | `#FF9800` | Operações de bainha e acabamento. |
| **Catraca** | Marrom | `#795548` | Máquinas pesadas ou de transporte especial. |
| **Galoneira** | Verde Água | `#009688` | Operações de friso ou elástico. |
| **Outras** | Cinza | `#607D8B` | Operações manuais ou máquinas secundárias. |

---

### 3. Status de Carga (O Semáforo do Termômetro)

O termômetro no rodapé das colunas de balanceamento deve seguir esta lógica de cores baseada no tempo acumulado:

* **Verde (`#4CAF50`):** Carga ideal (entre 80% e 100% do pulso).
* **Amarelo (`#FFEB3B`):** Carga baixa (ociosidade detectada).
* **Vermelho (`#F44336`):** Sobrecarga (excedeu 30 ou 60 min). **Ação Necessária: Fracionar.**

### 🚀 Texto para Adicionar ao seu Prompt:

> "Aplique um sistema de **Color Coding** rigoroso: Cada card de operação deve exibir uma borda lateral de 4px identificando a máquina (Overloque=Roxo, Reta=Azul, Cobertura=Laranja, Catraca=Marrom). O rodapé das workstations deve conter um **Termômetro de Carga** que reage ao tempo total: Verde para carga completa, Amarelo para ociosa e Vermelho para sobrecarga. O sistema deve permitir alternar globalmente o limite deste termômetro entre **30 e 60 minutos**, recalculando as porcentagens de preenchimento instantaneamente."
