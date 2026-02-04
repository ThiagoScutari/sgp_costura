
### 🚀 Prompt para a Tela 04: Cockpit de Balanceamento (Ciclo 2)

> **Contexto:** Você é um Engenheiro de Front-end Sênior. Preciso do HTML/CSS/JS (Tailwind CSS) para a tela de Balanceamento (Cockpit) do sistema SGP Costura. Esta é a tela mais complexa do sistema e exige um layout que **NUNCA** quebre.
> **Diretrizes de Layout (Desktop):**
> 1. **Estrutura de Tela Cheia:** Use `h-screen` e `overflow-hidden`. O cabeçalho é fixo e o conteúdo se divide em duas áreas:
> * **Esquerda (300px):** Banco de Operações Disponíveis (Scroll vertical).
> * **Direita (Flex-1):** Grid com exatamente 4 colunas (Workstations) de largura idêntica.
> 
> 
> 2. **O Card de Operação (Elemento Atômico):**
> * Deve ter altura fixa para não desalinhar o Kanban.
> * Borda lateral de 4px com a cor da máquina (Reta: Azul, Over: Roxo, Cobertura: Laranja, Catraca: Marrom).
> * Exibir ID, Descrição Curta e Tempo Final.
> 
> 
> 3. **O Rodapé da Workstation (O Termômetro):**
> * Cada uma das 4 colunas deve ter um rodapé fixo contendo uma barra de progresso (Termômetro).
> * A barra deve preencher conforme o tempo das operações aumenta.
> * **Lógica de Cor:** Verde (Ideal), Amarelo (Ocioso), Vermelho (Sobrecarga > Pulse Duration).
> * Botão "**✂️ FRACIONAR**" deve aparecer flutuando no card se a coluna estiver vermelha.
> 
> 
> 4. **Funcionalidade de Arraste:** Implemente a lógica de Drag and Drop para mover cards do banco para as colunas e entre colunas.
> 
> 
> **Variáveis Dinâmicas:**
> * O limite do termômetro deve respeitar o `pulseDuration` (30 ou 60 min).
> * Calcule o tempo total de cada coluna em tempo real a cada movimento de card.
> 
> 

---

