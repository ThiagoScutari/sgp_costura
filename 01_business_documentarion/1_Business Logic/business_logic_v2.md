## 📄 Especificação de Regras de Cálculo - Sistema VAC v2

### 1. Motor de Tempo Padrão (PSO)

O sistema deve calcular o tempo de cada operação e o tempo total da peça (TP).

* **Fórmula por Operação:**
    * FinalTime = TimeEdited / EfficiencyFactor
* **Nota:** O `EfficiencyFactor` deve ser tratado como decimal (ex: 80% = 0.80).
* **Tempo Padrão Total (TP):**
    * É a soma de todos os `FinalTime` apenas das operações onde `status = 'Ativa'`.

### 2. Motor de Planejamento (Tamanho do Lote - TL)

Esta regra define a quantidade de peças por carrinho. Deve ser recalculada sempre que o número de operadores mudar.

* **A Fórmula:**
    * TL = floor ( (Operators * PulseDuration) / TP )
* **REGRA CRÍTICA:** O uso da função `floor` (arredondamento para baixo) é **obrigatório**. Se o resultado for 16.9, o lote deve ser de 16 peças. Isso garante que o trabalho caiba dentro do tempo determinado.
* **PulseDuration:** Valor configurado na tabela `PRODUCTION_PLANNING` (ex: 30 ou 60 minutos).

### 3. Motor de Balanceamento (Carga da Workstation)

Calcula se a distribuição de tarefas feita pela Facilitadora é viável.

* **Carga Individual (CI):**
    * CI = Σ (FinalTime da Operação * TL)
* **Validação Visual (Front-end):**
    * Se CI > PulseDuration: Status Crítico (Vermelho).
    * Se (PulseDuration - 5) <= CI <= PulseDuration: Status Ideal (Verde).
    * Se CI < (PulseDuration - 5): Status Ocioso (Amarelo).

### 4. Motor de Cronometragem e Atraso (Dashboard)

O sistema deve monitorar o pulso definido, ignorando intervalos improdutivos.

* **Cálculo de Janela Útil:**
    * O sistema deve consultar a tabela `TURN_CALENDAR`. Se o intervalo de almoço ocorrer entre o início do pulso e o agora, o sistema deve **pausar** o cronômetro ou subtrair o tempo do intervalo do cálculo.
* **Identificação de Atraso (is_delayed):**
    * Se (Tempo Atual - Hora do Último Check-out) > PulseDuration, o sistema marca o carrinho atual como atrasado.

### 5. Motor de Fracionamento (Alocação Parcial)

Quando uma operação é dividida entre duas costureiras:

* **Regra de Soma:** O sistema deve validar que a soma das `executed_quantity` em todas as `OPERATION_ALLOCATION` vinculadas a uma mesma operação seja exatamente igual ao TL do lote.

---

### Dica para o Desenvolvedor:

> "O sistema é orientado a eventos. O gatilho principal é o **Check-out do Carrinho**. Quando este evento ocorre, o cronômetro global do pulso (PulseDuration) deve resetar para toda a célula, e o próximo ID de carrinho na fila assume o status de 'Em Produção'."