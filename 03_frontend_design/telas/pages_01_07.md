
###  Paleta de Cores Funcional (Máquinas Macro)

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

"Aplique um sistema de **Color Coding** rigoroso: Cada card de operação deve exibir uma borda lateral de 4px identificando a máquina (Overloque=Roxo, Reta=Azul, Cobertura=Laranja, Catraca=Marrom). O rodapé das workstations deve conter um **Termômetro de Carga** que reage ao tempo total: Verde para carga completa, Amarelo para ociosa e Vermelho para sobrecarga. O sistema deve permitir alternar globalmente o limite deste termômetro entre **30 e 60 minutos**, recalculando as porcentagens de preenchimento instantaneamente."

---

### 🚀 Prompt para a Tela 01: Dashboard Operacional (Mobile First)

**Contexto:** Você é um desenvolvedor Front-end Sênior. Preciso do código HTML/CSS (Tailwind CSS) para a tela principal de um sistema de gestão têxtil (SGP Costura). Esta tela será acessada principalmente via **CELULAR**.
**Diretrizes de Layout (Mobile):**
1. **Header Fixo:** Deve conter o nome "SGP - Sistema VAC", o status da conexão (dot verde) e um seletor discreto de OP ativa.
2. **O Metrônomo (Coração da Tela):** No topo, um Card centralizado com um cronômetro gigante. O fundo do card deve mudar de cor: **Azul** (rodando), **Cinza** (intervalo/turno) e **Vermelho Piscando** (pulso vencido/atraso). Abaixo do tempo, exibir "Próximo Lote em: [HH:MM]".
3. **Indicadores de Progresso (Cards Grandes):**
* **Progresso da OP:** Uma barra de progresso horizontal larga. Texto: "Lote 08 de 24".
* **Eficiência Atual:** Um indicador circular (Gauge) mostrando a % de eficiência em tempo real.
4. **Lista de Carrinhos Ativos (Checklist Mobile):** Abaixo dos indicadores, uma lista vertical de carrinhos que estão na "pista". Cada item da lista deve ter um botão de "CHECK" grande no lado direito, fácil de clicar com o polegar.

**Paleta de Cores e Estilo:**
* Use um tema "Dark Mode" ou "High Contrast" para facilitar a leitura sob as luzes da fábrica.
* **Botão de Check:** Verde Vibrante (`#4CAF50`).
* **Alertas:** Vermelho Crítico (`#F44336`).
* Siga o rigor de **mínima carga cognitiva**: sem firulas, apenas dados e botões de ação.

**Comportamento Responsivo:** No computador, os cards de indicadores devem ficar lado a lado. No celular, devem ser empilhados verticalmente para ocupar toda a largura da tela.

---

### 🚀 Prompt para a Tela 02: Lista de OPs (Home)

**Contexto:** Você é um desenvolvedor Front-end. Preciso do código HTML/CSS (Tailwind CSS) para a tela de Listagem de Ordens de Produção (Home) do sistema SGP Costura.
**Diretrizes de Layout:**
1. **Cabeçalho:** Título "Ordens de Produção" e um botão de destaque "**+ NOVA OP**" (cor Azul ou Verde).
2. **Filtros Rápidos (Pílulas):** Uma linha de filtros clicáveis: "Todas", "Planejamento", "Em Produção", "Finalizadas".
3. **Grid de Cards (Responsivo):**
* No Celular: 1 card por linha.
* No Computador: Grid de 3 ou 4 colunas.
4. **Anatomia do Card de OP:**
* **Topo:** Número da OP (ex: #2024-001) e um Badge de Status colorido.
* **Corpo:** Nome da Referência (ex: POLO PREMIUM) em destaque.
* **Progresso:** Uma barra de progresso visual mostrando a porcentagem concluída.
* **Dados Rápidos:** Pequenos ícones com "Qtd Total" e "Data de Início".

**Lógica de Cores para Status (Badges):**
* **Planejamento:** Amarelo (Indica que o balanceamento está sendo feito).
* **Em Produção:** Azul (Indica que o pulso está ativo).
* **Finalizada:** Verde (Indica que o lote total foi batido).

**Interação:** O card inteiro deve ser clicável, levando o usuário para o Dashboard daquela OP específica.

---

### 🚀 Prompt para a Tela 03: Engenharia de PSO (Ciclo 1)

**Contexto:** Você é um desenvolvedor Front-end especializado em interfaces de ERP e produtividade. Preciso do HTML/CSS (Tailwind CSS) para a tela de Engenharia de PSO (Sequência Operacional) do sistema SGP Costura.
**Diretrizes de Layout (Desktop Focus):**
1. **Cabeçalho de Ações:**
* Botão de destaque: "**📥 IMPORTAR PDF**" (abre um seletor de arquivos).
* Resumo dinâmico: "Tempo Total (TP): 11.67 min" | "Total de Operações: 22".
* Botão de salvamento: "**💾 SALVAR VERSÃO V1**" (cor verde).

2. **Tabela de Edição de Operações (Rigorosa):**
* Uma tabela que ocupa a largura total com as seguintes colunas:
* **Seq:** (Input numérico pequeno).
* **Descrição:** (Input de texto largo).
* **Máquina Macro:** (Um Select/Dropdown que altera a cor de fundo da célula com base na seleção: Reta=Azul, Over=Roxo, Cobertura=Laranja, Catraca=Marrom).
* **Tempo (s):** (Input numérico para o tempo centesimal).
* **Status:** (Toggle/Switch para Inativar/Ativar operação).

3. **Funcionalidades de Edição:**
* As linhas devem permitir reordenação (Drag handle).
* Operações inativadas devem ficar com a linha opaca (estilo "disabled").

**Paleta de Cores de Máquinas (CSS Variables):**
* Aplique o Color Coding definido: `--reta: #2196F3`, `--over: #9C27B0`, `--cobertura: #FF9800`, `--catraca: #795548`.

**Comportamento Reativo:** Sempre que um tempo for alterado ou uma operação inativada, o "Tempo Total (TP)" no cabeçalho deve ser recalculado instantaneamente via JavaScript.

---

### 🚀 Prompt para a Tela 04: Cockpit de Balanceamento (Ciclo 2)

**Contexto:** Você é um Engenheiro de Front-end Sênior. Preciso do HTML/CSS/JS (Tailwind CSS) para a tela de Balanceamento (Cockpit) do sistema SGP Costura. Esta é a tela mais complexa do sistema e exige um layout que **NUNCA** quebre.
**Diretrizes de Layout (Desktop):**
1. **Estrutura de Tela Cheia:** Use `h-screen` e `overflow-hidden`. O cabeçalho é fixo e o conteúdo se divide em duas áreas:
* **Esquerda (300px):** Banco de Operações Disponíveis (Scroll vertical).
* **Direita (Flex-1):** Grid com exatamente 4 colunas (Workstations) de largura idêntica.

2. **O Card de Operação (Elemento Atômico):**
* Deve ter altura fixa para não desalinhar o Kanban.
* Borda lateral de 4px com a cor da máquina (Reta: Azul, Over: Roxo, Cobertura: Laranja, Catraca: Marrom).
* Exibir ID, Descrição Curta e Tempo Final.

3. **O Rodapé da Workstation (O Termômetro):**
* Cada uma das 4 colunas deve ter um rodapé fixo contendo uma barra de progresso (Termômetro).
* A barra deve preencher conforme o tempo das operações aumenta.
* **Lógica de Cor:** Verde (Ideal), Amarelo (Ocioso), Vermelho (Sobrecarga Pulse Duration).
* Botão "**✂️ FRACIONAR**" deve aparecer flutuando no card se a coluna estiver vermelha.

4. **Funcionalidade de Arraste:** Implemente a lógica de Drag and Drop para mover cards do banco para as colunas e entre colunas.

**Variáveis Dinâmicas:**
* O limite do termômetro deve respeitar o `pulseDuration` (30 ou 60 min).
* Calcule o tempo total de cada coluna em tempo real a cada movimento de card.

---

### 🚀 Prompt para a Tela 05: Checklist Digital (Ciclo 3)

**Contexto:** Você é um Desenvolvedor Front-end UI/UX especializado em interfaces industriais. Preciso do código HTML/CSS (Tailwind CSS) para a tela de Checklist Digital da Facilitadora.
**Diretrizes de Layout (Mobile/Tablet First):**
1. **Cabeçalho de Status:** Exibir a OP Ativa, a Referência (POLO PREMIUM) e o Tamanho do Lote (TL: 10 peças) de forma bem legível.
2. **O "Próximo na Fila" (Destaque):** O primeiro carrinho da lista (o atual) deve ser um Card Gigante com um botão de "**✅ FINALIZAR LOTE**" que ocupe pelo menos 40% da largura da tela.
3. **Lista de Espera:** Abaixo do destaque, listar os próximos 5 carrinhos em cards horizontais mais compactos, apenas para visualização da sequência.
4. **Feedback Tátil/Visual:** Ao clicar em finalizar, o card deve ter uma animação de "sucesso" (confete ou check verde) antes de sumir e dar lugar ao próximo.

**Rigor Técnico:**
* **Botões Anti-Erro:** O botão de finalizar deve ter um "delay" de 1 segundo de pressão ou um clique duplo para evitar finalizações acidentais enquanto a facilitadora caminha.
* **Modo de Alto Contraste:** Fundo branco com textos pretos e botões em verde vibrante (`#4CAF50`) para leitura sob luz forte de galpão.

**Variável de Negócio:** Exiba um cronômetro regressivo pequeno dentro de cada card de carrinho indicando há quanto tempo ele está na célula.

---

### 🚀 Prompt para a Tela 06: Configurações de Apoio (Turnos e Usuários)

**Contexto:** Você é um Desenvolvedor Front-end especializado em painéis administrativos. Preciso do HTML/CSS (Tailwind CSS) para a tela de Configurações do sistema SGP Costura.
**Diretrizes de Layout (Desktop Focus):**
1. **Navegação por Abas:** Crie duas abas principais: "**🕒 Calendário de Turnos**" e "**👥 Gestão de Usuários**".

2. **Conteúdo Aba 01 (Turnos):**
* **Seção de Jornada:** Inputs para "Início do Turno" e "Fim do Turno".
* **Tabela de Intervalos:** Colunas para "Nome do Intervalo" (ex: Almoço), "Início", "Fim" e um botão de excluir.
* **Botão de Ação:** "+ Adicionar Intervalo".

3. **Conteúdo Aba 02 (Usuários):**
* **Tabela de Usuários:** Colunas para Nome, E-mail e Nível de Acesso (Role).
* **Níveis de Acesso (Badges):** Owner (Vermelho), User (Verde), View (Cinza).
* **Ação:** Botão "Novo Usuário" que abre um modal simples.

4. **Estilo Visual:** Mantenha o rigor técnico. Use cores sóbrias, fontes legíveis e botões de salvamento em destaque no final da página.

**Comportamento Reativo:** Ao salvar o turno, o sistema deve validar se os intervalos estão dentro do horário da jornada.

---

### 🚀 Prompt para a Tela 07: Relatórios de Eficiência (BI)

**Contexto:** Você é um Desenvolvedor Front-end especializado em Data Visualization. Preciso do código HTML/CSS (Tailwind CSS) para a tela de Relatórios de Eficiência do sistema SGP Costura.
**Diretrizes de Layout (Desktop/Mobile):**
1. **Cards de Indicadores (KPIs):** No topo, 3 cards de destaque:
* **Eficiência Média da Célula:** Valor em % com cor dinâmica (Verde 80%).
* **Total de Peças Produzidas:** Soma total do dia/período.
* **Gargalo Identificado:** Nome da máquina/operação que mais reteve tempo.

2. **Gráficos (Charts):**
* **Gráfico de Barras:** Comparativo de "Meta vs. Realizado" por hora.
* **Gráfico de Radar ou Barras Horizontais:** Eficiência individual por costureira (Workstation).

3. **Tabela de Alertas de Gargalo:** Uma lista simples mostrando as operações que excederam o Pulso (30/60 min) e quantas vezes isso ocorreu.

**Estilo Visual:**
* Use a biblioteca **Chart.js** ou **ApexCharts** para os gráficos.
* Mantenha o Color Coding das máquinas: Overloque (Roxo), Reta (Azul), etc.

**Interação:** Filtro por "Data" e "Ordem de Produção (OP)" no topo da página.

